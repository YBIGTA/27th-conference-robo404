#!/usr/bin/env python3
"""
Detection Handler Node

Subscribes to YOLO detections and performs specific actions based on detected objects.
For example, if a chair is detected, it can trigger navigation towards the chair.
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy
from std_msgs.msg import String, Bool
from geometry_msgs.msg import Point
from yolo_msgs.msg import DetectionArray


class DetectionHandlerNode(Node):
    def __init__(self):
        super().__init__('detection_handler_node')

        # Declare parameters
        self.declare_parameter('confidence_threshold', 0.7)
        self.declare_parameter('target_objects', ['chair', 'red_ball'])
        self.declare_parameter('detection_timeout', 5.0)  # seconds
        
        # Load parameters
        self.confidence_threshold = self.get_parameter('confidence_threshold').value
        self.target_objects = self.get_parameter('target_objects').value
        self.detection_timeout = self.get_parameter('detection_timeout').value
        
        # State tracking
        self.last_detected_objects = {}
        self.current_target = None
        self.target_position = None
        
        # QoS for YOLO detections
        qos = QoSProfile(depth=10, reliability=QoSReliabilityPolicy.BEST_EFFORT)

        # Subscriber: YOLO detections
        self.detection_sub = self.create_subscription(
            DetectionArray,
            '/yolo/detections',
            self.detection_callback,
            qos
        )

        # Publishers
        self.event_pub = self.create_publisher(String, '/detection_events', 10)
        self.target_pub = self.create_publisher(Point, '/target_position', 10)
        self.movement_cmd_pub = self.create_publisher(String, '/movement_command', 10)

        # Timer for detection timeout check
        self.timer = self.create_timer(1.0, self.check_timeouts)

        self.get_logger().info(
            f'Detection Handler Node initialized\n'
            f'  Confidence threshold: {self.confidence_threshold}\n'
            f'  Target objects: {self.target_objects}\n'
            f'  Detection timeout: {self.detection_timeout}s'
        )

    def detection_callback(self, msg: DetectionArray):
        """Process YOLO detections and trigger actions for specific objects."""
        if not msg.detections:
            return

        # Filter detections by confidence and target objects
        relevant_detections = []
        for detection in msg.detections:
            if (detection.score >= self.confidence_threshold and 
                detection.class_name in self.target_objects):
                relevant_detections.append(detection)

        if not relevant_detections:
            return

        # Sort by confidence score (highest first)
        relevant_detections.sort(key=lambda d: d.score, reverse=True)
        
        # Process the highest confidence detection
        best_detection = relevant_detections[0]
        self.handle_object_detection(best_detection)
            
    def handle_object_detection(self, detection):
        """Handle detection of a specific object type."""
        obj_class = detection.class_name
        confidence = detection.score
        
        # Update last detected objects
        self.last_detected_objects[obj_class] = {
            'confidence': confidence,
            'timestamp': self.get_clock().now(),
            'bbox': detection.bbox,
            'detection': detection
        }
        
        # Log the detection
        self.get_logger().info(
            f'Detected {obj_class} with confidence {confidence:.2f}'
        )
        
        # Publish detection event
        event_msg = String()
        event_msg.data = f'detected:{obj_class}:{confidence:.2f}'
        self.event_pub.publish(event_msg)
        
        # Set as current target if not already tracking something
        if self.current_target != obj_class:
            self.set_target(obj_class, detection)
        
        # Perform object-specific actions
        if obj_class == 'chair':
            self.handle_chair_detection(detection)
        elif obj_class == 'red_ball':
            self.handle_red_ball_detection(detection)
    
    def set_target(self, obj_class, detection):
        """Set a new target object for tracking and movement."""
        self.current_target = obj_class
        
        # Calculate target position from bounding box center
        # Note: This is in image coordinates, would need conversion to world coordinates
        bbox_center_x = detection.bbox.center.position.x
        bbox_center_y = detection.bbox.center.position.y
        
        # For now, use normalized image coordinates (-1 to 1)
        # In a real system, you'd convert this to world coordinates using depth info
        target_point = Point()
        target_point.x = (bbox_center_x - 960.0) / 960.0  # Normalize assuming 1920 width
        target_point.y = (bbox_center_y - 540.0) / 540.0  # Normalize assuming 1080 height
        target_point.z = 0.0
        
        self.target_position = target_point
        self.target_pub.publish(target_point)
        
        self.get_logger().info(f'Target set to {obj_class} at position ({target_point.x:.2f}, {target_point.y:.2f})')
    
    def handle_chair_detection(self, detection):
        """Specific actions when a chair is detected."""
        self.get_logger().info('Chair detected! Triggering chair-specific behavior...')
        
        # Publish movement command to approach the chair
        cmd_msg = String()
        cmd_msg.data = 'approach_chair'
        self.movement_cmd_pub.publish(cmd_msg)
        
        # Get chair position
        chair_x = detection.bbox.center.position.x
        chair_y = detection.bbox.center.position.y
        
        self.get_logger().info(f'Chair location in image: ({chair_x:.1f}, {chair_y:.1f})')
    
    def handle_red_ball_detection(self, detection):
        """Specific actions when a red_ball is detected."""
        self.get_logger().info('Red ball detected! Triggering red ball-specific behavior...')
        
        # Publish movement command to approach red ball
        cmd_msg = String()
        cmd_msg.data = 'approach_red_ball'
        self.movement_cmd_pub.publish(cmd_msg)
        
        ball_x = detection.bbox.center.position.x
        ball_y = detection.bbox.center.position.y
        
        self.get_logger().info(f'Red ball location in image: ({ball_x:.1f}, {ball_y:.1f})')
        
        # Publish specific red ball event
        event_msg = String()
        event_msg.data = f'red_ball_found:x={ball_x:.1f},y={ball_y:.1f}'
        self.event_pub.publish(event_msg)
 
    
    def check_timeouts(self):
        """Check for detection timeouts and clear old targets."""
        current_time = self.get_clock().now()
        timeout_ns = self.detection_timeout * 1e9
        
        # Remove old detections
        to_remove = []
        for obj_class, data in self.last_detected_objects.items():
            elapsed = (current_time - data['timestamp']).nanoseconds
            if elapsed > timeout_ns:
                to_remove.append(obj_class)
        
        for obj_class in to_remove:
            del self.last_detected_objects[obj_class]
            if self.current_target == obj_class:
                self.get_logger().info(f'Target {obj_class} lost due to timeout')
                self.current_target = None
                self.target_position = None
                
                # Publish stop command
                cmd_msg = String()
                cmd_msg.data = 'stop'
                self.movement_cmd_pub.publish(cmd_msg)
    
    def get_last_detection(self, object_class):
        """Get the last detection info for a specific object class."""
        return self.last_detected_objects.get(object_class, None)
    
    def get_current_target(self):
        """Get the current target object being tracked."""
        return self.current_target, self.target_position


def main(args=None):
    rclpy.init(args=args)
    node = DetectionHandlerNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()