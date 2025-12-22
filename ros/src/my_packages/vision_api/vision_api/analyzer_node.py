#!/usr/bin/env python3
"""
Vision API Analyzer Node

Captures images when camera is stable and sends them to external vision APIs.
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy

from std_msgs.msg import Bool, String
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

from vision_api.api import VisionAPIFactory


class VisionAnalyzerNode(Node):
    """Captures image on camera stabilization and analyzes via external API."""

    def __init__(self):
        super().__init__('vision_analyzer_node')

        # Parameters
        self.declare_parameter('api_provider', 'openai')
        self.declare_parameter('api_key', '')
        self.declare_parameter('api_model', '')
        self.declare_parameter(
            'analysis_prompt',
            'Describe what you see in this image. Focus on the main object.'
        )
        self.declare_parameter('min_stable_duration', 1.0)
        self.declare_parameter('analysis_cooldown', 5.0)
        self.declare_parameter('image_topic', '/camera/image_raw')
        self.declare_parameter('stable_topic', '/camera/stable')

        # Load parameters
        self.api_provider = self.get_parameter('api_provider').value
        self.api_key = self.get_parameter('api_key').value
        self.api_model = self.get_parameter('api_model').value or None
        self.analysis_prompt = self.get_parameter('analysis_prompt').value
        self.min_stable_duration = self.get_parameter('min_stable_duration').value
        self.analysis_cooldown = self.get_parameter('analysis_cooldown').value
        image_topic = self.get_parameter('image_topic').value
        stable_topic = self.get_parameter('stable_topic').value

        # Validate API key
        if not self.api_key:
            self.get_logger().error('API key not provided! Set api_key parameter.')
            raise ValueError('API key is required')

        # Initialize API client
        try:
            self.api_client = VisionAPIFactory.create(
                self.api_provider,
                self.api_key,
                self.api_model
            )
            self.get_logger().info(
                f'Initialized {self.api_client.get_provider_name()} API'
            )
        except Exception as e:
            self.get_logger().error(f'Failed to initialize API: {e}')
            raise

        # State variables
        self.cv_bridge = CvBridge()
        self.latest_image = None
        self.is_stable = False
        self.stable_start_time = None
        self.last_analysis_time = None
        self.analysis_in_progress = False

        # QoS for image (best effort for camera streams)
        image_qos = QoSProfile(
            depth=1,
            reliability=QoSReliabilityPolicy.BEST_EFFORT
        )

        # Subscribers
        self.image_sub = self.create_subscription(
            Image,
            image_topic,
            self.image_callback,
            image_qos
        )

        self.stable_sub = self.create_subscription(
            Bool,
            stable_topic,
            self.stable_callback,
            10
        )

        # Publishers
        self.result_pub = self.create_publisher(
            String,
            '/vision/analysis_result',
            10
        )

        # Timer for stability check
        self.timer = self.create_timer(0.1, self.check_and_analyze)

        self.get_logger().info(
            f'Vision Analyzer Node initialized\n'
            f'  Provider: {self.api_provider}\n'
            f'  Min stable duration: {self.min_stable_duration}s\n'
            f'  Analysis cooldown: {self.analysis_cooldown}s\n'
            f'  Image topic: {image_topic}\n'
            f'  Stable topic: {stable_topic}'
        )

    def image_callback(self, msg: Image):
        """Store latest image."""
        try:
            self.latest_image = self.cv_bridge.imgmsg_to_cv2(msg, 'bgr8')
        except Exception as e:
            self.get_logger().warn(f'Failed to convert image: {e}')

    def stable_callback(self, msg: Bool):
        """Update stability status."""
        current_time = self.get_clock().now()

        if msg.data and not self.is_stable:
            # Stability started
            self.is_stable = True
            self.stable_start_time = current_time
            self.get_logger().debug('Camera stabilized')

        elif not msg.data and self.is_stable:
            # Stability ended
            self.is_stable = False
            self.stable_start_time = None
            self.get_logger().debug('Camera unstable')

    def check_and_analyze(self):
        """Periodically check conditions and run analysis."""
        if self.analysis_in_progress:
            return

        if not self.is_stable or self.latest_image is None:
            return

        if self.stable_start_time is None:
            return

        current_time = self.get_clock().now()

        # Check minimum stable duration
        stable_duration = (current_time - self.stable_start_time).nanoseconds / 1e9
        if stable_duration < self.min_stable_duration:
            return

        # Check cooldown
        if self.last_analysis_time is not None:
            elapsed = (current_time - self.last_analysis_time).nanoseconds / 1e9
            if elapsed < self.analysis_cooldown:
                return

        # Run analysis
        self.perform_analysis()

    def perform_analysis(self):
        """Call API to analyze image."""
        self.analysis_in_progress = True

        try:
            self.get_logger().info('Starting image analysis...')

            result = self.api_client.analyze_image(
                self.latest_image,
                self.analysis_prompt
            )

            self.last_analysis_time = self.get_clock().now()

            if result.success:
                # Truncate for logging
                desc_preview = result.description[:200]
                if len(result.description) > 200:
                    desc_preview += '...'

                self.get_logger().info(
                    f'Analysis complete ({result.latency_ms:.0f}ms):\n'
                    f'{desc_preview}'
                )

                # Publish result
                result_msg = String()
                result_msg.data = result.description
                self.result_pub.publish(result_msg)

            else:
                self.get_logger().error(
                    f'Analysis failed: {result.error_message}'
                )

        except Exception as e:
            self.get_logger().error(f'Analysis error: {e}')

        finally:
            self.analysis_in_progress = False


def main(args=None):
    rclpy.init(args=args)
    node = VisionAnalyzerNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
