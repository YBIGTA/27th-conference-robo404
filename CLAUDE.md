# 위험 탐지 AI 로봇 프로젝트 (ROBO 404)

ROS 2 기반 YOLO 객체 탐지 + 카메라 추적 + AI 비전 분석 통합 로봇 시스템

## 기술 스택
- **ROS 2 Jazzy** + **Gazebo** (시뮬레이션)
- **TurtleBot3 Waffle** (로봇 플랫폼)
- **YOLO v8** (객체 탐지, Ultralytics)
- **Vision APIs**: OpenAI GPT-4o, Google Gemini, Huggingface VLM

## 프로젝트 구조
```
ros/src/
├── external/               # 외부 패키지
│   ├── turtlebot3_msgs/    # TurtleBot3 메시지 정의
│   ├── turtlebot3_simulations/  # Gazebo 시뮬레이션
│   └── yolo_ros/           # YOLO ROS 통합
└── my_packages/            # 커스텀 패키지
    ├── camera_tracker/     # 카메라 팬/틸트 추적 노드
    ├── vision_api/         # 멀티 프로바이더 비전 분석 API
    └── my_robot_bringup/   # 로봇 통합 실행 (런치, 월드, 모델)

training/                   # YOLO 학습 관련
├── train.py               # 학습 스크립트
├── split_data.py          # 데이터 분할
└── data/                  # 이미지/라벨 데이터셋
```

## 주요 ROS 노드

### camera_tracker
- **입력**: `/yolo/detections`
- **출력**: `/camera/pan_cmd`, `/camera/tilt_cmd`, `/camera/stable`
- YOLO 탐지 결과를 기반으로 카메라 팬/틸트 제어

### vision_api
- **입력**: `/camera/image_raw`, `/camera/stable`
- **출력**: `/vision/analysis_result`
- 카메라 안정화 시 AI API로 이미지 분석 (OpenAI/Gemini/Huggingface)

## 빌드 및 실행
```bash
# 빌드 (ros/ 디렉토리에서)
colcon build --symlink-install

# Gazebo 시뮬레이터 + 로봇 실행
ros2 launch my_robot_bringup my_launch.py

# YOLO 객체 탐지 (기본 모델)
ros2 launch yolo_bringup yolov8.launch.py model:=yolov8n input_image_topic:=/camera/image_raw

# YOLO 객체 탐지 (커스텀 모델 - chair_state_v1)
# Docker 환경에서 실행
ros2 launch yolo_bringup yolov8.launch.py \
  model:=/root/training/weights/train3/weights/chair_state_v1_best.pt \
  input_image_topic:=/camera/image_raw

# 호스트 환경에서 실행 시
ros2 launch yolo_bringup yolov8.launch.py \
  model:=/home/junchan/github/27th-conference-robo404/training/weights/train3/weights/chair_state_v1_best.pt \
  input_image_topic:=/camera/image_raw

# 카메라 추적
ros2 launch camera_tracker tracker.launch.py

# 비전 분석 (기본 프롬프트)
ros2 launch vision_api analyzer.launch.py api_provider:=openai

# 비전 분석 (커스텀 프롬프트)
ros2 launch vision_api analyzer.launch.py \
  api_provider:=openai \
  prompt:="이 이미지에서 위험한 상황을 탐지하고 상세히 설명해주세요."

# 비전 분석 (다른 API 프로바이더)
ros2 launch vision_api analyzer.launch.py api_provider:=gemini
ros2 launch vision_api analyzer.launch.py api_provider:=huggingface
```

## 커스텀 YOLO 모델

### chair_state_v1 모델
- **위치**: `training/weights/train3/weights/chair_state_v1_best.pt`
- **용도**: 의자 상태 탐지 (정상/전도 등)
- **학습**: YOLOv8 기반 커스텀 학습 모델

### Docker 환경 경로 차이
프로젝트가 Docker 컨테이너에서 실행될 때 경로 매핑에 유의:
- **호스트 경로**: `/home/junchan/github/27th-conference-robo404/training/weights/train3/weights/chair_state_v1_best.pt`
- **Docker 내부 경로**: `/root/training/weights/train3/weights/chair_state_v1_best.pt`

ROS 명령어 실행 시 현재 환경에 맞는 경로를 사용해야 함.

## Vision API 사용법

### API 프로바이더
- `openai`: OpenAI GPT-4o Vision
- `gemini`: Google Gemini Vision
- `huggingface`: Huggingface VLM

### 프롬프트 커스터마이징
`prompt` 인자로 분석 지시사항 지정 가능:
```bash
ros2 launch vision_api analyzer.launch.py \
  api_provider:=openai \
  prompt:="이미지 속 안전 위험 요소를 찾아 한국어로 설명하세요."
```

## Git 워크플로우
- 작업 완료 시 복사해서 바로 실행할 수 있는 git 명령어 전체를 출력
- 형식: `git add <파일들> && git commit -m "커밋메시지"`
- conventional commits 형식 사용 (feat:, fix:, docs: 등)
- 커밋 메시지는 한국어로 작성
- 커밋은 직접 실행하지 말 것
