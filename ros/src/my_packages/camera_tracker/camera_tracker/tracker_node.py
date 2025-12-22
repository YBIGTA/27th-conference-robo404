#!/usr/bin/env python3
"""
Camera Tracker Node

Tracks the highest-confidence object detected by YOLO and controls
camera pan/tilt joints to keep the object centered in the frame.
Returns to home position after timeout when no object is detected.
"""

import math
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy
from std_msgs.msg import Float64, Bool
from yolo_msgs.msg import DetectionArray


class CameraTrackerNode(Node):
    def __init__(self):
        super().__init__('camera_tracker_node')

        # Declare parameters
        self.declare_parameter('image_width', 1920)
        self.declare_parameter('image_height', 1080)
        self.declare_parameter('fov_horizontal', 1.02974)  # rad (~59 degrees)
        self.declare_parameter('timeout_seconds', 3.0)
        self.declare_parameter('kp_pan', 0.3)
        self.declare_parameter('kp_tilt', 0.2)
        self.declare_parameter('pan_limit', 1.57)   # rad (~90 degrees)
        self.declare_parameter('tilt_limit', 0.17)  # rad (~10 degrees)
        self.declare_parameter('dead_zone', 80.0)   # pixels
        self.declare_parameter('target_y_offset', 0.0)  # pixels (positive = target lower = camera looks up)
        # Smoothing parameters
        self.declare_parameter('smoothing_alpha', 0.2)  # EMA alpha (lower = smoother)
        self.declare_parameter('max_angular_rate', 0.05)  # rad/cycle (max speed)

        # Load parameters
        self.image_width = self.get_parameter('image_width').value
        self.image_height = self.get_parameter('image_height').value
        self.fov_h = self.get_parameter('fov_horizontal').value
        self.timeout = self.get_parameter('timeout_seconds').value
        self.kp_pan = self.get_parameter('kp_pan').value
        self.kp_tilt = self.get_parameter('kp_tilt').value
        self.pan_limit = self.get_parameter('pan_limit').value
        self.tilt_limit = self.get_parameter('tilt_limit').value
        self.dead_zone = self.get_parameter('dead_zone').value
        self.target_y_offset = self.get_parameter('target_y_offset').value

        # Calculate vertical FOV based on aspect ratio
        aspect_ratio = self.image_width / self.image_height
        self.fov_v = 2 * math.atan(math.tan(self.fov_h / 2) / aspect_ratio)

        # State variables
        self.current_pan = 0.0
        self.current_tilt = 0.0
        self.last_detection_time = None
        self.tracking_active = False

        # QoS for YOLO detections
        qos = QoSProfile(depth=10, reliability=QoSReliabilityPolicy.BEST_EFFORT)

        # Subscriber: YOLO detections
        self.detection_sub = self.create_subscription(
            DetectionArray,
            '/yolo/detections',
            self.detection_callback,
            qos
        )

        # Publishers: Camera joint commands
        self.pan_pub = self.create_publisher(Float64, '/camera/pan_cmd', 10)
        self.tilt_pub = self.create_publisher(Float64, '/camera/tilt_cmd', 10)

        # Publisher: Camera stability status
        self.stable_pub = self.create_publisher(Bool, '/camera/stable', 10)
        self.is_stable = False

        # Timer for timeout check and return to home
        self.timer = self.create_timer(0.1, self.timer_callback)

        self.get_logger().info(
            f'Camera Tracker Node initialized\n'
            f'  Image: {self.image_width}x{self.image_height}\n'
            f'  FOV: H={math.degrees(self.fov_h):.1f}deg, V={math.degrees(self.fov_v):.1f}deg\n'
            f'  Timeout: {self.timeout}s\n'
            f'  Gains: Kp_pan={self.kp_pan}, Kp_tilt={self.kp_tilt}'
        )

    def detection_callback(self, msg: DetectionArray):
        """Process YOLO detections and track the highest-confidence object."""
        if not msg.detections:
            return

        # Select the object with highest confidence score
        best_detection = max(msg.detections, key=lambda d: d.score)

        # Get object center coordinates (pixels)
        cx = best_detection.bbox.center.position.x
        cy = best_detection.bbox.center.position.y

        # Calculate offset from target position (pixels)
        # target_y_offset > 0 moves target down, so camera looks up
        offset_x = cx - (self.image_width / 2)
        target_y = (self.image_height / 2) + self.target_y_offset
        offset_y = cy - target_y

        # Check dead zone - if object is near center, camera is stable
        if abs(offset_x) < self.dead_zone and abs(offset_y) < self.dead_zone:
            self.last_detection_time = self.get_clock().now()
            self.tracking_active = True
            # Publish stable status (only on state change)
            if not self.is_stable:
                self.is_stable = True
                stable_msg = Bool()
                stable_msg.data = True
                self.stable_pub.publish(stable_msg)
            return

        # Camera is moving, publish unstable
        if self.is_stable:
            self.is_stable = False
            stable_msg = Bool()
            stable_msg.data = False
            self.stable_pub.publish(stable_msg)

        # Convert pixel offset to angular offset
        rad_per_pixel_h = self.fov_h / self.image_width
        rad_per_pixel_v = self.fov_v / self.image_height

        # Calculate target angle offset
        # Negative because camera coordinate system is inverted
        delta_pan = -offset_x * rad_per_pixel_h
        delta_tilt = -offset_y * rad_per_pixel_v

        # Proportional control for joint commands
        pan_cmd = self.current_pan + self.kp_pan * delta_pan
        tilt_cmd = self.current_tilt + self.kp_tilt * delta_tilt

        # Apply limits
        pan_cmd = max(-self.pan_limit, min(self.pan_limit, pan_cmd))
        tilt_cmd = max(-self.tilt_limit, min(self.tilt_limit, tilt_cmd))

        # Publish commands
        self.publish_commands(pan_cmd, tilt_cmd)

        # Update state
        self.current_pan = pan_cmd
        self.current_tilt = tilt_cmd
        self.last_detection_time = self.get_clock().now()
        self.tracking_active = True

        self.get_logger().debug(
            f'Tracking: {best_detection.class_name} '
            f'(score={best_detection.score:.2f}) -> '
            f'pan={math.degrees(pan_cmd):.1f}deg, '
            f'tilt={math.degrees(tilt_cmd):.1f}deg'
        )

    def timer_callback(self):
        """Check timeout and return to home position if needed."""
        if not self.tracking_active:
            return

        if self.last_detection_time is None:
            return

        elapsed = (self.get_clock().now() - self.last_detection_time).nanoseconds / 1e9

        if elapsed > self.timeout:
            self.get_logger().info(
                f'Object lost for {elapsed:.1f}s, returning to home position'
            )
            self.return_to_home()

    def return_to_home(self):
        """Return camera to home (forward-facing) position."""
        self.publish_commands(0.0, 0.0)
        self.current_pan = 0.0
        self.current_tilt = 0.0
        self.tracking_active = False
        # Publish unstable when returning home
        if self.is_stable:
            self.is_stable = False
            stable_msg = Bool()
            stable_msg.data = False
            self.stable_pub.publish(stable_msg)

    def publish_commands(self, pan: float, tilt: float):
        """Publish joint position commands."""
        pan_msg = Float64()
        pan_msg.data = pan
        self.pan_pub.publish(pan_msg)

        tilt_msg = Float64()
        tilt_msg.data = tilt
        self.tilt_pub.publish(tilt_msg)


def main(args=None):
    rclpy.init(args=args)
    node = CameraTrackerNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
