## 📦 1. Docker 이미지 빌드

```bash
docker build -t my-ros-jazzy-dev .
```

---

## ▶️ 3. 실행 순서

### 0-0. Setup API Keys on your local
set .env under ros/src/my_packages/vision_api/.env

### 0-1. 컨테이너 실행

```bash
xhost +local:root

docker run -it --rm \
  --name ros-dev \
  --gpus all \
  -e DISPLAY=$DISPLAY \
  -e QT_X11_NO_MITSHM=1 \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v $(pwd)/ros:/root/ros \
  -v $(pwd)/training:/root/training \
  -p 8501:8501 \
  my-ros-jazzy-dev
```

### 0-2. additional terminal

```bash
docker exec -it ros-dev bash
```

### 1. Gazebo 시뮬레이터

#### Run good world 
```bash
ros2 launch my_robot_bringup my_launch.py
```

#### Run bad world
```bash
ros2 launch my_robot_bringup my_launch.py world_name:=room_chairfall_1.sdf
```

### 2. Nav2

```bash
ros2 launch turtlebot3_navigation2 navigation2.launch.py use_sim_time:=True map:=/root/ros/src/my_packages/my_robot_bringup/maps/my_default_map.yaml
```

### 3. YOLOv8 노드

**GPU**

```bash
ros2 launch yolo_bringup yolov8.launch.py \
  model:=/root/training/weights/train3/chair_state_v1_best.pt device:=cuda:0 input_image_topic:=/camera/image_raw threshold:=0.5
```

### 4. Tracker

```bash
ros2 launch camera_tracker tracker.launch.py kp_tilt:=0.0 dead_zone:=500.0
```

### 5. 이미지 확인

```bash
ros2 run rqt_image_view rqt_image_view
```

### 6. Vision API (OpenAI/Gemini/Huggingface)

**Note:** Make sure you created `.env` file in step 0-0. Keys are auto-loaded by entrypoint.sh

#### OpenAI (auto-loaded from .env)
```bash
ros2 launch vision_api analyzer.launch.py \
  api_provider:=openai \
  prompt:="이 의자의 상태를 확인하고, 위험한 상태인지 판단해. 답변은 구체적으로, 간결한 문체로 해"
```

#### Gemini (auto-loaded from .env)
```bash
ros2 launch vision_api analyzer.launch.py \
  api_provider:=gemini \
  prompt:="이 의자의 상태를 확인하고, 위험한 상태인지 판단해. 답변은 구체적으로, 간결한 문체로 해"
```

#### Huggingface (auto-loaded from .env)
```bash
ros2 launch vision_api analyzer.launch.py \
  api_provider:=huggingface \
  prompt:="이 의자의 상태를 확인하고, 위험한 상태인지 판단해. 답변은 구체적으로, 간결한 문체로 해"
```

### 7. Streamlit 대시보드

Vision API 분석 결과를 웹 브라우저에서 확인할 수 있습니다.

```bash
streamlit run /root/ros/src/my_packages/vision_api/vision_api/dashboard.py --server.port 8501
```

브라우저에서 `http://localhost:8501` 접속

**표시 내용:**
- 실시간 카메라 이미지
- 최신 분석 결과
- 분석 히스토리 (최근 20개)