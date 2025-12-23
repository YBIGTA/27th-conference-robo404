# ROS 노드 이미지 플로우 다이어그램

ROS 2 기반 위험 탐지 로봇 시스템의 토픽 흐름도

---

## 1. 전체 시스템 개요

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Gazebo Simulator                                  │
│                                                                             │
│  ┌──────────────┐  ┌────────────┐  ┌────────┐  ┌───────────────────────┐   │
│  │ Camera Sensor│  │   LiDAR    │  │  IMU   │  │   DiffDrive Plugin    │   │
│  └──────┬───────┘  └─────┬──────┘  └────┬───┘  └───────────┬───────────┘   │
│         │                │              │                  │               │
└─────────┼────────────────┼──────────────┼──────────────────┼───────────────┘
          │                │              │                  ▲
          ▼                ▼              ▼                  │
   /camera/image_raw    /scan          /imu              /cmd_vel
          │                │              │                  │
          │                │              │                  │
     ┌────┴────┐      ┌────┴────┐    ┌────┴────┐      ┌─────┴─────┐
     │         │      │         │    │         │      │           │
     ▼         ▼      ▼         ▼    ▼         ▼      │           │
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐      │           │
│  YOLO   │ │ Vision  │ │  Nav2   │ │ (기타)  │      │   Nav2    │
│  Node   │ │   API   │ │  AMCL   │ │         │      │ Planner   │
└─────────┘ └─────────┘ └─────────┘ └─────────┘      └───────────┘
```

---

## 2. 이미지 처리 파이프라인 (비전 시스템)

```
                    ┌───────────────────────────────────────────┐
                    │          이미지 처리 파이프라인           │
                    └───────────────────────────────────────────┘

┌─────────────┐    /camera/image_raw     ┌────────────┐
│   Gazebo    │ ────────────────────────►│    YOLO    │
│   Camera    │                          │    Node    │
│  (1920x1080)│                          │  (yolov8)  │
└─────────────┘                          └─────┬──────┘
       │                                       │
       │                                       │ /yolo/detections
       │ /camera/image_raw                     │ (DetectionArray)
       │                                       │
       │                                       ▼
       │                              ┌────────────────┐
       │                              │ Camera Tracker │
       │                              │   (P 제어)     │
       │                              └───────┬────────┘
       │                                      │
       │      ┌───────────────────────────────┼───────────────────────┐
       │      │                               │                       │
       │      ▼                               ▼                       ▼
       │  /camera/pan_cmd             /camera/tilt_cmd         /camera/stable
       │  (Float64, rad)              (Float64, rad)           (Bool)
       │      │                               │                       │
       │      └───────────────┬───────────────┘                       │
       │                      ▼                                       │
       │               ┌─────────────┐                                │
       │               │   Gazebo    │                                │
       │               │ Pan/Tilt    │                                │
       │               │  Control    │                                │
       │               └─────────────┘                                │
       │                                                              │
       │                                                              ▼
       │                                                     ┌────────────────┐
       └────────────────────────────────────────────────────►│   Vision API   │
                                                             │   Analyzer     │
                                                             │ (GPT-4o/Gemini)│
                                                             └───────┬────────┘
                                                                     │
                                                                     ▼
                                                          /vision/analysis_result
                                                          (String)
```

### 이미지 처리 흐름 설명

1. **Gazebo Camera** → `/camera/image_raw` 발행
2. **YOLO Node**가 이미지 수신 → 객체 탐지 → `/yolo/detections` 발행
3. **Camera Tracker**가 탐지 결과 수신 → 가장 신뢰도 높은 객체 추적
4. **Camera Tracker** → 팬/틸트 명령 (`/camera/pan_cmd`, `/camera/tilt_cmd`) 발행
5. 객체가 Dead Zone(80px) 내 진입 시 → `/camera/stable = true` 발행
6. **Vision API**가 안정 신호 + 이미지 수신 → AI 분석 → `/vision/analysis_result` 발행

---

## 3. Nav2 네비게이션 파이프라인

```
                    ┌───────────────────────────────────────────┐
                    │        Nav2 네비게이션 파이프라인         │
                    └───────────────────────────────────────────┘

