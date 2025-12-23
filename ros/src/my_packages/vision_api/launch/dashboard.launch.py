"""Launch file for Vision API Streamlit Dashboard."""

import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    # Get package path
    pkg_path = get_package_share_directory('vision_api')
    dashboard_path = os.path.join(
        pkg_path, '..', '..', '..', '..', 'src',
        'my_packages', 'vision_api', 'vision_api', 'dashboard.py'
    )

    # Alternative: use installed package location
    # For development, use direct path
    import vision_api
    dashboard_path = os.path.join(
        os.path.dirname(vision_api.__file__),
        'dashboard.py'
    )

    # Run streamlit
    streamlit_cmd = ExecuteProcess(
        cmd=[
            'streamlit', 'run', dashboard_path,
            '--server.port', '8501',
            '--server.headless', 'true'
        ],
        output='screen'
    )

    return LaunchDescription([
        streamlit_cmd,
    ])
