#!/usr/bin/env python3
"""
Gazebo Auto Labeler for YOLO Training

This node automatically generates YOLO format labels from Gazebo simulation.
It captures camera images and calculates bounding boxes from known model positions.

Usage:
    ros2 run training auto_labeler.py
    # or
    python3 auto_labeler.py --config label_config.yaml --output data
"""

import os
import sys
import yaml
import argparse
import numpy as np
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

from sensor_msgs.msg import Image, CameraInfo
from geometry_msgs.msg import Pose, TransformStamped
from tf2_msgs.msg import TFMessage
from tf2_ros import Buffer, TransformListener
from cv_bridge import CvBridge


@dataclass
class TargetObject:
    """Target object for labeling"""
    name: str
    class_id: int
    class_name: str
    geometry_type: str  # sphere, box, cylinder
    size: List[float]   # [radius] for sphere, [x,y,z] for box, [radius, height] for cylinder


@dataclass
class BoundingBox:
    """2D Bounding box in pixel coordinates"""
    x_center: float
    y_center: float
    width: float
    height: float
    class_id: int

    def to_yolo(self, img_width: int, img_height: int) -> str:
        """Convert to YOLO format (normalized)"""
        x_norm = self.x_center / img_width
        y_norm = self.y_center / img_height
        w_norm = self.width / img_width
        h_norm = self.height / img_height

        # Clamp values to [0, 1]
        x_norm = max(0, min(1, x_norm))
        y_norm = max(0, min(1, y_norm))
        w_norm = max(0, min(1, w_norm))
        h_norm = max(0, min(1, h_norm))

        return f"{self.class_id} {x_norm:.6f} {y_norm:.6f} {w_norm:.6f} {h_norm:.6f}"


