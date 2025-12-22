# gz_label_world_v4

Gazebo 시뮬레이션에서 라벨이 붙은 박스 3개를 표시하는 월드입니다.

## 파일 구조

```
gz_label_world_v4/
├── set_labels.py           # 라벨 텍스처 생성 스크립트
├── launch_labeled_world.py # ROS2 launch 파일
├── models/
│   ├── labeled_box_a/      # 박스 A 모델
│   ├── labeled_box_b/      # 박스 B 모델
│   ├── labeled_box_c/      # 박스 C 모델
│   └── labeled_floor/      # 바닥 모델
└── worlds/
    └── labeled_world.sdf   # 월드 파일
```

## 사용법

### 1. 라벨 생성

```bash
cd ~/27th-conference-robo404/gz_label_world_v4
python3 set_labels.py <라벨1> <라벨2> <라벨3>
```

예시:
```bash
python3 set_labels.py A B C
python3 set_labels.py EXIT ENTER STOP
python3 set_labels.py 1 2 3
```

### 2. Gazebo 실행

```bash
GZ_SIM_RESOURCE_PATH=$PWD/models gz sim worlds/labeled_world.sdf
```

### 3. ROS2 Launch로 실행 (선택)

```bash
python3 launch_labeled_world.py
```

## 의존성

- Gazebo (gz sim)
- Python 3
- Pillow (`pip install pillow`)
