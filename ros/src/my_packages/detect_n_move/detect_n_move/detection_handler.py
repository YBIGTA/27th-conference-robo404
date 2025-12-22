#!/usr/bin/env python3
"""
Detection Handler Node (Nav2 Enabled) - FIXED for yolo_msgs
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy
from std_msgs.msg import String
from geometry_msgs.msg import PoseStamped
import statistics
import tf2_ros
import tf2_geometry_msgs
from tf2_ros import Buffer, TransformListener

# Import the correct message type
from yolo_msgs.msg import DetectionArray

class DetectionHandlerNode(Node):
    def __init__(self):
        super().__init__('detection_handler_node')

        # Parameters
        self.declare_parameter('confidence_threshold', 0.7)
        self.declare_parameter('target_objects', ['chair', 'red_ball'])
        self.declare_parameter('detection_timeout', 5.0)
        
        self.confidence_threshold = self.get_parameter('confidence_threshold').value
        self.target_objects = self.get_parameter('target_objects').value
        self.detection_timeout = self.get_parameter('detection_timeout').value
        
        # State
        self.frame_count = 0
        self.verification_window = 10
        self.required_confirmations = 2
        self.verification_states = {
            obj: {'state': 'IDLE', 'start_frame': 0, 'hits': 0, 'stored_detections': []} 
            for obj in self.target_objects
        }
        self.last_detected_objects = {}
        self.current_target = None

        # Tools
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        # Subscribers
        qos = QoSProfile(depth=10, reliability=QoSReliabilityPolicy.BEST_EFFORT)
        self.create_subscription(DetectionArray, '/yolo/detections_3d', self.detection_callback, qos)

        # Publishers
        self.event_pub = self.create_publisher(String, '/detection_events', 10)
        self.target_pose_pub = self.create_publisher(PoseStamped, '/target_pose', 10)
        self.movement_cmd_pub = self.create_publisher(String, '/movement_command', 10)
        
        self.timer = self.create_timer(1.0, self.check_timeouts)
        self.get_logger().info('Nav2 Detection Handler Initialized.')

    def detection_callback(self, msg: DetectionArray):
        self.frame_count += 1
        detections_in_frame = {} 
        
        for d in msg.detections:
            # CHECK 1: Ensure 3D data exists
            if d.bbox3d.center.position.z == 0.0:
                continue

            # CHECK 2: Access fields directly (yolo_msgs style)
            # Old: d.results[0].hypothesis.score
            # New: d.score
            if d.score < self.confidence_threshold:
                continue

            # Old: d.results[0].hypothesis.class_id
            # New: d.class_name (or d.class_id depending on version, usually class_name is the string)
            class_name = d.class_name 

            if class_name not in detections_in_frame:
                detections_in_frame[class_name] = d
            elif d.score > detections_in_frame[class_name].score:
                detections_in_frame[class_name] = d

        for target_name in self.target_objects:
            self.update_verification_logic(target_name, detections_in_frame)

    def update_verification_logic(self, target_name, detections_in_frame):
        state_info = self.verification_states[target_name]
        detection = detections_in_frame.get(target_name)
        
        if state_info['state'] == 'IDLE':
            if detection:
                state_info['state'] = 'VERIFYING'
                state_info['start_frame'] = self.frame_count
                state_info['hits'] = 0
                state_info['stored_detections'] = [detection]
        
        elif state_info['state'] == 'VERIFYING':
            if (self.frame_count - state_info['start_frame']) > self.verification_window:
                self.reset_state(target_name)
                return

            if detection: 
                state_info['hits'] += 1
                state_info['stored_detections'].append(detection)

            if state_info['hits'] >= self.required_confirmations:
                state_info['state'] = 'CONFIRMED'
                robust_detection = self.get_robust_target_location(state_info['stored_detections'])
                if robust_detection:
                    self.process_verified_target(robust_detection)

        elif state_info['state'] == 'CONFIRMED':
            if detection:
                self.process_verified_target(detection)

    def get_robust_target_location(self, detection_list):
        if not detection_list: return None
        
        # Access bbox3d directly
        x_coords = [d.bbox3d.center.position.x for d in detection_list]
        y_coords = [d.bbox3d.center.position.y for d in detection_list]
        z_coords = [d.bbox3d.center.position.z for d in detection_list]
        
        robust_det = detection_list[-1] 
        robust_det.bbox3d.center.position.x = statistics.median(x_coords)
        robust_det.bbox3d.center.position.y = statistics.median(y_coords)
        robust_det.bbox3d.center.position.z = statistics.median(z_coords)
        return robust_det

    def process_verified_target(self, detection):
        # CHECK 3: Access class_name directly
        obj_class = detection.class_name
        
        self.last_detected_objects[obj_class] = self.get_clock().now()
        
        msg = String()
        msg.data = f"detected:{obj_class}"
        self.event_pub.publish(msg)

        if self.current_target != obj_class:
            # DEBUG: Log raw detection data
            self.get_logger().info(f"RAW Detection - Class: {obj_class}")
            self.get_logger().info(f"RAW bbox3d center: x={detection.bbox3d.center.position.x:.3f}, y={detection.bbox3d.center.position.y:.3f}, z={detection.bbox3d.center.position.z:.3f}")
            self.get_logger().info(f"RAW bbox3d frame: {detection.bbox3d.frame_id}")
            
            map_pose = self.get_3d_map_pose(detection)
            
            if map_pose:
                self.current_target = obj_class
                self.get_logger().info(f"Target locked: {obj_class} at Map (x={map_pose.pose.position.x:.2f}, y={map_pose.pose.position.y:.2f}, z={map_pose.pose.position.z:.2f})")
                
                self.target_pose_pub.publish(map_pose)
                
                cmd = String()
                cmd.data = f"approach_{obj_class}"
                self.movement_cmd_pub.publish(cmd)

    def get_3d_map_pose(self, detection):
        """Convert 3D detection to map pose with an APPROACH OFFSET"""
        try:
            p_cam = PoseStamped()
            # Use custom_camera_depth_optical_frame as the source frame
            p_cam.header.frame_id = 'custom_camera_depth_optical_frame'
            p_cam.header.stamp = rclpy.time.Time().to_msg() # Use Sim Time 0 for latest transform
            
            # --- FIX: Apply Approach Offset ---
            # The 'z' axis in optical frames is usually the forward distance.
            # We want to stop at a reasonable distance from the object.
            raw_depth = detection.bbox3d.center.position.z
            approach_offset = 0.3  # How far to stop from the object (in meters) - SAFER DISTANCE
            
            # Ensure we don't set a target behind the camera (min distance 0.2m)
            target_depth = max(0.2, raw_depth - approach_offset)
            
            p_cam.pose.position.x = detection.bbox3d.center.position.x
            p_cam.pose.position.y = detection.bbox3d.center.position.y
            p_cam.pose.position.z = target_depth # Use the adjusted depth
            
            p_cam.pose.orientation.w = 1.0 

            # Transform this "Approach Point" to the Map Frame
            target_pose = self.tf_buffer.transform(p_cam, 'map', timeout=rclpy.duration.Duration(seconds=1.0))
            
            # DEBUG: Log the final transformed coordinates
            self.get_logger().info(f"TRANSFORMED to Map - x={target_pose.pose.position.x:.3f}, y={target_pose.pose.position.y:.3f}, z={target_pose.pose.position.z:.3f}")
            
            return target_pose
            
        except (tf2_ros.LookupException, tf2_ros.ConnectivityException, tf2_ros.ExtrapolationException) as e:
            self.get_logger().warn(f"TF Error: {e}")
            return None
    """
    def get_3d_map_pose(self, detection):
        try:
            p_cam = tf2_geometry_msgs.PoseStamped()
            # yolo_msgs frame_id is usually inside the bbox3d or the main header
            # Note: detection.header might differ, but bbox3d.frame_id is what we set in detect_3d_node
            p_cam.header.frame_id = detection.bbox3d.frame_id 
            p_cam.header.stamp = rclpy.time.Time().to_msg()
            
            p_cam.pose.position = detection.bbox3d.center.position
            p_cam.pose.orientation.w = 1.0 

            transform = self.tf_buffer.lookup_transform('map', p_cam.header.frame_id, rclpy.time.Time())
            p_map = tf2_geometry_msgs.do_transform_pose(p_cam, transform)
            
            target_pose = PoseStamped()
            target_pose.header.frame_id = 'map'
            target_pose.header.stamp = self.get_clock().now().to_msg()
            target_pose.pose = p_map.pose
            
            return target_pose
            
        except (tf2_ros.LookupException, tf2_ros.ConnectivityException, tf2_ros.ExtrapolationException) as e:
            self.get_logger().warn(f"TF Error: {e}")
            return None
    """

    def reset_state(self, obj_class):
        if obj_class in self.verification_states:
            self.verification_states[obj_class]['state'] = 'IDLE'
            self.verification_states[obj_class]['hits'] = 0
            self.verification_states[obj_class]['stored_detections'] = []

    def check_timeouts(self):
        pass

def main(args=None):
    rclpy.init(args=args)
    node = DetectionHandlerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt: pass
    finally: node.destroy_node(); rclpy.shutdown()

if __name__ == '__main__':
    main()