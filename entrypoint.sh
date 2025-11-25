#!/usr/bin/env bash
set -e

ROS_WS="/root/ros"

echo "[ENTRYPOINT] Starting ROS dev container..."
echo "[ENTRYPOINT] ROS_WS = $ROS_WS"

# 1. ROS2 Jazzy 환경 로드 (rosdep/colcon용)
if [ -f /opt/ros/jazzy/setup.bash ]; then
  source /opt/ros/jazzy/setup.bash
else
  echo "[WARN] /opt/ros/jazzy/setup.bash not found"
fi

# 2. ros 워크스페이스가 제대로 마운트 되었는지 확인
if [ ! -d "${ROS_WS}/src" ]; then
  echo "[WARN] ${ROS_WS}/src 가 없습니다. 호스트의 ./ros 를 -v 로 마운트했는지 확인하세요."
else
  cd "$ROS_WS"

  echo "[ENTRYPOINT] Running rosdep install..."
  rosdep update || echo "[WARN] rosdep update failed (network?)"
  rosdep install --from-paths src --ignore-src -r -y || echo "[WARN] rosdep install failed"

  echo "[ENTRYPOINT] Running colcon build..."
  colcon build --symlink-install || echo "[WARN] colcon build failed"
fi

echo "[ENTRYPOINT] Environment ready. Starting shell..."
exec "$@"
