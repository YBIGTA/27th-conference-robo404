#!/usr/bin/env python3
"""
Movement Controller Node (Nav2 Client)

Logic:
1. Receive 'approach_chair' command.
2. Receive 3D Pose from detection_handler.
3. Send Goal to Nav2 Action Server.
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult

class MovementControllerNode(Node):
    def __init__(self):
        super().__init__('movement_controller_node')
        
        self.nav = BasicNavigator()
        self.current_goal_pose = None
        self.processing_goal = False

        # Subscribers
        self.create_subscription(String, '/movement_command', self.command_callback, 10)
        self.create_subscription(PoseStamped, '/target_pose', self.pose_callback, 10) # Listens to 3D pose
        
        self.get_logger().info('Nav2 Movement Controller Initialized')

    def pose_callback(self, msg: PoseStamped):
        # Always update the latest known location of the target
        self.current_goal_pose = msg

    def command_callback(self, msg: String):
        command = msg.data
        
        if command == 'stop':
            self.nav.cancelTask()
            self.processing_goal = False
            self.get_logger().info('Nav2 Task Cancelled')
            
        elif 'approach' in command:
            if self.current_goal_pose and not self.processing_goal:
                self.processing_goal = True
                self.get_logger().info(f"Sending Nav2 Goal for {command}...")
                
                # Send goal to Nav2
                self.nav.goToPose(self.current_goal_pose)
                
                # Check result in a loop or timer (Simplified here)
                # In real code, you might want a timer to check nav.isTaskComplete()

def main(args=None):
    rclpy.init(args=args)
    node = MovementControllerNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()