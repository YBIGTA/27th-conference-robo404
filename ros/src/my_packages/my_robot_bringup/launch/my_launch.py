import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, AppendEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    pkg_my_robot_bringup = get_package_share_directory('my_robot_bringup')
    world_file = os.path.join(pkg_my_robot_bringup, 'worlds', 'my_world.sdf')
    
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')
    pkg_turtlebot3_gazebo = get_package_share_directory('turtlebot3_gazebo')

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

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': f'-r {world_file}'}.items(),
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

                        <link name="custom_camera_link">
                            <pose>0.15 0.0 0.25 0 0 0</pose> <inertial>
                                <mass>0.01</mass>
                                <inertia>
                                    <ixx>0.0001</ixx><ixy>0</ixy><ixz>0</ixz>
                                    <iyy>0.0001</iyy><iyz>0</iyz><izz>0.0001</izz>
                                </inertia>
                            </inertial>

                            <sensor name="camera_depth" type="depth_camera">
                                <always_on>true</always_on>
                                <update_rate>30</update_rate>
                                <topic>custom_camera/depth/image_raw</topic> <camera name="custom_realsense_depth">
                                    <horizontal_fov>1.02974</horizontal_fov>
                                    <image>
                                        <width>1920</width>
                                        <height>1080</height>
                                        <format>R_FLOAT32</format>
                                    </image>
                                    <clip>
                                        <near>0.1</near>
                                        <far>10.0</far>
                                    </clip>
                                </camera>
                            </sensor>

                            <sensor name="camera_rgb" type="camera">
                                <always_on>true</always_on>
                                <update_rate>30</update_rate>
                                <topic>custom_camera/image_raw</topic> <camera name="custom_realsense_rgb">
                                    <horizontal_fov>1.02974</horizontal_fov> <image>
                                        <width>1920</width>
                                        <height>1080</height>
                                        <format>R8G8B8</format>
                                    </image>
                                    <clip>
                                        <near>0.02</near>
                                        <far>10.0</far>
                                    </clip>
                                </camera>
                            </sensor>
                        </link>

                        <joint name="custom_camera_joint" type="fixed">
                            <parent>turtlebot3_waffle::base_link</parent>
                            <child>custom_camera_link</child>
                        </joint>

                        <plugin filename="ignition-gazebo-diff-drive-system" name="ignition::gazebo::systems::DiffDrive">
                            <left_joint>turtlebot3_waffle::wheel_left_joint</left_joint>
                            <right_joint>turtlebot3_waffle::wheel_right_joint</right_joint>
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
    )
    



    """
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

                        <link name="depth_camera_link">
                            <pose>0.15 -0.065 0.25 0 0 0</pose>
                            
                            <inertial>
                                <mass>0.01</mass>
                                <inertia>
                                    <ixx>0.0001</ixx><ixy>0</ixy><ixz>0</ixz>
                                    <iyy>0.0001</iyy><iyz>0</iyz><izz>0.0001</izz>
                                </inertia>
                            </inertial>

                            <sensor name="camera_depth" type="depth_camera">
                                <always_on>true</always_on>
                                <update_rate>30</update_rate>
                                <topic>camera/depth/image_raw</topic>
                                <camera name="intel_realsense_r200_depth">
                                    <camera_info_topic>camera/depth/camera_info</camera_info_topic>
                                    <horizontal_fov>1.02974</horizontal_fov>
                                    <image>
                                        <width>1920</width>
                                        <height>1080</height>
                                        <format>R_FLOAT32</format>
                                    </image>
                                    <clip>
                                        <near>0.1</near>
                                        <far>10.0</far>
                                    </clip>
                                    <noise>
                                        <type>gaussian</type>
                                        <mean>0.0</mean>
                                        <stddev>0.007</stddev>
                                    </noise>
                                </camera>
                            </sensor>
                        </link>

                        <joint name="depth_camera_joint" type="fixed">
                            <parent>turtlebot3_waffle::base_link</parent>
                            <child>depth_camera_link</child>
                        </joint>

                        <plugin filename="ignition-gazebo-diff-drive-system" name="ignition::gazebo::systems::DiffDrive">
                            <left_joint>turtlebot3_waffle::wheel_left_joint</left_joint>
                            <right_joint>turtlebot3_waffle::wheel_right_joint</right_joint>
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
    """

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
            # Camera depth info from (Gazebo -> Ros2)
            '/camera/depth/image_raw@sensor_msgs/msg/Image[gz.msgs.Image',
            '/camera/depth/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
            # Custom camera bridges
            '/custom_camera/image_raw@sensor_msgs/msg/Image[gz.msgs.Image',
            '/custom_camera/depth/image_raw@sensor_msgs/msg/Image[gz.msgs.Image'
        ],
        output='screen'
    )

    return LaunchDescription([
        gz_resource_path,
        gz_plugin_path,
        gz_sim,
        robot_state_publisher,
        spawn_entity,
        bridge
    ])
