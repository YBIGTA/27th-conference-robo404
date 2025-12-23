# ROBO 404 - ROS 2 시스템 아키텍처

## 1. 전체 시스템 개요

ROBO 404는 ROS 2 Jazzy 기반의 위험 탐지 AI 로봇 시스템입니다. TurtleBot3 Waffle 플랫폼에서 YOLO 객체 탐지, 카메라 추적, AI 비전 분석을 통합합니다.

---

## 2. 전체 시스템 토픽 연결 구조

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                           ROBO 404 전체 시스템 토픽 연결 구조                           │
└──────────────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────────┐
                              │   Gazebo Simulator  │
                              │  (TurtleBot3 Waffle)│
                              └──────────┬──────────┘
                                         │
                                         │ Gazebo 센서/액추에이터
                                         ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               ROS-Gazebo Bridge (ros_gz_bridge)                         │
│                                                                                         │
│  [Gazebo → ROS]                                      [ROS → Gazebo]                     │
│  • /camera/image_raw (sensor_msgs/Image)             • /cmd_vel (geometry_msgs/Twist)   │
│  • /camera/camera_info (sensor_msgs/CameraInfo)      • /camera/pan_cmd (std_msgs/Float64)│
│  • /scan (sensor_msgs/LaserScan)                     • /camera/tilt_cmd (std_msgs/Float64)│
│  • /odom (nav_msgs/Odometry)                                                            │
│  • /clock (rosgraph_msgs/Clock)                                                         │
│  • /tf (tf2_msgs/TFMessage)                                                             │
└───────┬───────────────────────────────┬────────────────────────────────┬───────────────┘
        │                               │                                │
        │ /camera/image_raw             │ /scan, /odom, /tf              │
        │                               │                                │
        ├───────────────┬───────────────┤                                │
        │               │               │                                │
        ▼               │               ▼                                │
┌───────────────┐       │       ┌───────────────────┐                    │
│   yolo_node   │       │       │   Nav2 Stack      │                    │
│   (yolo_ros)  │       │       │ (Navigation2)     │                    │
└───────┬───────┘       │       └─────────┬─────────┘                    │
        │               │                 │                              │
        │               │                 │ /cmd_vel                     │
        │               │                 ▼                              │
        │               │         [ROS-Gazebo Bridge]                    │
        │               │             → Gazebo                           │
        │               │                                                │
        │ /yolo/detections                                               │
        │ (yolo_msgs/DetectionArray)                                     │
        ▼                                                                │
┌───────────────────┐                                                    │
│  camera_tracker   │                                                    │
│  (camera_tracker) │                                                    │
└─────────┬─────────┘                                                    │
          │                                                              │
          ├──────────────────────────────────────────────────────────────┤
          │                                                              │
          │ /camera/pan_cmd, /camera/tilt_cmd                            │
          │ (std_msgs/Float64)                                           │
          │         │                                                    │
          │         └──────────────────────────────────────────────────► │
          │                                    [ROS-Gazebo Bridge → Gazebo]
          │
          │ /camera/stable
          │ (std_msgs/Bool)
          ▼
┌───────────────────┐ ◄──────────────────────────────────────────────────┘
│  vision_analyzer  │                      /camera/image_raw
│   (vision_api)    │
└─────────┬─────────┘
          │
          │ /vision/analysis_result
          │ (std_msgs/String)
          ▼
    [외부 시스템/로깅]
