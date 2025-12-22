#!/usr/bin/env python3
"""
Movement Controller Node (Simple Version)
Logic: Get chair coordinate -> Move toward chair -> Done!
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult

class MovementControllerNode(Node):
    def __init__(self):
        super().__init__('movement_controller_node')
        
        # Initialize Nav2
        self.nav = BasicNavigator()
        
        # Simple state
        self.navigation_in_progress = False
        self.last_goal_time = self.get_clock().now()
        
        # Subscriber
        self.create_subscription(PoseStamped, '/target_pose', self.pose_callback, 10)
        
        # Timer to check navigation status
        self.timer = self.create_timer(1.0, self.check_navigation_status)
        
        self.get_logger().info('Simple Movement Controller Ready. Waiting for chair...')

    def pose_callback(self, msg: PoseStamped):
        # Rate Limit (2 seconds)
        current_time = self.get_clock().now()
        if (current_time - self.last_goal_time).nanoseconds < 2 * 1e9:
            return

        # Skip if already navigating
        if self.navigation_in_progress:
            return

        self.get_logger().info(f"Moving to chair at: x={msg.pose.position.x:.2f}, y={msg.pose.position.y:.2f}")

        # Prepare goal pose
        goal_pose = PoseStamped()
        goal_pose.header.frame_id = 'map'
        goal_pose.header.stamp = self.nav.get_clock().now().to_msg()
        
        # Position (flattened for 2D navigation)
        goal_pose.pose.position.x = msg.pose.position.x
        goal_pose.pose.position.y = msg.pose.position.y
        goal_pose.pose.position.z = 0.0
        
        # Default orientation
        goal_pose.pose.orientation.w = 1.0

        # Start navigation
        self.get_logger().info("Sending goal to Nav2...")
        self.nav.goToPose(goal_pose)
        self.navigation_in_progress = True
        self.last_goal_time = current_time
        
        # Debug: Check if Nav2 accepted the goal
        self.create_timer(2.0, self.check_nav2_status)

    def check_navigation_status(self):
        """Simple check if navigation is complete"""
        if not self.navigation_in_progress:
            return
            
        if self.nav.isTaskComplete():
            result = self.nav.getResult()
            self.navigation_in_progress = False
            
            if result == TaskResult.SUCCEEDED:
                self.get_logger().info("✅ Reached chair!")
            elif result == TaskResult.FAILED:
                self.get_logger().error("❌ Navigation failed!")
            else:
                self.get_logger().warn(f"Navigation result: {result}")

    def check_nav2_status(self):
        """Debug Nav2 connection"""
        try:
            if self.nav.isTaskComplete():
                self.get_logger().info("Nav2 task completed (quick finish)")
            else:
                self.get_logger().info("Nav2 task is running...")
        except Exception as e:
            self.get_logger().error(f"Nav2 connection error: {e}")
        
        # Only run once
        self.destroy_timer(self.check_nav2_status)

def main(args=None):
    rclpy.init(args=args)
    node = MovementControllerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt: pass
    finally: node.destroy_node(); rclpy.shutdown()

if __name__ == '__main__':
    main()