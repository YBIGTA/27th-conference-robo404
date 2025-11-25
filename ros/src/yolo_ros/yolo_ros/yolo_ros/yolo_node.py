#!/usr/bin/env python3
# Copyright (C) 2023 Miguel Ángel González Santamarta
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from typing import List, Dict, Tuple, Optional
from collections import deque
import time

from cv_bridge import CvBridge

import rclpy
from rclpy.qos import QoSProfile
from rclpy.qos import QoSHistoryPolicy
from rclpy.qos import QoSDurabilityPolicy
from rclpy.qos import QoSReliabilityPolicy
from rclpy.lifecycle import LifecycleNode
from rclpy.lifecycle import TransitionCallbackReturn
from rclpy.lifecycle import LifecycleState

import torch
from ultralytics import YOLO, YOLOWorld, YOLOE
from ultralytics.engine.results import Results
from ultralytics.engine.results import Boxes
from ultralytics.engine.results import Masks
from ultralytics.engine.results import Keypoints

from std_srvs.srv import SetBool
from sensor_msgs.msg import Image
from yolo_msgs.msg import Point2D
from yolo_msgs.msg import BoundingBox2D
from yolo_msgs.msg import Mask
from yolo_msgs.msg import KeyPoint2D
from yolo_msgs.msg import KeyPoint2DArray
from yolo_msgs.msg import Detection
from yolo_msgs.msg import DetectionArray
from yolo_msgs.srv import SetClasses