```

---

## 3. 노드별 입출력 토픽 상세

### 3.1 커스텀 패키지 노드

| 노드 | 패키지 | 입력 토픽 | 출력 토픽 |
|------|--------|----------|----------|
| **yolo_node** | yolo_ros | `/camera/image_raw` | `/yolo/detections` |
| **camera_tracker_node** | camera_tracker | `/yolo/detections` | `/camera/pan_cmd`, `/camera/tilt_cmd`, `/camera/stable` |
| **vision_analyzer_node** | vision_api | `/camera/image_raw`, `/camera/stable` | `/vision/analysis_result` |

### 3.2 토픽 메시지 타입

| 토픽 | 메시지 타입 | 발행 노드 | 구독 노드 |
|------|------------|----------|----------|
| `/camera/image_raw` | `sensor_msgs/Image` | ros_gz_bridge | yolo_node, vision_analyzer |
| `/yolo/detections` | `yolo_msgs/DetectionArray` | yolo_node | camera_tracker |
| `/camera/pan_cmd` | `std_msgs/Float64` | camera_tracker | ros_gz_bridge |
| `/camera/tilt_cmd` | `std_msgs/Float64` | camera_tracker | ros_gz_bridge |
| `/camera/stable` | `std_msgs/Bool` | camera_tracker | vision_analyzer |
| `/vision/analysis_result` | `std_msgs/String` | vision_analyzer | (외부) |
| `/scan` | `sensor_msgs/LaserScan` | ros_gz_bridge | nav2 |
| `/odom` | `nav_msgs/Odometry` | ros_gz_bridge | nav2 |
| `/cmd_vel` | `geometry_msgs/Twist` | nav2/teleop | ros_gz_bridge |

---

## 4. 노드별 내부 흐름

### 4.1 yolo_node (객체 탐지)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         yolo_node 내부 흐름                          │
└─────────────────────────────────────────────────────────────────────┘

[ros_gz_bridge]                         [yolo_node]
      │                                       │
      └── /camera/image_raw ─────────────────►├── image_callback()
                (Image)                       │       │
                                              │       ▼
                                              │   YOLO 모델 추론
                                              │   (yolov8n 또는 커스텀)
                                              │       │
                                              │       ▼
                                              │   바운딩 박스 생성
                                              │       │
                                              │       ▼
                                              └──► /yolo/detections
                                                    (DetectionArray)
```

**DetectionArray 메시지 구조:**
```
detections[]:
  - class_id: int32
  - class_name: string
  - score: float64 (신뢰도 0.0~1.0)
  - bbox: BoundingBox2D
      - center.position.x, y (픽셀)
      - size.width, height (픽셀)
```

---

### 4.2 camera_tracker_node (카메라 추적)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    camera_tracker_node 내부 흐름                     │
└─────────────────────────────────────────────────────────────────────┘

[yolo_node]                             [camera_tracker_node]
      │                                       │
      └── /yolo/detections ─────────────────►├── detection_callback()
            (DetectionArray)                  │       │
                                              │       ▼
                                              │   최고 신뢰도 객체 선택
                                              │       │
                                              │       ▼
                                              │   bbox 중심점 계산
                                              │       │
                                              │       ▼
                                              │   이미지 중심과 오차 계산
                                              │       │
                                              │       ▼
                                              │   P 제어 (비례 제어)
                                              │   pan_cmd = kp * error_x
                                              │   tilt_cmd = kp * error_y
                                              │       │
                                              │       ▼
                                              │   Dead zone 체크
                                              │   (오차 < 30px → 안정)
                                              │       │
                                              ├──────►├── /camera/pan_cmd (Float64)
                                              ├──────►├── /camera/tilt_cmd (Float64)
                                              └──────►└── /camera/stable (Bool)
```

**주요 파라미터:**
| 파라미터 | 기본값 | 설명 |
|---------|--------|------|
| `image_width` | 1920 | 이미지 너비 (픽셀) |
| `image_height` | 1080 | 이미지 높이 (픽셀) |
| `kp_pan` | 0.5 | 팬 비례 게인 |
| `kp_tilt` | 0.5 | 틸트 비례 게인 |
| `dead_zone` | 30.0 | 안정화 판정 범위 (픽셀) |
| `timeout_seconds` | 3.0 | 탐지 없을 시 홈 복귀 시간 |

---

### 4.3 vision_analyzer_node (AI 비전 분석)

```
┌─────────────────────────────────────────────────────────────────────┐
│                   vision_analyzer_node 내부 흐름                     │
└─────────────────────────────────────────────────────────────────────┘

