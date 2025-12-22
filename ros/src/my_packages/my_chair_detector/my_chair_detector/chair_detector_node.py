import rclpy
from rclpy.node import Node
# [변경 1] 메시지 타입 임포트 변경 (vision_msgs -> yolo_msgs)
from yolo_msgs.msg import DetectionArray

class ChairDetectorNode(Node):
    def __init__(self):
        super().__init__('chair_detector_node')
        # [변경 2] 구독할 토픽 이름 변경 ('/yolo/detections' -> '/detections')
        # [변경 3] 메시지 타입 변경 (Detection2DArray -> DetectionArray)
        self.subscription = self.create_subscription(
            DetectionArray,
            '/detections',
            self.detection_callback,
            10)
        self.get_logger().info('Chair Detector Node has been started and is listening to /detections')

        # 클래스 ID 정의 (학습 때 설정한 것과 일치해야 함)
        self.CLASS_ID_UPRIGHT = 0
        self.CLASS_ID_FALLEN = 1

    def detection_callback(self, msg):
        detect_count = 0
        # [변경 4] yolo_msgs 구조에 맞게 데이터 파싱 방법 변경
        # (보통 yolo_msgs는 구조가 더 간단해서 바로 접근 가능합니다)
        for detection in msg.detections:
            # class_id와 score에 접근하는 방식이 다릅니다.
            # (패키지마다 조금 다를 수 있지만, 보통 아래와 같습니다.)
            class_id = int(detection.class_id)
            score = detection.score

            if score < 0.5: # 신뢰도가 낮으면 무시
                continue

            detect_count += 1
            if class_id == self.CLASS_ID_UPRIGHT:
                self.get_logger().info(f'[정상] 의자가 똑바로 서 있습니다. (신뢰도: {score:.2f})')
            elif class_id == self.CLASS_ID_FALLEN:
                self.get_logger().warn(f'[경고!] 의자가 넘어져 있습니다. (신뢰도: {score:.2f})')
        
        # (너무 자주 떠서 시끄러우면 이 부분은 주석 처리해도 됩니다)
        if detect_count == 0:
            self.get_logger().debug('감지된 의자가 없습니다.')

def main(args=None):
    rclpy.init(args=args)
    node = ChairDetectorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()