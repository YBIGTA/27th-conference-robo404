## 📦 1. Docker 이미지 빌드

```bash
docker build -t my-ros-jazzy-dev .
```

---

## ▶️ 3. 실행 순서

### 0-0. 컨테이너 실행

```bash
xhost +local:root
docker run -it --rm \
  --name ros-dev \
  --gpus all \
  -e DISPLAY=$DISPLAY \
  -e QT_X11_NO_MITSHM=1 \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v $(pwd)/ros:/root/ros \
  my-ros-jazzy-dev
```

### 0-1. additional terminal

```bash
docker exec -it ros-dev bash
```

### 1. Gazebo 시뮬레이터

```bash
ros2 launch my_robot_bringup my_launch.py
```

### 2. Nav2

```bash
docker exec -it ros-dev bash
ros2 launch turtlebot3_navigation2 navigation2.launch.py use_sim_time:=True map:=/root/ros/src/my_packages/my_robot_bringup/maps/my_default_map.yaml
```

### 3. YOLOv8 노드

**GPU**

```bash
docker exec -it ros-dev bash
ros2 launch yolo_bringup yolov8.launch.py \
  model:=/root/training/weights/train3/weights/chair_state_v1_best.pt device:=cuda:0 input_image_topic:=/camera/image_raw threshold:=0.5
```

### 4. Tracker

```bash
ros2 launch camera_tracker tracker.launch.py kp_tilt:=0.0 dead_zone:=500.0
```

### 5. 이미지 확인

```bash
ros2 run rqt_image_view rqt_image_view
```

### 6. Openai

```bash
launch vision_api analyzer.launch.py api_provider:=openai prompt:="이 의자의 상태를 확인하고, 위험한 상태인지 판단해. 답변은 구체적으로, 간결한 문체로 해"
```