import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    # Get package directory
    pkg_detect_n_move = get_package_share_directory('detect_n_move')
    
    # Declare launch arguments
    confidence_threshold_arg = DeclareLaunchArgument(
        'confidence_threshold',
        default_value='0.7',
        description='Confidence threshold for object detection'
    )
    
    target_objects_arg = DeclareLaunchArgument(
        'target_objects',
        default_value='["chair", "red_ball"]',
        description='List of target objects to detect and approach'
    )
    
    linear_speed_arg = DeclareLaunchArgument(
        'linear_speed',
        default_value='0.2',
        description='Linear speed for robot movement (m/s)'
    )
    
    angular_speed_arg = DeclareLaunchArgument(
        'angular_speed',
        default_value='0.5',
        description='Angular speed for robot movement (rad/s)'
    )
    
    detection_timeout_arg = DeclareLaunchArgument(
        'detection_timeout',
        default_value='3.0',
        description='Timeout for losing track of target (seconds)'
    )
    
    # Node configurations
    detection_handler_node = Node(
        package='detect_n_move',
        executable='detection_handler',
        name='detection_handler_node',
        output='screen',
        parameters=[{
            'confidence_threshold': LaunchConfiguration('confidence_threshold'),
            'target_objects': LaunchConfiguration('target_objects'),
            'detection_timeout': LaunchConfiguration('detection_timeout')
        }],
        remappings=[
            ('/yolo/detections', '/yolo/detections'),
            ('/detection_events', '/detection_events'),
            ('/target_position', '/target_position'),
            ('/movement_command', '/movement_command')
        ]
    )
    
    movement_controller_node = Node(
        package='detect_n_move',
        executable='movement_controller',
        name='movement_controller_node',
        output='screen',
        parameters=[{
            'linear_speed': LaunchConfiguration('linear_speed'),
            'angular_speed': LaunchConfiguration('angular_speed'),
            'approach_distance': 1.0,
            'position_tolerance': 0.1,
            'angle_tolerance': 0.1
        }],
        remappings=[
            ('/movement_command', '/movement_command'),
            ('/target_position', '/target_position'),
            ('/odom', '/odom'),
            ('/cmd_vel', '/cmd_vel'),
            ('/movement_status', '/movement_status')
        ]
    )
    
    # Alternative: Single integrated node
    detect_n_move_node = Node(
        package='detect_n_move',
        executable='detect_n_move_node',
        name='detect_n_move_node',
        output='screen',
        parameters=[{
            'confidence_threshold': LaunchConfiguration('confidence_threshold'),
            'target_objects': LaunchConfiguration('target_objects'),
            'linear_speed': LaunchConfiguration('linear_speed'),
            'angular_speed': LaunchConfiguration('angular_speed'),
            'detection_timeout': LaunchConfiguration('detection_timeout')
        }],
        remappings=[
            ('/yolo/detections', '/yolo/detections'),
            ('/cmd_vel', '/cmd_vel'),
            ('/detect_move_status', '/detect_move_status'),
            ('/detection_events', '/detection_events')
        ]
    )
    
    return LaunchDescription([
        confidence_threshold_arg,
        target_objects_arg,
        linear_speed_arg,
        angular_speed_arg,
        detection_timeout_arg,
        
        # Launch the integrated node (comment out for separate nodes)
        detect_n_move_node,
        
        # Uncomment these for separate detection and movement nodes
        # detection_handler_node,
        # movement_controller_node,
    ])