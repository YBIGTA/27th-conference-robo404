import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, AppendEnvironmentVariable, DeclareLaunchArgument, LogInfo
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, PythonExpression
from launch_ros.actions import Node

def generate_launch_description():
    pkg_my_robot_bringup = get_package_share_directory('my_robot_bringup')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')
    pkg_turtlebot3_gazebo = get_package_share_directory('turtlebot3_gazebo')

    # 커맨드 라인에서 받을 인자(argument) 선언
    # 실행 시 'world_name:=파일이름.sdf' 형태로 입력받습니다.
    # 입력이 없으면 default_value인 'my_world.sdf'가 사용됩니다.
    world_name_arg = DeclareLaunchArgument(
        'world_name',
        default_value='my_world.sdf',
        description='World file name'
    )
    world_name_config = LaunchConfiguration('world_name')
    
    gui_arg = DeclareLaunchArgument(
        'gui',
        default_value='true',
        description='Set to "false" to run headless.'
    )
    gui_config = LaunchConfiguration('gui')

    world_path = PathJoinSubstitution([
        pkg_my_robot_bringup, 
        'worlds',            
        world_name_config    
    ])

    models_path = os.path.join(pkg_turtlebot3_gazebo, 'models')
    share_path = os.path.dirname(pkg_turtlebot3_gazebo)
    my_models_path = os.path.join(pkg_my_robot_bringup, 'models')

    gz_resource_path = AppendEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=f"{models_path}:{share_path}:{my_models_path}"
    )
    
    gz_plugin_path = AppendEnvironmentVariable(
        name='GZ_SIM_SYSTEM_PLUGIN_PATH',
        value='/opt/ros/jazzy/lib/gz-sim-8/plugins'
    )

    headless_flag = PythonExpression([
        "' -s' if '", gui_config, "'.lower() == 'false' else ''"
    ])

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={
            'gz_args': ['-r', headless_flag, ' ', world_path]
        }.items(),
    )

    # Robot State Publisher
    robot_state_publisher = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_turtlebot3_gazebo, 'launch', 'robot_state_publisher.launch.py')
        ),
        launch_arguments={'use_sim_time': 'true'}.items(),
    )

    spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', 'waffle',
            '-topic', 'robot_description',
            '-x', '0.0', '-y', '0.0', '-z', '0.1',
            '-string', '''
                <sdf version="1.6">
                    <model name="waffle_with_sensors">
                        <include>
                            <uri>model://turtlebot3_waffle</uri>
                        </include>

                        <plugin filename="ignition-gazebo-diff-drive-system" name="ignition::gazebo::systems::DiffDrive">
                            <left_joint>wheel_left_joint</left_joint>
                            <right_joint>wheel_right_joint</right_joint>
                            <wheel_separation>0.287</wheel_separation>
                            <wheel_radius>0.033</wheel_radius>
                            <topic>/cmd_vel</topic>
                            <odom_publish_frequency>30</odom_publish_frequency>
                        </plugin>

                        <plugin filename="ignition-gazebo-sensors-system" name="ignition::gazebo::systems::Sensors">
                            <render_engine>ogre2</render_engine>
                        </plugin>

                    </model>
                </sdf>
            '''
        ],
        output='screen',
    )

    # ROS-Gazebo Bridge
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            '/cmd_vel@geometry_msgs/msg/TwistStamped]gz.msgs.Twist',
            '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            '/camera/image_raw@sensor_msgs/msg/Image[gz.msgs.Image',
            '/camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
            '/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
            # Model pose for auto-labeling (Gazebo -> ROS2)
            '/world/default/pose/info@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
            # Camera joint control (ROS2 -> Gazebo)
            '/camera/pan_cmd@std_msgs/msg/Float64]gz.msgs.Double',
            '/camera/tilt_cmd@std_msgs/msg/Float64]gz.msgs.Double',
        ],
        output='screen'
    )

    return LaunchDescription([
        LogInfo(msg=["[DEBUG] User GUI input: ", gui_config]),
        LogInfo(msg=["[DEBUG] Generated Headless Flag: ", headless_flag]),
        
        world_name_arg,
        gui_arg,
        gz_resource_path,
        gz_plugin_path,
        gz_sim,
        robot_state_publisher,
        spawn_entity,
        bridge
    ])