class YoloNode(LifecycleNode):

    def __init__(self) -> None:
        super().__init__("yolo_node")

        # -------------------------
        # 기본 params (원본 그대로)
        # -------------------------
        self.declare_parameter("model_type", "YOLO")
        self.declare_parameter("model", "yolov8m.pt")
        self.declare_parameter("device", "cuda:0")
        self.declare_parameter("yolo_encoding", "bgr8")
        self.declare_parameter("enable", True)
        self.declare_parameter("image_reliability", QoSReliabilityPolicy.BEST_EFFORT)

        self.declare_parameter("threshold", 0.5)
        self.declare_parameter("iou", 0.5)
        self.declare_parameter("imgsz_height", 640)
        self.declare_parameter("imgsz_width", 640)
        self.declare_parameter("half", False)
        self.declare_parameter("max_det", 300)
        self.declare_parameter("augment", False)
        self.declare_parameter("agnostic_nms", False)
        self.declare_parameter("retina_masks", False)

        # -------------------------
        # 디버그용 추가 params
        # -------------------------
        # latency 로깅 on/off + 몇 프레임마다 평균 찍을지
        self.declare_parameter("debug_timing", True)
        self.declare_parameter("debug_interval", 30)

        self.type_to_model = {"YOLO": YOLO, "World": YOLOWorld, "YOLOE": YOLOE}

        # 디버그용 상태 변수는 on_configure에서 초기화

    def on_configure(self, state: LifecycleState) -> TransitionCallbackReturn:
        self.get_logger().info(f"[{self.get_name()}] Configuring...")

        # model params
        self.model_type = (
            self.get_parameter("model_type").get_parameter_value().string_value
        )
        self.model = self.get_parameter("model").get_parameter_value().string_value
        self.device = self.get_parameter("device").get_parameter_value().string_value
        self.yolo_encoding = (
            self.get_parameter("yolo_encoding").get_parameter_value().string_value
        )

        # inference params
        self.threshold = (
            self.get_parameter("threshold").get_parameter_value().double_value
        )
        self.iou = self.get_parameter("iou").get_parameter_value().double_value
        self.imgsz_height = (
            self.get_parameter("imgsz_height").get_parameter_value().integer_value
        )
        self.imgsz_width = (
            self.get_parameter("imgsz_width").get_parameter_value().integer_value
        )
        self.half = self.get_parameter("half").get_parameter_value().bool_value
        self.max_det = self.get_parameter("max_det").get_parameter_value().integer_value
        self.augment = self.get_parameter("augment").get_parameter_value().bool_value
        self.agnostic_nms = (
            self.get_parameter("agnostic_nms").get_parameter_value().bool_value
        )
        self.retina_masks = (
            self.get_parameter("retina_masks").get_parameter_value().bool_value
        )

        # ros params
        self.enable = self.get_parameter("enable").get_parameter_value().bool_value
        self.reliability = (
            self.get_parameter("image_reliability").get_parameter_value().integer_value
        )

        # debug params
        self.debug_timing = (
            self.get_parameter("debug_timing").get_parameter_value().bool_value
        )
        self.debug_interval = (
            self.get_parameter("debug_interval").get_parameter_value().integer_value
        )

        # detection pub QoS
        self.image_qos_profile = QoSProfile(
            reliability=self.reliability,
            history=QoSHistoryPolicy.KEEP_LAST,
            durability=QoSDurabilityPolicy.VOLATILE,
            depth=1,
        )

        self._pub = self.create_lifecycle_publisher(DetectionArray, "detections", 10)
        self.cv_bridge = CvBridge()

        # -------------------------
        # 디버그용 타이밍 버퍼 초기화
        # -------------------------
        # (cv, infer, post, total) ms 값 저장
        self._timing_buffer: deque[Tuple[float, float, float, float]] = deque(
            maxlen=200
        )
        self._frame_count: int = 0
        self._last_wall_time: Optional[float] = None

        self.get_logger().info(
            f"[{self.get_name()}] Debug timing: {self.debug_timing}, "
            f"interval: {self.debug_interval}"
        )

        super().on_configure(state)
        self.get_logger().info(f"[{self.get_name()}] Configured")

        return TransitionCallbackReturn.SUCCESS

    def on_activate(self, state: LifecycleState) -> TransitionCallbackReturn:
        self.get_logger().info(f"[{self.get_name()}] Activating...")

        # 모델 로딩
        try:
            self.yolo = self.type_to_model[self.model_type](self.model)
        except FileNotFoundError:
            self.get_logger().error(f"Model file '{self.model}' does not exists")
            return TransitionCallbackReturn.ERROR

        # YOLOE does not support fusing
        if isinstance(self.yolo, YOLO) or isinstance(self.yolo, YOLOWorld):
            try:
                self.get_logger().info("Trying to fuse model...")
                self.yolo.fuse()
            except TypeError as e:
                self.get_logger().warn(f"Error while fuse: {e}")

        self._enable_srv = self.create_service(SetBool, "enable", self.enable_cb)

        if isinstance(self.yolo, YOLOWorld):
            self._set_classes_srv = self.create_service(
                SetClasses, "set_classes", self.set_classes_cb
            )

        self._sub = self.create_subscription(
            Image, "image_raw", self.image_cb, self.image_qos_profile
        )

        super().on_activate(state)
        self.get_logger().info(f"[{self.get_name()}] Activated")

        return TransitionCallbackReturn.SUCCESS

    def on_deactivate(self, state: LifecycleState) -> TransitionCallbackReturn:
        self.get_logger().info(f"[{self.get_name()}] Deactivating...")

        del self.yolo
        if "cuda" in self.device:
            self.get_logger().info("Clearing CUDA cache")
            torch.cuda.empty_cache()

        self.destroy_service(self._enable_srv)
        self._enable_srv = None

        if isinstance(self.yolo, YOLOWorld):
            self.destroy_service(self._set_classes_srv)
            self._set_classes_srv = None

        self.destroy_subscription(self._sub)
        self._sub = None

        super().on_deactivate(state)
        self.get_logger().info(f"[{self.get_name()}] Deactivated")

        return TransitionCallbackReturn.SUCCESS

    def on_cleanup(self, state: LifecycleState) -> TransitionCallbackReturn:
        self.get_logger().info(f"[{self.get_name()}] Cleaning up...")

        self.destroy_publisher(self._pub)

        del self.image_qos_profile

        super().on_cleanup(state)
        self.get_logger().info(f"[{self.get_name()}] Cleaned up")

        return TransitionCallbackReturn.SUCCESS

    def on_shutdown(self, state: LifecycleState) -> TransitionCallbackReturn:
        self.get_logger().info(f"[{self.get_name()}] Shutting down...")
        super().on_cleanup(state)
        self.get_logger().info(f"[{self.get_name()}] Shutted down")
        return TransitionCallbackReturn.SUCCESS

    def enable_cb(
        self,
        request: SetBool.Request,
        response: SetBool.Response,
    ) -> SetBool.Response:
        self.enable = request.data
        response.success = True
        return response

    def parse_hypothesis(self, results: Results) -> List[Dict]:

        hypothesis_list = []

        if results.boxes:
            box_data: Boxes
            for box_data in results.boxes:
                hypothesis = {
                    "class_id": int(box_data.cls),
                    "class_name": self.yolo.names[int(box_data.cls)],
                    "score": float(box_data.conf),
                }
                hypothesis_list.append(hypothesis)

        elif results.obb:
            for i in range(results.obb.cls.shape[0]):
                hypothesis = {
                    "class_id": int(results.obb.cls[i]),
                    "class_name": self.yolo.names[int(results.obb.cls[i])],
                    "score": float(results.obb.conf[i]),
                }
                hypothesis_list.append(hypothesis)

        return hypothesis_list

    def parse_boxes(self, results: Results) -> List[BoundingBox2D]:

        boxes_list = []

        if results.boxes:
            box_data: Boxes
            for box_data in results.boxes:

                msg = BoundingBox2D()

                # get boxes values
                box = box_data.xywh[0]
                msg.center.position.x = float(box[0])
                msg.center.position.y = float(box[1])
                msg.size.x = float(box[2])
                msg.size.y = float(box[3])

                # append msg
                boxes_list.append(msg)

        elif results.obb:
            for i in range(results.obb.cls.shape[0]):
                msg = BoundingBox2D()

                # get boxes values
                box = results.obb.xywhr[i]
                msg.center.position.x = float(box[0])
                msg.center.position.y = float(box[1])
                msg.center.theta = float(box[4])
                msg.size.x = float(box[2])
                msg.size.y = float(box[3])

                # append msg
                boxes_list.append(msg)

        return boxes_list

    def parse_masks(self, results: Results) -> List[Mask]:

        masks_list = []

        def create_point2d(x: float, y: float) -> Point2D:
            p = Point2D()
            p.x = x
            p.y = y
            return p

        mask: Masks
        for mask in results.masks:

            msg = Mask()

            msg.data = [
                create_point2d(float(ele[0]), float(ele[1]))
                for ele in mask.xy[0].tolist()
            ]
            msg.height = results.orig_img.shape[0]
            msg.width = results.orig_img.shape[1]

            masks_list.append(msg)

        return masks_list

    def parse_keypoints(self, results: Results) -> List[KeyPoint2DArray]:

        keypoints_list = []

        points: Keypoints
        for points in results.keypoints:

            msg_array = KeyPoint2DArray()

            if points.conf is None:
                continue

            for kp_id, (p, conf) in enumerate(zip(points.xy[0], points.conf[0])):

                if conf >= self.threshold:
                    msg = KeyPoint2D()

                    msg.id = kp_id + 1
                    msg.point.x = float(p[0])
                    msg.point.y = float(p[1])
                    msg.score = float(conf)

                    msg_array.data.append(msg)

            keypoints_list.append(msg_array)

        return keypoints_list

    def image_cb(self, msg: Image) -> None:
        """
        메인 이미지 콜백.
        원래 로직은 그대로 두고, 그 위/아래로 latency 측정 코드만 추가.
        """

        if not self.enable:
            return

        # -----------------------------
        # 0) 프레임 시작 시간 기록
        # -----------------------------
        t0 = time.time()
        self._frame_count += 1

        # -----------------------------
        # 1) cv_bridge 변환 (ROS Image -> OpenCV)
        # -----------------------------
        t_cv0 = time.time()
        try:
            cv_image = self.cv_bridge.imgmsg_to_cv2(
                msg, desired_encoding=self.yolo_encoding
            )
        except Exception as e:
            self.get_logger().error(f"cv_bridge conversion failed: {e}")
            return
        t_cv1 = time.time()
        cv_time = (t_cv1 - t_cv0) * 1000.0  # ms

        # -----------------------------
        # 2) YOLO 추론 (self.yolo.predict)
        # -----------------------------
        t_infer0 = time.time()
        results = self.yolo.predict(
            source=cv_image,
            verbose=False,
            stream=False,
            conf=self.threshold,
            iou=self.iou,
            imgsz=(self.imgsz_height, self.imgsz_width),
            half=self.half,
            max_det=self.max_det,
            augment=self.augment,
            agnostic_nms=self.agnostic_nms,
            retina_masks=self.retina_masks,
            device=self.device,
        )
        results: Results = results[0].cpu()
        t_infer1 = time.time()
        infer_time = (t_infer1 - t_infer0) * 1000.0  # ms

        # -----------------------------
        # 3) 후처리 + DetectionArray 생성 + publish
        # -----------------------------
        t_post0 = time.time()

        hypothesis = []
        boxes = []
        masks = []
        keypoints = []

        if results.boxes or results.obb:
            hypothesis = self.parse_hypothesis(results)
            boxes = self.parse_boxes(results)

        if results.masks:
            masks = self.parse_masks(results)

        if results.keypoints:
            keypoints = self.parse_keypoints(results)

        # create detection msgs
        detections_msg = DetectionArray()

        for i in range(len(results)):

            aux_msg = Detection()

            if (results.boxes or results.obb) and hypothesis and boxes:
                aux_msg.class_id = hypothesis[i]["class_id"]
                aux_msg.class_name = hypothesis[i]["class_name"]
                aux_msg.score = hypothesis[i]["score"]

                aux_msg.bbox = boxes[i]

            if results.masks and masks:
                aux_msg.mask = masks[i]

            if results.keypoints and keypoints:
                aux_msg.keypoints = keypoints[i]

            detections_msg.detections.append(aux_msg)

        # publish detections
        detections_msg.header = msg.header
        self._pub.publish(detections_msg)

        # 원래 있던 메모리 정리
        del results
        del cv_image

        t_post1 = time.time()
        post_time = (t_post1 - t_post0) * 1000.0  # ms

        # -----------------------------
        # 4) 전체 시간 + FPS 계산
        # -----------------------------
        t1 = time.time()
        total_time = (t1 - t0) * 1000.0  # ms

        fps_str = ""
        if self._last_wall_time is None:
            self._last_wall_time = t1
        else:
            dt = t1 - self._last_wall_time
            if dt > 0.0:
                fps = 1.0 / dt
                fps_str = f" | inst FPS ~ {fps:.2f}"
            self._last_wall_time = t1

        # -----------------------------
        # 5) 통계 버퍼 업데이트 + N프레임마다 평균 로그
        # -----------------------------
        self._timing_buffer.append((cv_time, infer_time, post_time, total_time))

        if self.debug_timing and (self._frame_count % self.debug_interval == 0):
            self._log_timing_stats(len(detections_msg.detections), fps_str)

        # 필요하면 매 프레임 로그도 여기서 찍을 수 있음
        # self.get_logger().info(
        #     f"[Frame {self._frame_count}] "
        #     f"cv={cv_time:.1f}ms, infer={infer_time:.1f}ms, "
        #     f"post={post_time:.1f}ms, total={total_time:.1f}ms "
        #     f"(dets={len(detections_msg.detections)}){fps_str}"
        # )

    def set_classes_cb(
        self,
        req: SetClasses.Request,
        res: SetClasses.Response,
    ) -> SetClasses.Response:
        self.get_logger().info(f"Setting classes: {req.classes}")
        self.yolo.set_classes(req.classes)
        self.get_logger().info(f"New classes: {self.yolo.names}")
        return res

    # -----------------------------
    # 디버그용 타이밍 통계 로그 함수
    # -----------------------------
    def _log_timing_stats(self, num_dets: int, fps_str: str) -> None:
        if not self._timing_buffer:
            return

        cv_times, infer_times, post_times, total_times = zip(*self._timing_buffer)

        def avg(xs: Tuple[float, ...]) -> float:
            return float(sum(xs) / len(xs))

        avg_cv = avg(cv_times)
        avg_infer = avg(infer_times)
        avg_post = avg(post_times)
        avg_total = avg(total_times)

        self.get_logger().info(
            f"[YOLO Timing (last {len(self._timing_buffer)} frames)] "
            f"cv={avg_cv:.1f}ms, infer={avg_infer:.1f}ms, "
            f"post={avg_post:.1f}ms, total={avg_total:.1f}ms, "
            f"last_frame_dets={num_dets}{fps_str}"
        )


def main():
    rclpy.init()
    node = YoloNode()
    node.trigger_configure()
    node.trigger_activate()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