┌─────────────┐                    ┌─────────────┐
│   LiDAR     │ ─────/scan────────►│    AMCL     │
│   Sensor    │   (LaserScan)      │Localization │
└─────────────┘                    └──────┬──────┘
                                          │
                                          │ 위치 추정
                                          ▼
┌─────────────┐                    ┌─────────────┐        ┌─────────────┐
│  Odometry   │ ─────/odom────────►│   Costmap   │───────►│   Global    │
│ (DiffDrive) │   (Odometry)       │   Server    │        │   Planner   │
└─────────────┘                    └─────────────┘        └──────┬──────┘
                                          ▲                      │
                                          │                      │ 경로
┌─────────────┐                           │                      ▼
│     TF      │ ──────/tf─────────────────┘               ┌─────────────┐
│  Transform  │    (TFMessage)                            │   Local     │
└─────────────┘                                           │   Planner   │
                                                          │   (DWB)     │
                                                          └──────┬──────┘
                                                                 │
                                                                 │
                                                                 ▼
                                                             /cmd_vel
                                                             (Twist)
                                                                 │
                                                                 ▼
                                                          ┌─────────────┐
                                                          │  DiffDrive  │
                                                          │   Plugin    │
                                                          │  (Gazebo)   │
                                                          └─────────────┘
```

### 네비게이션 흐름 설명

1. **LiDAR** → `/scan` 발행 (레이저 스캔 데이터)
2. **DiffDrive Plugin** → `/odom`, `/tf` 발행 (오도메트리)
3. **AMCL**이 `/scan` + `/odom`으로 현재 위치 추정
4. **Global Planner**가 목표까지 경로 생성
5. **DWB Local Planner**가 경로 추종 → `/cmd_vel` 발행
6. **DiffDrive Plugin**이 `/cmd_vel` 수신 → 로봇 구동

---

## 4. 통합 시스템 다이어그램

```
                              ┌─────────────────────────┐
                              │    TurtleBot3 Waffle    │
                              │    (Gazebo Simulator)   │
                              └───────────┬─────────────┘
                                          │
          ┌───────────────────────────────┼───────────────────────────────┐
          │                               │                               │
          ▼                               ▼                               ▼
   /camera/image_raw                   /scan                          /odom
          │                               │                               │
          │                               │                               │
    ┌─────┴─────┐                         └──────────┬────────────────────┘
    │           │                                    │
    ▼           ▼                                    ▼
┌───────┐  ┌──────────┐                      ┌─────────────┐
│ YOLO  │  │ Vision   │                      │    Nav2     │
│ Node  │  │   API    │◄──/camera/stable──┐  │   Stack     │
└───┬───┘  └────┬─────┘                   │  └──────┬──────┘
    │           │                         │         │
    │           ▼                         │         ▼
    │  /vision/analysis_result            │     /cmd_vel
    │           │                         │         │
    │           ▼                         │         ▼
    │    ┌─────────────┐                  │  ┌─────────────┐
    │    │ 외부 시스템  │                  │  │  DiffDrive  │
    │    │ (알림/로깅) │                  │  │   Plugin    │
    │    └─────────────┘                  │  └─────────────┘
    │                                     │
    ▼                                     │
/yolo/detections                          │
    │                                     │
    ▼                                     │
┌────────────────┐                        │
│ Camera Tracker │────────────────────────┘
└───────┬────────┘
        │
        ├──► /camera/pan_cmd ──┐
        │                      │
        └──► /camera/tilt_cmd ─┼──► Gazebo Camera Control
                               │
