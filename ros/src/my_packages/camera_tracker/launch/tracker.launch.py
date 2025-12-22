from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    # Declare launch arguments
    image_width_arg = DeclareLaunchArgument(
        'image_width',
        default_value='1920',
        description='Camera image width in pixels'
    )

    image_height_arg = DeclareLaunchArgument(
        'image_height',
        default_value='1080',
        description='Camera image height in pixels'
    )

    fov_horizontal_arg = DeclareLaunchArgument(
        'fov_horizontal',
        default_value='1.02974',
        description='Horizontal field of view in radians'
    )

    timeout_arg = DeclareLaunchArgument(
        'timeout_seconds',
        default_value='3.0',
        description='Seconds to wait before returning to home position'
    )

    kp_pan_arg = DeclareLaunchArgument(
        'kp_pan',
        default_value='0.5',
        description='Proportional gain for pan control'
    )

    kp_tilt_arg = DeclareLaunchArgument(
        'kp_tilt',
        default_value='0.5',
        description='Proportional gain for tilt control'
    )

    dead_zone_arg = DeclareLaunchArgument(
        'dead_zone',
        default_value='30.0',
        description='Dead zone around center in pixels'
    )

    target_y_offset_arg = DeclareLaunchArgument(
        'target_y_offset',
        default_value='180.0',
        description='Y offset from center in pixels (positive = camera looks up)'
    )

    # Camera tracker node
    tracker_node = Node(
        package='camera_tracker',
        executable='tracker_node',
        name='camera_tracker',
        output='screen',
        parameters=[{
            'image_width': LaunchConfiguration('image_width'),
            'image_height': LaunchConfiguration('image_height'),
            'fov_horizontal': LaunchConfiguration('fov_horizontal'),
            'timeout_seconds': LaunchConfiguration('timeout_seconds'),
            'kp_pan': LaunchConfiguration('kp_pan'),
            'kp_tilt': LaunchConfiguration('kp_tilt'),
            'pan_limit': 1.57,
            'tilt_limit': 0.52,
            'dead_zone': LaunchConfiguration('dead_zone'),
            'target_y_offset': LaunchConfiguration('target_y_offset'),
        }]
    )

    return LaunchDescription([
        image_width_arg,
        image_height_arg,
        fov_horizontal_arg,
        timeout_arg,
        kp_pan_arg,
        kp_tilt_arg,
        dead_zone_arg,
        target_y_offset_arg,
        tracker_node,
    ])
