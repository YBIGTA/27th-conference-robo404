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

# YOLO 객체 탐지
ros2 launch yolo_bringup yolov8.launch.py model:=yolov8n input_image_topic:=/camera/image_raw

# 카메라 추적
ros2 launch camera_tracker tracker.launch.py

# 비전 분석
ros2 launch vision_api analyzer.launch.py api_provider:=openai
```

## Git 워크플로우
- 작업 완료 시 복사해서 바로 실행할 수 있는 git 명령어 전체를 출력
- 형식: `git add <파일들> && git commit -m "커밋메시지"`
- conventional commits 형식 사용 (feat:, fix:, docs: 등)
- 커밋 메시지는 한국어로 작성
- 커밋은 직접 실행하지 말 것
