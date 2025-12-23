from setuptools import find_packages, setup

package_name = 'vision_api'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/analyzer.launch.py']),
    ],
    install_requires=[
        'setuptools',
        'requests>=2.31.0',
        'openai>=1.0.0',
        'google-generativeai>=0.3.0',
        'Pillow>=9.0.0',
    ],
    zip_safe=True,
    maintainer='Robo404 Team',
    maintainer_email='robo404@example.com',
    description='Vision API integration for camera analysis',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'analyzer_node = vision_api.analyzer_node:main',
        ],
    },
)