[camera_tracker]                        [vision_analyzer_node]
      │                                       │
      └── /camera/stable (Bool) ────────────►├── stable_callback()
                                              │       │
[ros_gz_bridge]                               │       ▼
      │                                       │   안정화 상태 업데이트
      └── /camera/image_raw ─────────────────►├── image_callback()
                (Image)                       │       │
                                              │       ▼
                                              │   최신 이미지 저장
                                              │       │
                                              │       ▼
                                              │   check_and_analyze() [타이머 0.1s]
                                              │       │
                                              │       ▼
                                              │   ┌─────────────────────────┐
                                              │   │ 분석 트리거 조건 체크:    │
                                              │   │ 1. is_stable == True    │
                                              │   │ 2. stable_duration >= 1s│
                                              │   │ 3. cooldown >= 5s       │
                                              │   │ 4. 분석 중 아님          │
                                              │   └────────────┬────────────┘
                                              │                │ 조건 충족
                                              │                ▼
                                              │   perform_analysis()
                                              │       │
                                              │       ▼
                                              │   VisionAPIFactory.create()
                                              │       │
                                              │       ├──► OpenAI GPT-4o
                                              │       ├──► Google Gemini
                                              │       └──► Huggingface BLIP
                                              │       │
                                              │       ▼
                                              └──► /vision/analysis_result
                                                        (String)
```

---

## 5. ROS-Gazebo Bridge 상세

### 5.1 브릿지 토픽 매핑 (my_launch.py)

```python
# Gazebo → ROS 2 (센서 데이터)
'/camera/image_raw':    gz.msgs.Image      → sensor_msgs/msg/Image
'/camera/camera_info':  gz.msgs.CameraInfo → sensor_msgs/msg/CameraInfo
'/scan':                gz.msgs.LaserScan  → sensor_msgs/msg/LaserScan
'/odom':                gz.msgs.Odometry   → nav_msgs/msg/Odometry
'/clock':               gz.msgs.Clock      → rosgraph_msgs/msg/Clock
'/tf':                  gz.msgs.Pose_V     → tf2_msgs/msg/TFMessage

# ROS 2 → Gazebo (제어 명령)
'/cmd_vel':             geometry_msgs/msg/Twist    → gz.msgs.Twist
'/camera/pan_cmd':      std_msgs/msg/Float64       → gz.msgs.Double
'/camera/tilt_cmd':     std_msgs/msg/Float64       → gz.msgs.Double
```

### 5.2 브릿지 방향

```
┌─────────────────────────────────────────────────────────────────────┐
│                     ROS-Gazebo Bridge 양방향 연결                    │
└─────────────────────────────────────────────────────────────────────┘

        Gazebo Simulator                    ROS 2 Nodes
     ┌─────────────────┐               ┌─────────────────┐
     │                 │  ──────────►  │                 │
     │   Camera        │  image_raw    │   yolo_node     │
     │   Sensor        │               │   vision_api    │
     │                 │               │                 │
     ├─────────────────┤               ├─────────────────┤
     │                 │  ──────────►  │                 │
     │   LiDAR         │  scan         │   Nav2          │
     │   Sensor        │               │                 │
     │                 │               │                 │
     ├─────────────────┤               ├─────────────────┤
     │                 │  ◄──────────  │                 │
     │   Pan/Tilt      │  pan_cmd      │   camera_tracker│
     │   Joint         │  tilt_cmd     │                 │
     │                 │               │                 │
     ├─────────────────┤               ├─────────────────┤
     │                 │  ◄──────────  │                 │
     │   Diff Drive    │  cmd_vel      │   Nav2/Teleop   │
     │   Controller    │               │                 │
     └─────────────────┘               └─────────────────┘
```

---

## 6. 데이터 흐름 시퀀스

### 6.1 객체 탐지 및 추적 흐름

```
시간 →

[1] Gazebo Camera
        │
        │ /camera/image_raw (30Hz)
        ▼
