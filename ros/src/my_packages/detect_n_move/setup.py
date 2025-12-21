from setuptools import find_packages, setup

package_name = 'detect_n_move'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/detect_n_move.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Robo404 Team',
    maintainer_email='robo404@example.com',
    description='Object detection and movement control package',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'detection_handler = detect_n_move.detection_handler:main',
            'movement_controller = detect_n_move.movement_controller:main',
            'detect_n_move_node = detect_n_move.detect_n_move_node:main',
        ],
    },
)