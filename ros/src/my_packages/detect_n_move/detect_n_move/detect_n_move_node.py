#!/usr/bin/env python3
"""
Detect and Move Node

Main node that combines detection and movement functionality.
This node integrates object detection with robot movement control.
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy
from std_msgs.msg import String
from geometry_msgs.msg import Point, Twist
from yolo_msgs.msg import DetectionArray
import math


class DetectAndMoveNode(Node):
    def __init__(self):
        super().__init__('detect_and_move_node')

        # Declare parameters
        self.declare_parameter('confidence_threshold', 0.7)
        self.declare_parameter('target_objects', ['chair', 'red_ball'])
        self.declare_parameter('linear_speed', 0.2)
        self.declare_parameter('angular_speed', 0.5)
        self.declare_parameter('detection_timeout', 3.0)
        
        # Load parameters
        self.confidence_threshold = self.get_parameter('confidence_threshold').value
        self.target_objects = self.get_parameter('target_objects').value
        self.linear_speed = self.get_parameter('linear_speed').value
        self.angular_speed = self.get_parameter('angular_speed').value
        self.detection_timeout = self.get_parameter('detection_timeout').value
        
        # State variables
        self.current_target = None
        self.last_detection_time = None
        self.is_moving = False
        self.target_position = None
        
        # QoS for YOLO detections
        qos = QoSProfile(depth=10, reliability=QoSReliabilityPolicy.BEST_EFFORT)

        # Subscribers
        self.detection_sub = self.create_subscription(
            DetectionArray,
            '/yolo/detections',
            self.detection_callback,
            qos
        )

        # Publishers
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.status_pub = self.create_publisher(String, '/detect_move_status', 10)
        self.event_pub = self.create_publisher(String, '/detection_events', 10)

        # Control timer
        self.control_timer = self.create_timer(0.1, self.control_loop)
        self.timeout_timer = self.create_timer(1.0, self.check_timeout)

        self.get_logger().info(
            f'Detect and Move Node initialized\n'
            f'  Target objects: {self.target_objects}\n'
            f'  Confidence threshold: {self.confidence_threshold}\n'
            f'  Movement speeds: linear={self.linear_speed}, angular={self.angular_speed}'
        )

    def detection_callback(self, msg: DetectionArray):
        """Process YOLO detections and update target."""
        if not msg.detections:
            return

        # Filter relevant detections
        relevant_detections = []
        for detection in msg.detections:
            if (detection.score >= self.confidence_threshold and 
                detection.class_name in self.target_objects):
                relevant_detections.append(detection)

        if not relevant_detections:
            return

        # Get highest confidence detection
        best_detection = max(relevant_detections, key=lambda d: d.score)
        
        # Update target
        self.current_target = best_detection.class_name
        self.last_detection_time = self.get_clock().now()
        
        # Calculate normalized target position from bounding box
        bbox_center_x = best_detection.bbox.center.position.x
        bbox_center_y = best_detection.bbox.center.position.y
        
        # Normalize to [-1, 1] range (assuming 1920x1080 image)
        norm_x = (bbox_center_x - 960.0) / 960.0
        norm_y = (bbox_center_y - 540.0) / 540.0
        
        self.target_position = Point()
        self.target_position.x = norm_x
        self.target_position.y = norm_y
        self.target_position.z = 0.0
        
        # Start movement if not already moving
        if not self.is_moving:
            self.is_moving = True
            self.get_logger().info(f'Started tracking {self.current_target}')
        
        # Publish detection event
        event_msg = String()
        event_msg.data = f'tracking:{self.current_target}:{best_detection.score:.2f}'
        self.event_pub.publish(event_msg)

    def control_loop(self):
        """Main control loop for robot movement."""
        twist = Twist()
        
        if not self.is_moving or self.target_position is None:
            self.cmd_vel_pub.publish(twist)  # Send zero velocity
            return
        
        # Get target position in image coordinates
        target_x = self.target_position.x  # [-1, 1] horizontal
        target_y = self.target_position.y  # [-1, 1] vertical
        
        # Angular control - turn towards target
        angular_error = target_x  # Positive means target is to the right
        
        if abs(angular_error) > 0.1:  # Dead zone
            twist.angular.z = -angular_error * self.angular_speed
        
        # Linear control - move forward when target is centered
        if abs(angular_error) < 0.2:  # Target is roughly centered
            # Use vertical position to control forward movement
            # Positive y means target is in lower part of image (closer)
            if target_y < 0.0:  # Target is in upper part (farther)
                twist.linear.x = self.linear_speed * 0.5
            elif target_y > 0.5:  # Target is very close
                twist.linear.x = 0.0  # Stop
                self.get_logger().info(f'Reached {self.current_target}!')
            else:
                twist.linear.x = self.linear_speed * 0.3  # Slow approach
        
        # Publish movement command
        self.cmd_vel_pub.publish(twist)
        
        # Publish status
        status_msg = String()
        if self.current_target:
            status_msg.data = f'moving_to:{self.current_target}:pos=({target_x:.2f},{target_y:.2f})'
        else:
            status_msg.data = 'idle'
        self.status_pub.publish(status_msg)

    def check_timeout(self):
        """Check if target detection has timed out."""
        if not self.is_moving or self.last_detection_time is None:
            return
        
        elapsed = (self.get_clock().now() - self.last_detection_time).nanoseconds / 1e9
        
        if elapsed > self.detection_timeout:
            self.get_logger().info(f'Lost target {self.current_target} after {elapsed:.1f}s')
            self.stop_movement()

    def stop_movement(self):
        """Stop robot movement and reset target."""
        self.is_moving = False
        self.current_target = None
        self.target_position = None
        self.last_detection_time = None
        
        # Send zero velocity
        twist = Twist()
        self.cmd_vel_pub.publish(twist)
        
        # Publish status
        status_msg = String()
        status_msg.data = 'stopped'
        self.status_pub.publish(status_msg)
        
        self.get_logger().info('Movement stopped')

    def get_target_info(self):
        """Get information about current target."""
        return {
            'target': self.current_target,
            'position': self.target_position,
            'is_moving': self.is_moving,
            'last_seen': self.last_detection_time
        }


def main(args=None):
    rclpy.init(args=args)
    node = DetectAndMoveNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()