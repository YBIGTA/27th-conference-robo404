<div align="center">

# ROBO 404

### *Autonomous Hazard Detection Robot System*

<br>

**자율 순찰 · 실시간 탐지 · AI 안전성 평가**

<br>

![ROS2](https://img.shields.io/badge/ROS2-Jazzy-22314E?style=flat-square&logo=ros&logoColor=white)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-00FFFF?style=flat-square)
![Gazebo](https://img.shields.io/badge/Gazebo-Garden-F58025?style=flat-square)
![Docker](https://img.shields.io/badge/Docker-GPU-2496ED?style=flat-square&logo=docker&logoColor=white)

<br>

[시작하기](#8-실행-방법-how-to-run) · [시스템 구조](#3-전체-시스템-구조-system-architecture) · [API 설정](#api-키-설정) · [팀 소개](#12-팀-구성-및-역할-team-robo-404)

</div>

---

## 📋 목차

1. [프로젝트 개요](#1-프로젝트-개요-overview)
2. [문제 정의](#2-문제-정의-problem-statement)
3. [시스템 구조](#3-전체-시스템-구조-system-architecture)
4. [기술 스택](#4-기술-스택-tech-stack)
5. [데이터 설명](#5-데이터-설명-dataset)
6. [핵심 방법론](#6-핵심-방법론-methodology)
7. [실험 및 결과](#7-실험-및-결과-experiments--results)
8. [실행 방법](#8-실행-방법-how-to-run)
9. [프로젝트 구조](#9-프로젝트-구조-directory-structure)
10. [ROS2 인터페이스](#10-ros2-인터페이스-ros2-interface)
11. [한계점 및 향후 계획](#11-한계점-및-향후-계획-limitations--future-work)
12. [팀 구성](#12-팀-구성-및-역할-team-robo-404)

---

## 🚀 빠른 시작 (Quick Start)

```bash
# 1. 저장소 클론 및 설정
git clone <repository-url> && cd 27th-conference-robo404
chmod +x setup_repos.sh && ./setup_repos.sh

# 2. Docker 빌드 및 실행
docker build -t my-ros-jazzy-dev .
xhost +local:root && docker run -it --rm --gpus all \
  -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v $(pwd)/ros:/root/ros -v $(pwd)/training:/root/training \
  my-ros-jazzy-dev

# 3. 시뮬레이션 시작 (컨테이너 내부)
ros2 launch my_robot_bringup my_launch.py world_name:=room_chairfall_1.sdf
```

> 📖 자세한 실행 방법은 [실행 방법](#8-실행-방법-how-to-run) 섹션을 참고하세요.

---

## 1. 프로젝트 개요 (Overview)

### 배경
실내 환경에서 넘어진 의자, 불안정한 가구 등은 보행자에게 위험을 초래할 수 있지만, 인간의 지속적인 모니터링에는 한계가 있습니다. 특히 대규모 시설이나 고령자 시설에서는 실시간 안전 모니터링이 중요한 과제입니다.

### 목표
**입력**: TurtleBot3 로봇의 카메라 영상과 센서 데이터  
**처리**: YOLO 객체 탐지 → 지능형 카메라 트래킹 → 다중 AI 비전 API 분석  
**출력**: 실시간 위험도 평가 및 안전성 분석 리포트

---

## 2. 문제 정의 (Problem Statement)

**"실내 환경에서 가구의 위험 상태를 자동으로 탐지하고 안전성을 평가하는 자율 순찰 로봇 시스템 구축"**

- **대상 환경**: 실내 공간 (사무실, 거주 공간, 공공시설)
- **대상 객체**: 의자, 소파, 테이블 등 가구류
- **목표 성능**: 실시간 객체 탐지 (30+ FPS), AI 분석 정확도 95%+

---

## 3. 전체 시스템 구조 (System Architecture)

```
[Camera Input]
      ↓
[YOLO Object Detection] → [Bounding Box Detection]
      ↓                           ↓
[Camera PTZ Tracking]    [Object Classification]
      ↓
[Image Stabilization]
      ↓
[Multi-API Vision Analysis]
↙        ↓        ↘
[OpenAI]  [Gemini]  [HuggingFace]
      ↓
[Safety Assessment Report]
      ↓
[ROS Topic Publishing]
```

### 주요 컴포넌트
- **로봇 플랫폼**: TurtleBot3 Waffle (LIDAR + Camera)
- **시뮬레이션**: Gazebo 물리 엔진
- **네비게이션**: ROS2 Nav2 스택
- **객체 탐지**: 커스텀 학습된 YOLOv8 모델
- **카메라 제어**: 비례제어 기반 PTZ 트래킹
- **AI 분석**: OpenAI/Gemini/HuggingFace Vision API

---

## 4. 기술 스택 (Tech Stack)

### Backend / Core
- **Language**: Python 3.12, C++
- **Framework**: ROS2 Jazzy, OpenCV
- **Model**: YOLOv8 (Ultralytics), 커스텀 학습 모델

### System / Infra
- **OS**: Ubuntu 24.04 (ROS2 Jazzy 호환)
- **Hardware**: NVIDIA GPU 지원 (CUDA)
- **Container**: Docker with GPU runtime
- **Simulation**: Gazebo Garden

### AI / Vision
- **Object Detection**: YOLOv8 (가구 위험 상태 특화)
- **Vision API**: OpenAI GPT-4V, Google Gemini Vision, HuggingFace
- **Camera Control**: 실시간 PTZ 트래킹

---

## 5. 데이터 설명 (Dataset)

### 훈련 데이터
- **데이터 출처**: Gazebo 시뮬레이션 환경에서 수집된 가구 이미지
- **데이터 규모**: 커스텀 라벨링된 가구 상태 데이터셋
- **입력 형태**: RGB 이미지 (640x480)
- **출력 형태**: YOLO 바운딩 박스 + 안전성 분석 텍스트

| 항목 | 설명 |
|----|-----|
| 데이터 수 | 커스텀 가구 상태 데이터셋 |
| 입력 형태 | RGB 카메라 이미지 (640x480) |
| 출력 형태 | 바운딩 박스 + AI 안전성 평가 |
| 전처리 | YOLO 정규화, 이미지 안정화 |

### 라벨 구조
```yaml
# 주요 클래스
0: red_ball      # 테스트용 객체
1: chair         # 의자 (위험 상태 탐지 대상)
2: sofa          # 소파
3: table         # 테이블
```

---

## 6. 핵심 방법론 (Methodology)

### 1단계: 객체 탐지
- **YOLOv8 모델**: 가구 객체에 특화된 커스텀 학습
- **실시간 추론**: GPU 가속을 통한 30+ FPS 성능
- **신뢰도 임계값**: 0.5 이상에서 객체 인식

### 2단계: 지능형 카메라 트래킹
```python
# 비례제어 알고리즘
error_x = target_center_x - camera_center_x
pan_velocity = kp_pan * error_x

# 데드존 처리
if abs(error) < dead_zone:
    camera_stabilized = True
```

### 3단계: AI 비전 분석
- **다중 API 지원**: 장애 허용성 및 결과 비교 분석
- **구조화된 프롬프트**: "이 의자의 상태를 확인하고, 위험한 상태인지 판단해"
- **자동 트리거**: 카메라 안정화 시점에서 분석 실행

---

## 7. 실험 및 결과 (Experiments & Results)

### 실험 설정
- **환경**: Gazebo 시뮬레이션 (room_chairfall_*.sdf)
- **로봇**: TurtleBot3 Waffle + RGB 카메라 + LIDAR
- **모델**: 커스텀 YOLOv8 (chair_state_v1_best.pt)

### 성능 메트릭
| Metric | Result |
|--------|--------|
| 객체 탐지 정확도 | 95%+ (훈련된 모델 기준) |
| 실시간 추론 속도 | 30+ FPS (GPU 환경) |
| 카메라 트래킹 지연시간 | < 200ms |
| AI 분석 응답 시간 | 2-5초 (API별 상이) |

### 핵심 성과
- **자율 순찰**: Nav2를 통한 실내 맵 기반 자율 네비게이션
- **실시간 트래킹**: 객체 탐지 시 자동 카메라 추적 및 안정화
- **다중 AI 분석**: 3개 Vision API의 교차 검증을 통한 신뢰성 향상

---

## 8. 실행 방법 (How to Run)

### 사전 준비
```bash
# 1. 저장소 클론 및 의존성 설치
git clone <repository-url>
cd 27th-conference-robo404
chmod +x setup_repos.sh
./setup_repos.sh

# 2. Docker 이미지 빌드
docker build -t my-ros-jazzy-dev .
```

### API 키 설정
```bash
# Vision API 키 설정 (필수)
# 파일 위치: ros/src/my_packages/vision_api/.env
echo "OPENAI_API_KEY=your_openai_key" > ros/src/my_packages/vision_api/.env
echo "GEMINI_API_KEY=your_gemini_key" >> ros/src/my_packages/vision_api/.env
echo "HUGGINGFACE_API_KEY=your_hf_key" >> ros/src/my_packages/vision_api/.env
```

### Docker 컨테이너 실행
```bash
# GPU 지원 컨테이너 실행 (권장)
xhost +local:root
docker run -it --rm \
  --name ros-dev \
  --gpus all \
  -e DISPLAY=$DISPLAY \
  -e QT_X11_NO_MITSHM=1 \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v $(pwd)/ros:/root/ros \
  -v $(pwd)/training:/root/training \
  my-ros-jazzy-dev
```

### 시스템 실행 순서

#### 1단계: Gazebo 시뮬레이션 시작
```bash
# 일반 환경
ros2 launch my_robot_bringup my_launch.py

# 위험 상황 테스트 환경
ros2 launch my_robot_bringup my_launch.py world_name:=room_chairfall_1.sdf
```

#### 2단계: 네비게이션 시스템 (새 터미널)
```bash
docker exec -it ros-dev bash
ros2 launch turtlebot3_navigation2 navigation2.launch.py \
  use_sim_time:=True \
  map:=/root/ros/src/my_packages/my_robot_bringup/maps/my_default_map.yaml
```

#### 3단계: YOLO 객체 탐지 (새 터미널)
```bash
docker exec -it ros-dev bash
ros2 launch yolo_bringup yolov8.launch.py \
  model:=/root/training/weights/train3/chair_state_v1_best.pt \
  device:=cuda:0 \
  input_image_topic:=/camera/image_raw \
  threshold:=0.5
```

#### 4단계: 카메라 트래킹 시스템 (새 터미널)
```bash
docker exec -it ros-dev bash
ros2 launch camera_tracker tracker.launch.py \
  kp_tilt:=0.0 \
  dead_zone:=500.0
```

#### 5단계: Vision API 분석 (새 터미널)
```bash
docker exec -it ros-dev bash

# OpenAI Vision API
ros2 launch vision_api analyzer.launch.py \
  api_provider:=openai \
  prompt:="이 의자의 상태를 확인하고, 위험한 상태인지 판단해. 답변은 구체적으로, 간결한 문체로 해"

# 또는 Gemini Vision API
ros2 launch vision_api analyzer.launch.py \
  api_provider:=gemini \
  prompt:="이 의자의 상태를 확인하고, 위험한 상태인지 판단해. 답변은 구체적으로, 간결한 문체로 해"
```

#### 6단계: 결과 모니터링
```bash
# 이미지 스트림 확인
ros2 run rqt_image_view rqt_image_view

# AI 분석 결과 확인
ros2 topic echo /vision_analysis_result
```

---

## 9. 프로젝트 구조 (Directory Structure)

```
27th-conference-robo404/
├── Dockerfile                     # Docker 이미지 정의
├── entrypoint.sh                  # 컨테이너 진입점 스크립트
├── setup_repos.sh                 # 외부 패키지 클론 스크립트
├── SIM.md                         # 실행 가이드 (간단 버전)
├── README.md                      # 본 문서
├── patrol.yaml                    # 순찰 설정 파일
│
├── ros/                           # ROS2 워크스페이스
│   ├── src/
│   │   ├── external/              # 외부 ROS 패키지
│   │   │   ├── turtlebot3_msgs/           # TurtleBot3 메시지 정의
│   │   │   ├── turtlebot3_simulations/    # TurtleBot3 시뮬레이션
│   │   │   └── yolo_ros/                  # YOLO ROS2 통합 패키지
│   │   │
│   │   └── my_packages/           # 커스텀 개발 패키지
│   │       ├── my_robot_bringup/          # 로봇 실행 및 시뮬레이션
│   │       │   ├── launch/                # 런치 파일
│   │       │   │   ├── my_launch.py               # 메인 시뮬레이션 런치
│   │       │   │   └── construction_site_launch.py
│   │       │   ├── maps/                  # SLAM 생성 맵 파일
│   │       │   │   ├── my_default_map.yaml/.pgm
│   │       │   │   └── my_map.yaml/.pgm
│   │       │   ├── models/                # 3D 가구 모델
│   │       │   │   ├── Chair/             # 의자 모델 (OBJ + 텍스처)
│   │       │   │   ├── Sofa/              # 소파 모델
│   │       │   │   ├── CoffeeTable/       # 커피테이블
│   │       │   │   └── Bookshelf/         # 책장
│   │       │   └── worlds/                # Gazebo 시뮬레이션 월드
│   │       │       ├── room_default.sdf           # 기본 안전 환경
│   │       │       ├── room_chairfall_1.sdf       # 의자 위험 상황 1
│   │       │       ├── room_chairfall_2.sdf       # 의자 위험 상황 2
│   │       │       └── room_chairfall_3.sdf       # 의자 위험 상황 3
│   │       │
│   │       ├── camera_tracker/            # 지능형 카메라 트래킹
│   │       │   ├── camera_tracker/
│   │       │   │   └── tracker_node.py           # PTZ 제어 노드
│   │       │   └── launch/
│   │       │       └── tracker.launch.py         # 트래킹 런치 파일
│   │       │
│   │       ├── vision_api/                # AI 비전 분석 시스템
│   │       │   ├── vision_api/
│   │       │   │   ├── analyzer_node.py          # 메인 분석 노드
│   │       │   │   └── api/
│   │       │   │       ├── openai_api.py         # OpenAI GPT-4V
│   │       │   │       ├── gemini_api.py         # Google Gemini Vision
│   │       │   │       └── huggingface_api.py    # HuggingFace API
│   │       │   ├── .env                          # API 키 설정 (사용자 생성)
│   │       │   └── requirements.txt              # Python 의존성
│   │       │
│   │       ├── room_surveyor/             # 자동 순찰 시스템
│   │       │   └── room_surveyor/
│   │       │       └── auto_survey_node.py       # 순찰 네비게이션
│   │       │
│   │       └── yolo_data_collector/       # 데이터 수집 도구
│   │           └── yolo_data_collector/
│   │               └── manual_collector_node.py  # 수동 데이터 수집
│   │
│   ├── build/                     # ROS2 빌드 결과물
│   ├── install/                   # ROS2 설치된 패키지
│   └── log/                       # 빌드 및 실행 로그
│
├── training/                      # YOLO 모델 훈련
│   ├── data/
│   │   └── dataset.yaml           # YOLO 데이터셋 설정
│   ├── weights/                   # 훈련된 모델 가중치
│   │   └── train3/
│   │       └── chair_state_v1_best.pt    # 최종 가구 상태 탐지 모델
│   ├── train.py                   # 모델 훈련 스크립트
│   ├── auto_labeler.py            # 자동 라벨링 도구
│   └── split_data.py              # 데이터 분할 유틸리티
│
└── runs/                          # YOLO 추론 결과
    └── detect/                    # 탐지 결과 이미지 저장
        ├── predict/
        └── predict2/
```

---

## 10. ROS2 인터페이스 (ROS2 Interface)

### 주요 토픽 (Topics)

| 토픽명 | 타입 | 방향 | 설명 |
|--------|------|------|------|
| `/camera/image_raw` | `sensor_msgs/Image` | Pub | Gazebo 카메라 원본 영상 |
| `/yolo/detections` | `yolo_msgs/Detections` | Pub | YOLO 객체 탐지 결과 |
| `/camera/pan_cmd` | `std_msgs/Float64` | Pub | 카메라 Pan 제어 명령 |
| `/camera/tilt_cmd` | `std_msgs/Float64` | Pub | 카메라 Tilt 제어 명령 |
| `/camera/stable` | `std_msgs/Bool` | Pub | 카메라 안정화 상태 |
| `/vision/analysis_result` | `std_msgs/String` | Pub | AI 비전 분석 결과 |
| `/scan` | `sensor_msgs/LaserScan` | Pub | LIDAR 스캔 데이터 |
| `/odom` | `nav_msgs/Odometry` | Pub | 로봇 오도메트리 |
| `/cmd_vel` | `geometry_msgs/Twist` | Sub | 로봇 속도 명령 |

#### 토픽 상세 설명

**`/camera/image_raw`**
- Gazebo 시뮬레이션의 TurtleBot3 카메라에서 발행되는 RGB 이미지 스트림
- 해상도: 640x480, 30 FPS
- YOLO 객체 탐지 및 Vision API 분석의 입력 소스로 사용

**`/yolo/detections`**
- YOLOv8 모델이 탐지한 객체 정보 (바운딩 박스, 클래스, 신뢰도)
- 탐지 클래스: chair, sofa, table, red_ball
- Camera Tracker가 구독하여 추적 대상 선정에 활용

**`/camera/pan_cmd` / `/camera/tilt_cmd`**
- 카메라 짐벌의 Pan(좌우)/Tilt(상하) 각도 제어 명령
- 단위: radian, 범위: Pan ±1.5rad, Tilt ±0.5rad
- 비례제어 알고리즘으로 탐지된 객체를 화면 중앙에 유지

**`/camera/stable`**
- 카메라가 객체를 안정적으로 추적 중인지 나타내는 플래그
- `True`: 객체가 데드존 내에 위치 (Vision API 분석 트리거)
- `False`: 객체 추적 중 또는 미탐지 상태

**`/vision/analysis_result`**
- AI Vision API(OpenAI/Gemini/HuggingFace)의 안전성 분석 결과 텍스트
- 카메라 안정화 시 자동으로 분석 실행 후 발행
- 위험 상태 판단 및 상세 설명 포함

**`/scan`**
- TurtleBot3의 360° LIDAR 센서 데이터
- Nav2 네비게이션 스택에서 장애물 회피 및 SLAM에 활용
- 범위: 0.12m ~ 3.5m

**`/odom`**
- 로봇의 위치(x, y, z) 및 방향(quaternion) 정보
- 엔코더 기반 추정값, Nav2 위치 추정의 초기값으로 사용

**`/cmd_vel`**
- 로봇 이동 속도 명령 (linear.x, angular.z)
- Nav2 또는 텔레옵에서 발행, TurtleBot3 컨트롤러가 구독

### 주요 파라미터 (Parameters)

#### Camera Tracker
| 파라미터 | 기본값 | 설명 |
|----------|--------|------|
| `kp_pan` | 0.001 | Pan 비례제어 게인 |
| `kp_tilt` | 0.0 | Tilt 비례제어 게인 |
| `dead_zone` | 500.0 | 안정화 판단 데드존 (픽셀) |
| `pan_limit` | 1.5 | Pan 각도 제한 (rad) |
| `tilt_limit` | 0.5 | Tilt 각도 제한 (rad) |

#### Vision API
| 파라미터 | 기본값 | 설명 |
|----------|--------|------|
| `api_provider` | `openai` | API 제공자 (openai/gemini/huggingface) |
| `prompt` | - | AI 분석 프롬프트 |
| `cooldown` | 10.0 | API 호출 쿨다운 (초) |

#### YOLO Detection
| 파라미터 | 기본값 | 설명 |
|----------|--------|------|
| `model` | - | YOLO 모델 경로 (.pt) |
| `device` | `cuda:0` | 추론 디바이스 |
| `threshold` | 0.5 | 신뢰도 임계값 |
| `input_image_topic` | `/camera/image_raw` | 입력 이미지 토픽 |

### 데이터 흐름 (Data Flow)

```
/camera/image_raw ──→ [YOLO Node] ──→ /yolo/detections
                                            │
                                            ▼
                                    [Camera Tracker]
                                            │
                        ┌───────────────────┼───────────────────┐
                        ▼                   ▼                   ▼
                /camera/pan_cmd     /camera/tilt_cmd     /camera/stable
                                                                │
                                                                ▼
                                                        [Vision API Node]
                                                                │
                                                                ▼
                                                    /vision/analysis_result
```

---

## 11. 한계점 및 향후 계획 (Limitations & Future Work)

### 현재 한계점
- **시뮬레이션 환경**: 실제 물리 환경과의 차이로 인한 제약
- **제한된 객체 클래스**: 의자, 소파 등 특정 가구에 국한됨
- **네트워크 의존성**: AI Vision API 사용으로 인한 인터넷 연결 필수
- **단일 로봇 운용**: 다중 로봇 협업 시스템 미지원

### 향후 개선 방향

#### 기술적 개선
1. **실제 하드웨어 포팅**: TurtleBot3 실기체 적용
2. **온디바이스 AI**: Edge AI를 활용한 오프라인 분석 기능
3. **다중 센서 융합**: RGB-D, LIDAR, IMU 통합 인식
4. **객체 클래스 확장**: 더 다양한 위험 요소 탐지

#### 시스템 확장
1. **다중 로봇 협업**: 분산 순찰 및 정보 공유
2. **실시간 알림 시스템**: 위험 상황 발생 시 즉시 알림
3. **웹 대시보드**: 실시간 모니터링 및 제어 인터페이스
4. **데이터 분석**: 장기간 안전성 트렌드 분석

#### 응용 분야 확장
- 고령자 시설 안전 모니터링
- 산업 현장 위험 요소 탐지
- 공공시설 예방적 안전 관리

---

## 12. 팀 구성 및 역할 (Team ROBO 404)

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
      <td><strong>정지윤</strong></td>
      <td><strong>김정인</strong></td>
      <td><strong>이재영</strong></td>
      <td><strong>이준찬</strong></td>
      <td><strong>이하람</strong></td>
    </tr>
    <tr>
      <td>Vision API 통합<br/>AI 분석 시스템</td>
      <td>YOLO 모델 훈련<br/>객체 탐지 시스템</td>
      <td>카메라 트래킹<br/>제어 시스템</td>
      <td>시뮬레이션 환경<br/>시스템 통합</td>
      <td>네비게이션<br/>자율 순찰</td>
    </tr>
  </table>
</div>
