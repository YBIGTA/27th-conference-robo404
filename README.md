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


## 📦 1. Docker 이미지 빌드

```bash
docker build -t my-ros-jazzy-dev .
```

---

## 🚀 2. 컨테이너 실행

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

## 📂 3. ROS 패키지 구조 (필수)

```
ros/
 └── src/
      ├── turtlebot3_msgs
      ├── turtlebot3_simulations
      └── yolo_ros
```

---

## ▶️ 4. 실행 순서

### 1. Gazebo 시뮬레이터

```bash
docker exec -it ros-dev bash
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py
```

### 2. Nav2

```bash
docker exec -it ros-dev bash
ros2 launch turtlebot3_navigation2 navigation2.launch.py use_sim_time:=True
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

