#!/usr/bin/env python3
# 필요한 라이브러리들을 가져옵니다.
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError
import cv2
import os
from datetime import datetime

class ManualImageSaverNode(Node):
    def __init__(self):
        super().__init__('manual_image_saver_node')

        # 저장할 폴더 경로 (기본값: 홈 디렉토리 밑에 yolo_data/manual)
        default_save_dir = os.path.join(os.path.expanduser('~'), 'yolo_data', 'manual')
        self.declare_parameter('save_dir', default_save_dir)
        self.save_dir = self.get_parameter('save_dir').value

        # 구독할 카메라 토픽
        self.declare_parameter('image_topic', '/camera/image_raw')
        image_topic = self.get_parameter('image_topic').value
        # ---------------------

        # 저장 폴더
        os.makedirs(self.save_dir, exist_ok=True)
        self.get_logger().info(f"이미지 저장 경로: {self.save_dir}")

        # CvBridge 인스턴스 생성
        self.bridge = CvBridge()

        # Subscriber 생성
        self.subscription = self.create_subscription(
            Image,
            image_topic,
            self.image_callback,
            10)
        
        self.get_logger().info(f"'{image_topic}' 구독 시작. OpenCV 창을 클릭하고 's'를 눌러 저장하세요. 'q'로 종료합니다.")
        self.window_name = "Camera View - Press 's' to save, 'q' to quit"

    def image_callback(self, msg):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        except CvBridgeError as e:
            self.get_logger().error(f'CvBridge 변환 실패: {e}')
            return

        
        cv2.imshow(self.window_name, cv_image)

        # 키보드 입력 대기
        key = cv2.waitKey(1) & 0xFF

        # 's' 키가 눌렸으면 이미지 저장
        if key == ord('s'):
            # 파일명 생성
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename = os.path.join(self.save_dir, f"manual_{timestamp}.jpg")
            
            # 이미지 저장
            cv2.imwrite(filename, cv_image)
            self.get_logger().info(f'이미지 저장됨: {filename}')
        
        # 'q' 키가 눌렸으면 노드 종료
        elif key == ord('q'):
            self.get_logger().info('종료 키(q) 입력됨. 노드를 종료합니다.')
            rclpy.shutdown()

    def destroy_node(self):
        cv2.destroyAllWindows()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = ManualImageSaverNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except ExternalShutdownException:
        pass
    finally:
        if rclpy.ok():
            node.destroy_node()
            rclpy.shutdown()

if __name__ == '__main__':
    main()