[2] yolo_node
        │ YOLO 추론 (~10Hz)
        │
        │ /yolo/detections
        ▼
[3] camera_tracker
        │ P 제어 계산
        │
        ├── /camera/pan_cmd ──► [Gazebo Pan Joint]
        ├── /camera/tilt_cmd ─► [Gazebo Tilt Joint]
        │
        │ Dead zone 판정
        │
        │ /camera/stable
        ▼
[4] vision_analyzer
        │ (stable && duration >= 1s)
        │
        │ API 호출 (OpenAI/Gemini/HF)
        │
        │ /vision/analysis_result
        ▼
[5] 외부 시스템 (로깅/알림)
```

### 6.2 자율 주행 흐름 (Nav2)

```
시간 →

[1] Gazebo LiDAR + Odometry
        │
        ├── /scan
        ├── /odom
        ├── /tf
        ▼
[2] Nav2 Stack
        │ SLAM / Localization
        │ Path Planning
        │ DWB Controller
        │
        │ /cmd_vel
        ▼
[3] ros_gz_bridge
        │
        │ gz.msgs.Twist
        ▼
[4] Gazebo Diff Drive
```

---

## 7. 실행 명령어

### 7.1 전체 시스템 실행

```bash
# 터미널 1: Gazebo 시뮬레이터 + 브릿지
ros2 launch my_robot_bringup my_launch.py

# 터미널 2: YOLO 객체 탐지
ros2 launch yolo_bringup yolov8.launch.py \
  model:=yolov8n \
  input_image_topic:=/camera/image_raw

# 터미널 3: 카메라 추적
ros2 launch camera_tracker tracker.launch.py

# 터미널 4: 비전 분석
export VISION_API_KEY="your-api-key"
ros2 launch vision_api analyzer.launch.py api_provider:=openai
```

### 7.2 토픽 모니터링

```bash
# 전체 토픽 목록
ros2 topic list

# YOLO 탐지 결과
ros2 topic echo /yolo/detections

# 카메라 안정화 상태
ros2 topic echo /camera/stable

# 비전 분석 결과
ros2 topic echo /vision/analysis_result
```

### 7.3 노드 그래프 시각화

```bash
# rqt_graph로 노드/토픽 연결 시각화
ros2 run rqt_graph rqt_graph
```

---

## 8. 패키지 의존성 그래프

```
┌─────────────────────────────────────────────────────────────────────┐
│                        패키지 의존성 구조                            │
└─────────────────────────────────────────────────────────────────────┘

my_robot_bringup
    ├── ros_gz_sim
    ├── ros_gz_bridge
    ├── turtlebot3_gazebo
    ├── turtlebot3_navigation2
    └── robot_state_publisher

camera_tracker
    ├── rclpy
    ├── std_msgs
    └── yolo_msgs ◄──────────────────┐
                                     │
vision_api                           │
    ├── rclpy                        │
    ├── std_msgs                     │
    ├── sensor_msgs                  │
    └── cv_bridge                    │
                                     │
yolo_ros ────────────────────────────┘
    ├── rclpy
    ├── sensor_msgs
    ├── yolo_msgs
    └── ultralytics
```

---

## 9. 문제 해결

### 9.1 토픽 연결 확인

```bash
# 노드가 토픽을 발행하는지 확인
ros2 topic info /camera/image_raw

# 토픽 발행 주파수 확인
ros2 topic hz /camera/image_raw

# 노드 연결 상태 확인
ros2 node info /yolo_node
```

### 9.2 일반적인 문제

| 증상 | 원인 | 해결 |
|------|------|------|
| 이미지 토픽 없음 | Gazebo 브릿지 미실행 | `my_launch.py` 재실행 |
| YOLO 탐지 안됨 | 모델 경로 오류 | 모델 경로 확인 |
| 카메라 안정화 안됨 | YOLO 탐지 없음 | 객체가 카메라 시야에 있는지 확인 |
| 비전 분석 안됨 | API 키 미설정 | `VISION_API_KEY` 환경변수 설정 |
