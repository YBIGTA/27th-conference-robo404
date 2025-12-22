# 위험 탐지 AI 로봇 프로젝트

## Teams: ROBO 404

<div align="center">
  <table>
    <tr>
      <td><a href="https://github.com/jiy0-0nv"><img src="https://github.com/jiy0-0nv.png" width="100"></a></td>
      <td><a href="https://github.com/jungin7612"><img src="https://github.com/jungin7612.png" width="100"></a></td>
      <td><a href="https://github.com/Sleepylee02"><img src="https://github.com/Sleepylee02.png" width="100"></a></td>
      <td><a href="https://github.com/gamma4638"><img src="https://github.com/gamma4638.png" width="100"></a></td>
      <td><a href="https://github.com/rammmaa"><img src="https://github.com/rammmaa.png" width="100"></a></td>
    </tr>
    <tr>
      <td>정지윤</td>
      <td>김정인</td>
      <td>이재영</td>
      <td>이준찬</td>
      <td>이하람</td>
    </tr>
  </table>
</div>


## 🛠️ 1. Pre-build Setup

First, run the repository setup script to clone required ROS packages:

```bash
chmod +x setup_repos.sh
./setup_repos.sh
```

## 📦 2. Docker 이미지 빌드

```bash
docker build -t my-ros-jazzy-dev .
```

---

## 🚀 3. 컨테이너 실행

### GPU 사용(Linux)

Need to add how do get gpu container
Need to explain about the idea of display connecting on docker

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

### CPU 실행

```bash
docker run -it --rm \
  --name ros-dev \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v $(pwd)/ros:/root/ros \
  my-ros-jazzy-dev
```

---

## 📂 3. 프로젝트 전체 구조

```
27th-conference-robo404/
├─ Dockerfile                # Docker 이미지 빌드 파일
├─ entrypoint.sh             # Docker 컨테이너 진입점 스크립트
├─ setup_repos.sh            # 외부 ROS 패키지 클론 스크립트
├─ README.md
│
├─ ros/                      # ROS2 워크스페이스
│   └─ src/
│       ├─ external/         # 외부 패키지 (setup_repos.sh로 클론)
│       │   ├─ turtlebot3_msgs/           # TurtleBot3 메시지 정의
│       │   ├─ turtlebot3_simulations/    # TurtleBot3 시뮬레이션
│       │   └─ yolo_ros/                  # YOLO ROS2 통합
│       │
│       └─ my_packages/      # 커스텀 패키지
│           ├─ my_robot_bringup/          # 로봇 실행 및 통합 설정
│           │   ├─ launch/                # 런치 파일 (my_launch.py)
│           │   ├─ maps/                  # SLAM 맵 파일 (.pgm, .yaml)
│           │   ├─ models/                # 3D 모델 (Chair, Sofa, 등)
│           │   └─ worlds/                # Gazebo 월드 파일 (.sdf)
│           │
│           └─ camera_tracker/            # 카메라 트래킹 노드
│               ├─ camera_tracker/        # 트래커 노드 구현
│               └─ launch/                # 런치 파일
│
├─ training/                 # YOLO 모델 학습
│   ├─ auto_labeler.py       # 자동 라벨링 스크립트
│   ├─ split_data.py         # 데이터 분할 스크립트
│   ├─ train.py              # 학습 스크립트
│   ├─ label_config.yaml     # 라벨 설정
│   └─ data/                 # 학습 데이터
│
└─ runs/                     # YOLO 추론 결과
    └─ detect/               # 탐지 결과
```

---

## ▶️ 4. 실행 순서

### 1. Gazebo 시뮬레이터

```bash
docker exec -it ros-dev bash
ros2 launch my_robot_bringup my_launch.py
```

### 2. Nav2

```bash
docker exec -it ros-dev bash
ros2 launch turtlebot3_navigation2 navigation2.launch.py use_sim_time:=True map:=/root/ros/src/my_packages/my_robot_bringup/maps/my_map.yaml
```

### 3. YOLOv8 노드

**CPU**

```bash
docker exec -it ros-dev bash
ros2 launch yolo_bringup yolov8.launch.py \
  model:=yolov8n device:=cpu input_image_topic:=/camera/image_raw
```

**GPU**

```bash
docker exec -it ros-dev bash
ros2 launch yolo_bringup yolov8.launch.py \
  model:=yolov8n device:=cuda:0 input_image_topic:=/camera/image_raw
```

### 4. 이미지 확인 / FPS 체크

```bash
docker exec -it ros-dev bash
ros2 run rqt_image_view rqt_image_view
# 또는
ros2 topic hz /yolo/detections
```