```

---

## 5. 토픽 관계 테이블

### 비전 시스템 토픽

| 토픽 | 메시지 타입 | QoS | 퍼블리셔 | 서브스크라이버 |
|------|-------------|-----|----------|----------------|
| `/camera/image_raw` | sensor_msgs/Image | BEST_EFFORT | Gazebo | YOLO, Vision API |
| `/yolo/detections` | yolo_msgs/DetectionArray | BEST_EFFORT | YOLO Node | Camera Tracker |
| `/camera/pan_cmd` | std_msgs/Float64 | 10 | Camera Tracker | Gazebo |
| `/camera/tilt_cmd` | std_msgs/Float64 | 10 | Camera Tracker | Gazebo |
| `/camera/stable` | std_msgs/Bool | 10 | Camera Tracker | Vision API |
| `/vision/analysis_result` | std_msgs/String | 10 | Vision API | (외부) |

### 네비게이션 토픽

| 토픽 | 메시지 타입 | QoS | 퍼블리셔 | 서브스크라이버 |
|------|-------------|-----|----------|----------------|
| `/scan` | sensor_msgs/LaserScan | BEST_EFFORT | Gazebo LiDAR | Nav2 AMCL |
| `/odom` | nav_msgs/Odometry | 10 | DiffDrive | Nav2 |
| `/tf` | tf2_msgs/TFMessage | 10 | DiffDrive | Nav2, AMCL |
| `/cmd_vel` | geometry_msgs/Twist | 10 | Nav2 Planner | DiffDrive |

### 기타 토픽

| 토픽 | 메시지 타입 | 퍼블리셔 | 용도 |
|------|-------------|----------|------|
| `/clock` | rosgraph_msgs/Clock | Gazebo | 시뮬레이션 시간 동기화 |
| `/imu` | sensor_msgs/Imu | Gazebo IMU | 관성 측정 |
| `/camera/camera_info` | sensor_msgs/CameraInfo | Gazebo | 카메라 캘리브레이션 |
| `/joint_states` | sensor_msgs/JointState | Gazebo | 조인트 상태 |

---

## 6. 노드별 상세 정보

### Gazebo Camera
- **해상도**: 1920 x 1080
- **FOV (수평)**: ~59° (1.02974 rad)
- **출력 토픽**: `/camera/image_raw`
- **프레임**: `camera_link`

### YOLO Node
- **모델**: yolov8n (기본) 또는 커스텀 모델 (chair_state_v1)
- **입력**: `/camera/image_raw`
- **출력**: `/yolo/detections` (DetectionArray)
- **임계값**: 0.5 (기본)

### Camera Tracker
- **제어 방식**: P 제어 (Proportional Control)
- **팬 이득 (kp_pan)**: 0.3
- **틸트 이득 (kp_tilt)**: 0.2
- **Dead Zone**: 80 픽셀 (중앙 기준)
- **타임아웃**: 3초 (객체 미탐지 시 홈 위치 복귀)

### Vision API Analyzer
- **지원 API**: OpenAI GPT-4o, Google Gemini, Huggingface VLM
- **최소 안정화 시간**: 1.0초
- **분석 쿨다운**: 5.0초
- **트리거 조건**: `/camera/stable = true` + 안정화 시간 경과

### Nav2 Stack
- **로컬라이제이션**: AMCL (Adaptive Monte Carlo Localization)
- **로컬 플래너**: DWB (Dynamic Window Based)
- **최대 선속도**: 0.5 m/s
- **최대 각속도**: 2.0 rad/s
- **프레임**: map → odom → base_footprint

### TurtleBot3 Waffle
- **플랫폼**: 차동 구동 (Differential Drive)
- **바퀴 간격**: 0.287m
- **바퀴 반경**: 0.033m
- **센서**: LiDAR, 카메라, IMU

---

## 7. 실행 명령어

```bash
# 1. Gazebo 시뮬레이터 + 로봇 실행
ros2 launch my_robot_bringup my_launch.py

# 2. YOLO 객체 탐지
ros2 launch yolo_bringup yolov8.launch.py model:=yolov8n input_image_topic:=/camera/image_raw

# 3. 카메라 추적
ros2 launch camera_tracker tracker.launch.py

# 4. Vision API 분석
ros2 launch vision_api analyzer.launch.py api_provider:=openai
```
