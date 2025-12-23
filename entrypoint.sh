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

# 3. Load Vision API environment variables if .env exists
ENV_FILE="${ROS_WS}/src/my_packages/vision_api/.env"
if [ -f "$ENV_FILE" ]; then
  echo "[ENTRYPOINT] Loading Vision API keys from .env..."
  source "$ENV_FILE"
  export VISION_API_KEY="${OPENAI_API_KEY:-}"
  export OPENAI_API_KEY="${OPENAI_API_KEY:-}"
  export GEMINI_API_KEY="${GEMINI_API_KEY:-}"
  export HUGGINGFACE_API_TOKEN="${HUGGINGFACE_API_TOKEN:-}"
  echo "[ENTRYPOINT] Vision API keys loaded"
else
  echo "[INFO] Vision API .env not found. Create it at: $ENV_FILE"
fi

echo "[ENTRYPOINT] Environment ready. Starting shell..."
exec "$@"
