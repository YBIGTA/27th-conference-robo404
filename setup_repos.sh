#!/bin/bash

# Setup ROS repositories script
# This script checks if repositories exist and clones them if they don't

# Get current directory and append /ros/src
CURRENT_DIR=$(pwd)
ROS_SRC_DIR="$CURRENT_DIR/ros/src"

echo "Setting up ROS repositories in $ROS_SRC_DIR..."

# Create src directory if it doesn't exist
mkdir -p "$ROS_SRC_DIR"
cd "$ROS_SRC_DIR"

# Check and clone turtlebot3_simulations
if [ ! -d "turtlebot3_simulations" ]; then
    echo "Cloning turtlebot3_simulations..."
    git clone -b jazzy https://github.com/ROBOTIS-GIT/turtlebot3_simulations.git
else
    echo "turtlebot3_simulations already exists, skipping..."
fi

# Check and clone turtlebot3_msgs
if [ ! -d "turtlebot3_msgs" ]; then
    echo "Cloning turtlebot3_msgs..."
    git clone -b jazzy https://github.com/ROBOTIS-GIT/turtlebot3_msgs.git
else
    echo "turtlebot3_msgs already exists, skipping..."
fi

# Check and clone yolo_ros
if [ ! -d "yolo_ros" ]; then
    echo "Cloning yolo_ros..."
    git clone https://github.com/mgonzs13/yolo_ros.git
else
    echo "yolo_ros already exists, skipping..."
fi

echo "Repository setup complete!"