class AutoLabeler(Node):
    def __init__(self, config_path: str, output_dir: str, world_name: str = "default"):
        super().__init__('auto_labeler')

        self.cv_bridge = CvBridge()
        self.output_dir = Path(output_dir)
        self.world_name = world_name

        # Create output directories
        (self.output_dir / "images" / "train").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "labels" / "train").mkdir(parents=True, exist_ok=True)

        # Load config
        self.targets = self._load_config(config_path)
        self.get_logger().info(f"Loaded {len(self.targets)} target objects: {list(self.targets.keys())}")

        # Camera parameters (will be updated from CameraInfo)
        self.camera_matrix = None
        self.img_width = 1920
        self.img_height = 1080

        # Model positions from Gazebo (world frame)
        self.model_poses: Dict[str, Pose] = {}

        # Robot pose (for coordinate transformation)
        self.robot_pose: Optional[Pose] = None

        # TF for camera pose
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        # QoS for sensor topics
        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )

        # QoS for pose topic (reliable)
        pose_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )

        # Subscribers
        self.image_sub = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.image_callback,
            sensor_qos
        )

        self.camera_info_sub = self.create_subscription(
            CameraInfo,
            '/camera/camera_info',
            self.camera_info_callback,
            sensor_qos
        )

        # Subscribe to Gazebo model poses via ROS2 bridge
        self.pose_sub = self.create_subscription(
            TFMessage,
            f'/world/{self.world_name}/pose/info',
            self.pose_callback,
            pose_qos
        )
        self.get_logger().info(f"Subscribed to pose topic: /world/{self.world_name}/pose/info")

        # Capture control
        self.capture_enabled = False
        self.capture_count = 0
        self.capture_interval = 1.0  # seconds
        self.last_capture_time = self.get_clock().now()

        # Timer for status updates
        self.create_timer(5.0, self.status_callback)

        self.get_logger().info("Auto Labeler initialized")
        self.get_logger().info(f"Output directory: {self.output_dir}")

    def _load_config(self, config_path: str) -> Dict[str, TargetObject]:
        """Load target objects from config file"""
        targets = {}

        config_file = Path(config_path)
        if not config_file.exists():
            self.get_logger().warn(f"Config file not found: {config_path}, using defaults")
            # Default: red_ball
            targets["red_ball_10in"] = TargetObject(
                name="red_ball_10in",
                class_id=0,
                class_name="red_ball",
                geometry_type="sphere",
                size=[0.127]  # radius in meters
            )
            return targets

        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)

        for obj in config.get('targets', []):
            targets[obj['model_name']] = TargetObject(
                name=obj['model_name'],
                class_id=obj['class_id'],
                class_name=obj['class_name'],
                geometry_type=obj['geometry_type'],
                size=obj['size']
            )

        return targets

    def pose_callback(self, msg: TFMessage):
        """Callback for Gazebo model poses via ROS2 bridge"""
        for transform in msg.transforms:
            # child_frame_id contains the model name
            model_name = transform.child_frame_id

            # Store robot pose for coordinate transformation
            if model_name == "waffle" or model_name == "turtlebot3_waffle" or "waffle" in model_name.lower():
                self.robot_pose = Pose()
                self.robot_pose.position.x = transform.transform.translation.x
                self.robot_pose.position.y = transform.transform.translation.y
                self.robot_pose.position.z = transform.transform.translation.z
                self.robot_pose.orientation = transform.transform.rotation

            # Check if this is a target object
            if model_name in self.targets:
                pose = Pose()
                pose.position.x = transform.transform.translation.x
                pose.position.y = transform.transform.translation.y
                pose.position.z = transform.transform.translation.z
                pose.orientation = transform.transform.rotation
                self.model_poses[model_name] = pose

    def camera_info_callback(self, msg: CameraInfo):
        """Update camera intrinsic parameters"""
        self.img_width = msg.width
        self.img_height = msg.height

        # Camera matrix K: [fx, 0, cx, 0, fy, cy, 0, 0, 1]
        self.camera_matrix = np.array(msg.k).reshape(3, 3)

    def image_callback(self, msg: Image):
        """Process camera image and generate labels"""
        if self.camera_matrix is None:
            return

        if self.robot_pose is None:
            return

        current_time = self.get_clock().now()

        # Check capture conditions
        if not self.capture_enabled:
            return

        time_diff = (current_time - self.last_capture_time).nanoseconds / 1e9
        if time_diff < self.capture_interval:
            return

        # Convert image
        try:
            cv_image = self.cv_bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().error(f"Failed to convert image: {e}")
            return

        # Calculate bounding boxes
        bboxes = self._calculate_bounding_boxes()

        if not bboxes:
            self.get_logger().debug("No objects in view")
            return

        # Save image and labels
        self._save_data(cv_image, bboxes, msg.header.stamp)

        self.last_capture_time = current_time
        self.capture_count += 1
        self.get_logger().info(f"Captured frame {self.capture_count}, {len(bboxes)} objects labeled")

    def _calculate_bounding_boxes(self) -> List[BoundingBox]:
        """Calculate 2D bounding boxes from 3D model positions"""
        bboxes = []

        if self.robot_pose is None:
            return bboxes

        for model_name, target in self.targets.items():
            if model_name not in self.model_poses:
                continue

            model_pose = self.model_poses[model_name]

            # Transform object position to robot-relative coordinates
            # Object position in world frame
            obj_world = np.array([
                model_pose.position.x,
                model_pose.position.y,
                model_pose.position.z
            ])

            # Robot position in world frame
            robot_world = np.array([
                self.robot_pose.position.x,
                self.robot_pose.position.y,
                self.robot_pose.position.z
            ])

            # Get robot yaw from quaternion
            q = self.robot_pose.orientation
            # Simplified yaw extraction (assumes mostly 2D rotation)
            siny_cosp = 2 * (q.w * q.z + q.x * q.y)
            cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
            robot_yaw = np.arctan2(siny_cosp, cosy_cosp)

            # Transform to robot frame
            obj_rel = obj_world - robot_world

            # Rotate to robot frame (2D rotation around Z axis)
            cos_yaw = np.cos(-robot_yaw)
            sin_yaw = np.sin(-robot_yaw)

            obj_robot = np.array([
                cos_yaw * obj_rel[0] - sin_yaw * obj_rel[1],
                sin_yaw * obj_rel[0] + cos_yaw * obj_rel[1],
                obj_rel[2]
            ])

            # Project to 2D
            bbox = self._project_object(obj_robot, target)

            if bbox is not None:
                bboxes.append(bbox)

        return bboxes

    def _project_object(self, pos_robot: np.ndarray, target: TargetObject) -> Optional[BoundingBox]:
        """Project 3D object to 2D bounding box"""
        if self.camera_matrix is None:
            return None

        # Camera frame convention for TurtleBot3:
        # Robot frame: X forward, Y left, Z up
        # Camera frame: Z forward, X right, Y down

        # Transform robot frame to camera frame
        # Camera is mounted on the robot facing forward
        x_cam = -pos_robot[1]  # Robot Y (left) -> Camera X (right, negated)
        y_cam = -pos_robot[2] + 0.1  # Robot Z -> Camera Y (down, with camera height offset)
        z_cam = pos_robot[0]   # Robot X (forward) -> Camera Z (depth)

        # Check if object is in front of camera
        if z_cam <= 0.2:  # minimum depth
            return None

        # Get camera intrinsics
        fx = self.camera_matrix[0, 0]
        fy = self.camera_matrix[1, 1]
        cx = self.camera_matrix[0, 2]
        cy = self.camera_matrix[1, 2]

        # Project center point
        u = fx * x_cam / z_cam + cx
        v = fy * y_cam / z_cam + cy

        # Calculate bounding box size based on object geometry
        if target.geometry_type == "sphere":
            radius = target.size[0]
            # Project sphere radius to pixel size
            pixel_radius_x = fx * radius / z_cam
            pixel_radius_y = fy * radius / z_cam
            width = pixel_radius_x * 2
            height = pixel_radius_y * 2

        elif target.geometry_type == "box":
            # Use maximum dimension for conservative bbox
            max_dim = max(target.size[:2])  # X, Y dimensions
            height_dim = target.size[2] if len(target.size) > 2 else max_dim
            width = fx * max_dim / z_cam
            height = fy * height_dim / z_cam

        elif target.geometry_type == "cylinder":
            radius = target.size[0]
            cyl_height = target.size[1] if len(target.size) > 1 else radius * 2
            width = fx * radius * 2 / z_cam
            height = fy * cyl_height / z_cam

        else:
            return None

        # Check if bbox is within image bounds (at least partially visible)
        if (u + width/2 < 0 or u - width/2 > self.img_width or
            v + height/2 < 0 or v - height/2 > self.img_height):
            return None

        return BoundingBox(
            x_center=u,
            y_center=v,
            width=width,
            height=height,
            class_id=target.class_id
        )

    def _save_data(self, image: np.ndarray, bboxes: List[BoundingBox], stamp):
        """Save image and YOLO format labels"""
        import cv2

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"frame_{timestamp}"

        # Save image
        img_path = self.output_dir / "images" / "train" / f"{filename}.jpg"
        cv2.imwrite(str(img_path), image)

        # Save labels
        label_path = self.output_dir / "labels" / "train" / f"{filename}.txt"
        with open(label_path, 'w') as f:
            for bbox in bboxes:
                yolo_line = bbox.to_yolo(self.img_width, self.img_height)
                f.write(yolo_line + '\n')

    def status_callback(self):
        """Print status update"""
        robot_status = "tracked" if self.robot_pose is not None else "not found"
        self.get_logger().info(
            f"Status: capture={'ON' if self.capture_enabled else 'OFF'}, "
            f"frames={self.capture_count}, "
            f"models_tracked={len(self.model_poses)}/{len(self.targets)}, "
            f"robot={robot_status}"
        )

    def start_capture(self):
        """Start continuous capture"""
        self.capture_enabled = True
        self.get_logger().info("Capture started")

    def stop_capture(self):
        """Stop continuous capture"""
        self.capture_enabled = False
        self.get_logger().info("Capture stopped")

    def single_capture(self):
        """Capture single frame"""
        self.capture_enabled = True
        self.last_capture_time = self.get_clock().now() - rclpy.duration.Duration(seconds=self.capture_interval + 1)


def main():
    parser = argparse.ArgumentParser(description="Gazebo Auto Labeler for YOLO")
    parser.add_argument('--config', type=str, default='label_config.yaml',
                        help='Path to label config file')
    parser.add_argument('--output', type=str, default='data',
                        help='Output directory for images and labels')
    parser.add_argument('--world', type=str, default='default',
                        help='Gazebo world name')
    parser.add_argument('--interval', type=float, default=1.0,
                        help='Capture interval in seconds')

    args = parser.parse_args()

    rclpy.init()

    # Resolve paths relative to script directory
    script_dir = Path(__file__).parent.resolve()
    config_path = script_dir / args.config
    output_dir = script_dir / args.output

    node = AutoLabeler(
        config_path=str(config_path),
        output_dir=str(output_dir),
        world_name=args.world
    )

    node.capture_interval = args.interval

    # Start capture automatically
    node.start_capture()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.get_logger().info(f"Total frames captured: {node.capture_count}")
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
