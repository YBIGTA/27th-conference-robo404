#!/usr/bin/env python3
"""
Movement Controller Node

Controls robot movement based on object detections.
Subscribes to detection events and target positions to navigate towards detected objects.
"""

import math
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Point, Twist
from nav_msgs.msg import Odometry


class MovementControllerNode(Node):
    def __init__(self):
        super().__init__('movement_controller_node')

        # Declare parameters
        self.declare_parameter('linear_speed', 0.2)
        self.declare_parameter('angular_speed', 0.5)
        self.declare_parameter('approach_distance', 1.0)  # meters
        self.declare_parameter('position_tolerance', 0.1)  # meters
        self.declare_parameter('angle_tolerance', 0.1)  # radians
        
        # Load parameters
        self.linear_speed = self.get_parameter('linear_speed').value
        self.angular_speed = self.get_parameter('angular_speed').value
        self.approach_distance = self.get_parameter('approach_distance').value
        self.position_tolerance = self.get_parameter('position_tolerance').value
        self.angle_tolerance = self.get_parameter('angle_tolerance').value
        
        # State variables
        self.current_command = None
        self.target_position = None
        self.robot_position = Point()
        self.robot_orientation = 0.0  # yaw in radians
        self.is_moving = False
        
        # Subscribers
        self.command_sub = self.create_subscription(
            String,
            '/movement_command',
            self.command_callback,
            10
        )
        
        self.target_sub = self.create_subscription(
            Point,
            '/target_position',
            self.target_callback,
            10
        )
        
        self.odom_sub = self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            10
        )
        
        # Publishers
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.status_pub = self.create_publisher(String, '/movement_status', 10)
        
        # Control timer
        self.control_timer = self.create_timer(0.1, self.control_loop)
        
        self.get_logger().info(
            f'Movement Controller Node initialized\n'
            f'  Linear speed: {self.linear_speed} m/s\n'
            f'  Angular speed: {self.angular_speed} rad/s\n'
            f'  Approach distance: {self.approach_distance} m'
        )

    def command_callback(self, msg: String):
        """Process movement commands from detection handler."""
        command = msg.data
        self.current_command = command
        
        self.get_logger().info(f'Received movement command: {command}')
        
        if command == 'stop':
            self.stop_movement()
        elif command in ['approach_chair', 'approach_red_ball']:
            self.is_moving = True
            self.get_logger().info(f'Starting movement for command: {command}')
        else:
            self.get_logger().warn(f'Unknown command: {command}')

    def target_callback(self, msg: Point):
        """Update target position from detection handler."""
        self.target_position = msg
        self.get_logger().info(f'Target position updated: ({msg.x:.2f}, {msg.y:.2f}, {msg.z:.2f})')

    def odom_callback(self, msg: Odometry):
        """Update robot position and orientation from odometry."""
        self.robot_position = msg.pose.pose.position
        
        # Extract yaw from quaternion
        orientation_q = msg.pose.pose.orientation
        siny_cosp = 2 * (orientation_q.w * orientation_q.z + orientation_q.x * orientation_q.y)
        cosy_cosp = 1 - 2 * (orientation_q.y * orientation_q.y + orientation_q.z * orientation_q.z)
        self.robot_orientation = math.atan2(siny_cosp, cosy_cosp)

    def control_loop(self):
        """Main control loop for robot movement."""
        if not self.is_moving or self.current_command is None or self.target_position is None:
            return
        
        # Calculate movement based on current command
        twist_msg = Twist()
        
        if self.current_command in ['approach_chair', 'approach_red_ball']:
            twist_msg = self.approach_target()
        
        # Publish movement command
        self.cmd_vel_pub.publish(twist_msg)
        
        # Publish status
        status_msg = String()
        status_msg.data = f'executing:{self.current_command}'
        self.status_pub.publish(status_msg)

    def approach_target(self):
        """Calculate movement to approach a static target."""
        twist = Twist()
        
        if self.target_position is None:
            return twist
        
        # For now, use simple image-based control
        # In a real system, you'd convert image coordinates to world coordinates
        
        # Target is in normalized image coordinates (-1 to 1)
        target_x = self.target_position.x
        target_y = self.target_position.y
        
        # Simple proportional control
        # If target is to the left/right, turn
        if abs(target_x) > 0.1:  # Dead zone
            twist.angular.z = -target_x * self.angular_speed
        
        # If target is centered horizontally, move forward
        if abs(target_x) < 0.2:
            # Move forward if target is not too close (target_y > -0.5 means not too close)
            if target_y > -0.3:  # Adjust this threshold as needed
                twist.linear.x = self.linear_speed * 0.5
            else:
                # Target is close enough, stop
                self.get_logger().info('Target reached!')
                self.stop_movement()
                return twist
        
        return twist

    def follow_target(self):
        """Calculate movement to follow a moving target (like a person)."""
        twist = Twist()
        
        if self.target_position is None:
            return twist
        
        # Similar to approach_target but with different behavior
        target_x = self.target_position.x
        target_y = self.target_position.y
        
        # Always try to keep the target centered and at a certain distance
        if abs(target_x) > 0.1:
            twist.angular.z = -target_x * self.angular_speed
        
        # Maintain distance - move forward if target is far, backward if too close
        if target_y > 0.1:  # Target is far
            twist.linear.x = self.linear_speed * 0.3
        elif target_y < -0.3:  # Target is too close
            twist.linear.x = -self.linear_speed * 0.2
        
        return twist

    def stop_movement(self):
        """Stop all robot movement."""
        self.is_moving = False
        self.current_command = None
        
        # Publish zero velocity
        twist = Twist()
        self.cmd_vel_pub.publish(twist)
        
        # Publish status
        status_msg = String()
        status_msg.data = 'stopped'
        self.status_pub.publish(status_msg)
        
        self.get_logger().info('Robot movement stopped')

    def calculate_distance_to_target(self):
        """Calculate distance to target in world coordinates."""
        if self.target_position is None:
            return float('inf')
        
        dx = self.target_position.x - self.robot_position.x
        dy = self.target_position.y - self.robot_position.y
        return math.sqrt(dx*dx + dy*dy)

    def calculate_angle_to_target(self):
        """Calculate angle to target relative to robot orientation."""
        if self.target_position is None:
            return 0.0
        
        dx = self.target_position.x - self.robot_position.x
        dy = self.target_position.y - self.robot_position.y
        target_angle = math.atan2(dy, dx)
        
        # Normalize angle difference
        angle_diff = target_angle - self.robot_orientation
        while angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        while angle_diff < -math.pi:
            angle_diff += 2 * math.pi
        
        return angle_diff

    def get_status(self):
        """Get current movement status."""
        return {
            'is_moving': self.is_moving,
            'current_command': self.current_command,
            'target_position': self.target_position,
            'robot_position': self.robot_position,
            'robot_orientation': self.robot_orientation
        }


def main(args=None):
    rclpy.init(args=args)
    node = MovementControllerNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()