#!/usr/bin/env python3
"""
Movement Controller Node (Simple Relay) - ROBUST VERSION
Logic: Receives /target_pose -> Sanitize -> Sends to Nav2 /goal_pose
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from rclpy.qos import QoSProfile, QoSReliabilityPolicy

class MovementControllerNode(Node):
    def __init__(self):
        super().__init__('movement_controller_node')
        
        # 1. QoS Profile (Must match Nav2's Best Effort)
        qos_profile = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            depth=10
        )

        self.create_subscription(PoseStamped, '/target_pose', self.pose_callback, 10)
        self.nav_pub = self.create_publisher(PoseStamped, '/goal_pose', qos_profile)
        
        self.get_logger().info('Movement Controller Ready. Waiting for target...')
        self.last_goal_time = self.get_clock().now()

    def pose_callback(self, msg: PoseStamped):
        # Rate Limit (2 seconds)
        current_time = self.get_clock().now()
        if (current_time - self.last_goal_time).nanoseconds < 2 * 1e9:
            return

        self.get_logger().info(f"Forwarding goal: x={msg.pose.position.x:.2f}, y={msg.pose.position.y:.2f}")

        # --- FIX 1: Timestamp Hack ---
        # Setting time to 0 tells Nav2 "Ignore the timestamp and just do it now."
        # This bypasses any System Time vs Sim Time conflicts.
        msg.header.stamp.sec = 0
        msg.header.stamp.nanosec = 0
        
        # --- FIX 2: Flatten the Z-Axis ---
        # Nav2 is a 2D navigator. A goal floating in the air (z=0.5) can cause failures.
        msg.pose.position.z = 0.0
        
        # --- FIX 3: Ensure Valid Orientation ---
        # If orientation is empty/invalid, Nav2 rejects it. Default to facing forward.
        if msg.pose.orientation.w == 0.0 and msg.pose.orientation.x == 0.0 and msg.pose.orientation.y == 0.0 and msg.pose.orientation.z == 0.0:
            msg.pose.orientation.w = 1.0

        self.nav_pub.publish(msg)
        self.last_goal_time = current_time

def main(args=None):
    rclpy.init(args=args)
    node = MovementControllerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt: pass
    finally: node.destroy_node(); rclpy.shutdown()

if __name__ == '__main__':
    main()