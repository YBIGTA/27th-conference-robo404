import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    # 1. 모델 파일 경로 동적 생성
    # 현재 패키지(my_chair_detector)의 설치 경로를 찾고, 그 안의 weights/best.pt 경로를 완성합니다.
    pkg_share = get_package_share_directory('my_chair_detector')
    model_path = os.path.join(pkg_share, 'weights', 'best.pt')

    # 2. YOLO 노드 실행 설정 (external/yolo_ros 패키지 활용)
    # 패키지 이름, 실행 파일 이름, 모델 경로 파라미터 이름은 실제 yolo_ros 패키지에 맞춰 수정해야 합니다.
    yolo_node = Node(
        package='yolo_ros',           # 사용하려는 YOLO 패키지 이름
        executable='yolo_node',       # 실행할 노드 실행 파일 이름
        name='yolo_node',
        parameters=[{
            'model_path': model_path, # [핵심] 우리가 만든 모델 파일의 경로를 전달
            'device': 'cpu',       # GPU 사용 시 설정 (CPU는 'cpu')
            'conf': 0.5               # 신뢰도 임계값
        }],
        remappings=[
            ('/image_raw', '/camera/image_raw')
        ]
    )

    # 3. 커스텀 의자 탐지 노드 실행 설정
    chair_detector_node = Node(
        package='my_chair_detector',
        executable='chair_detector_node',
        name='chair_detector',
        output='screen'
    )

    return LaunchDescription([
        yolo_node,
        chair_detector_node
    ])