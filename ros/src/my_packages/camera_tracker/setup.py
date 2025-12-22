from setuptools import find_packages, setup

package_name = 'camera_tracker'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/tracker.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Robo404 Team',
    maintainer_email='robo404@example.com',
    description='Camera object tracking node using YOLO detections',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'tracker_node = camera_tracker.tracker_node:main',
        ],
    },
)
