"""Launch file for Vision Analyzer Node."""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, EnvironmentVariable
from launch_ros.actions import Node


def generate_launch_description():
    # Launch arguments
    api_provider_arg = DeclareLaunchArgument(
        'api_provider',
        default_value='openai',
        description='Vision API provider (openai, gemini, huggingface)'
    )

    api_key_arg = DeclareLaunchArgument(
        'api_key',
        default_value=EnvironmentVariable('VISION_API_KEY', default_value=''),
        description='API key for the vision provider'
    )

    api_model_arg = DeclareLaunchArgument(
        'api_model',
        default_value='',
        description='Model name (optional, uses provider default if empty)'
    )

    prompt_arg = DeclareLaunchArgument(
        'prompt',
        default_value='Describe the main object in this image.',
        description='Analysis prompt'
    )

    min_stable_arg = DeclareLaunchArgument(
        'min_stable_duration',
        default_value='1.0',
        description='Minimum stable duration before analysis (seconds)'
    )

    cooldown_arg = DeclareLaunchArgument(
        'analysis_cooldown',
        default_value='5.0',
        description='Cooldown between analyses (seconds)'
    )

    image_topic_arg = DeclareLaunchArgument(
        'image_topic',
        default_value='/camera/image_raw',
        description='Image topic to subscribe'
    )

    stable_topic_arg = DeclareLaunchArgument(
        'stable_topic',
        default_value='/camera/stable',
        description='Camera stability topic to subscribe'
    )

    # Node
    analyzer_node = Node(
        package='vision_api',
        executable='analyzer_node',
        name='vision_analyzer',
        output='screen',
        parameters=[{
            'api_provider': LaunchConfiguration('api_provider'),
            'api_key': LaunchConfiguration('api_key'),
            'api_model': LaunchConfiguration('api_model'),
            'analysis_prompt': LaunchConfiguration('prompt'),
            'min_stable_duration': LaunchConfiguration('min_stable_duration'),
            'analysis_cooldown': LaunchConfiguration('analysis_cooldown'),
            'image_topic': LaunchConfiguration('image_topic'),
            'stable_topic': LaunchConfiguration('stable_topic'),
        }]
    )

    return LaunchDescription([
        api_provider_arg,
        api_key_arg,
        api_model_arg,
        prompt_arg,
        min_stable_arg,
        cooldown_arg,
        image_topic_arg,
        stable_topic_arg,
        analyzer_node,
    ])
