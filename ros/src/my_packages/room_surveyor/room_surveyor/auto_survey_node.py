import os
import json
from datetime import datetime

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from nav_msgs.msg import Odometry
from cv_bridge import CvBridge
import cv2


class AutoSurveyNode(Node):
    def __init__(self):
        super().__init__('auto_survey_node')
        self.get_logger().info('촬영·위치 기록 모듈이 시작되었습니다.')

        self.save_dir = 'survey_captures'
        os.makedirs(self.save_dir, exist_ok=True)
        self.json_path = os.path.join(self.save_dir, 'survey_log.json')
        self.logs = []

        self.bridge = CvBridge()
        self.latest_image = None
        self.latest_pose = None
        self.image_count = 0
        self.capture_limit = 100

        self.create_subscription(Image, '/camera/image_raw', self.image_callback, 10)
        self.create_subscription(Odometry, '/odom', self.odom_callback, 10)

        self.create_timer(2.0, self.capture_callback)

    def image_callback(self, msg):
        try:
            self.latest_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        except Exception as e:
            self.get_logger().error(f'CvBridge 변환 실패: {e}')

    def odom_callback(self, msg):
        self.latest_pose = msg.pose.pose

    def capture_callback(self):
        if self.latest_image is None or self.latest_pose is None:
            self.get_logger().warn('센서 데이터 대기 중 — 아직 촬영 불가')
            return

        if self.image_count >= self.capture_limit:
            self.finish_and_shutdown()
            return

        filename = os.path.join(self.save_dir, f'img_{self.image_count:04d}.jpg')
        cv2.imwrite(filename, self.latest_image)

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        pos = self.latest_pose.position

        self.logs.append({
            "timestamp": timestamp,
            "filename": filename,
            "pose": {"x": pos.x, "y": pos.y, "z": pos.z}
        })

        with open(self.json_path, 'w') as f:
            json.dump(self.logs, f, indent=4)

        self.get_logger().info(f'촬영 {self.image_count + 1}/{self.capture_limit} → {filename}')
        self.image_count += 1

    def finish_and_shutdown(self):
        self.get_logger().info(
            f'📌 총 {self.image_count}장 촬영 완료 — JSON 로그 저장 완료\n'
            f'📌 노드를 종료합니다.'
        )
        self.destroy_node()
        rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)
    node = AutoSurveyNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if rclpy.ok():
            node.destroy_node()
            rclpy.shutdown()


if __name__ == '__main__':
    main()
