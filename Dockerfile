# 1. ROS2 Jazzy + Desktop (RViz, Gazebo 포함)
FROM osrf/ros:jazzy-desktop

# 2. 기본 툴 + Nav2 + TurtleBot3 패키지
RUN apt-get update && apt-get install -y \
    git \
    python3-pip \
    python3-venv \
    python3-virtualenv \
    build-essential \
    ros-jazzy-nav2* \
    ros-jazzy-turtlebot3* \
    ros-jazzy-rqt-image-view \
    && rm -rf /var/lib/apt/lists/*

# 3. yolo_ros의 requirements.txt 를 이미지 안으로 복사
#    => 로컬 ./ros/src/yolo_ros/requirements.txt 가 있어야 함
#    => 없으면 먼저 ./setup_repos.sh 를 실행하세요
COPY ./ros/src/external/yolo_ros/requirements.txt /tmp/yolo_requirements.txt

# 4. YOLO 전용 venv 생성 + requirements 설치
#    venv는 /opt/yolo_venv 에 둬서 워크스페이스(ros)와 분리
RUN python3 -m virtualenv -p python3 /opt/yolo_venv && \
    . /opt/yolo_venv/bin/activate && \
    pip install --upgrade pip && \
    pip install "setuptools<75" && \
    pip install -r /tmp/yolo_requirements.txt && \
    deactivate

# 5. bashrc에 ROS/워크스페이스/YOLO 환경 자동 로드 설정
RUN echo 'if [ -f /opt/ros/jazzy/setup.bash ]; then source /opt/ros/jazzy/setup.bash; fi' >> /root/.bashrc && \
    echo 'if [ -f /root/ros/install/setup.bash ]; then source /root/ros/install/setup.bash; fi' >> /root/.bashrc && \
    echo 'export PYTHONPATH="/opt/yolo_venv/lib/python3.12/site-packages:$PYTHONPATH"' >> /root/.bashrc && \
    echo 'export TURTLEBOT3_MODEL=waffle' >> /root/.bashrc

# 6. 작업 디렉토리를 /root/ros 로 변경
WORKDIR /root/ros

# 7. entrypoint.sh 복사 후 실행 가능하게
COPY ./entrypoint.sh /root/entrypoint.sh
RUN chmod +x /root/entrypoint.sh

# 8. 컨테이너 시작 시 entrypoint.sh 실행
ENTRYPOINT ["/root/entrypoint.sh"]

# 9. entrypoint.sh 에 인자로 전달할 기본 커맨드 = bash
CMD ["bash"]
