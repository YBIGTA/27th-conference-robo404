#!/usr/bin/env python3
"""
Vision API Streamlit Dashboard

Displays vision analysis results and camera images from ROS topics.
"""

import threading
from datetime import datetime
from collections import deque

import streamlit as st
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy
from std_msgs.msg import String
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import numpy as np


class DashboardNode(Node):
    """ROS node for receiving vision data."""

    def __init__(self, data_store):
        super().__init__('vision_dashboard_node')
        self.data_store = data_store
        self.cv_bridge = CvBridge()

        # QoS for image (best effort for camera streams)
        image_qos = QoSProfile(
            depth=1,
            reliability=QoSReliabilityPolicy.BEST_EFFORT
        )

        # Subscribers
        self.result_sub = self.create_subscription(
            String,
            '/vision/analysis_result',
            self.result_callback,
            10
        )

        self.image_sub = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.image_callback,
            image_qos
        )

        self.get_logger().info('Dashboard node initialized')

    def result_callback(self, msg: String):
        """Handle analysis result."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.data_store['latest_result'] = msg.data
        self.data_store['history'].appendleft({
            'time': timestamp,
            'result': msg.data
        })

    def image_callback(self, msg: Image):
        """Handle camera image."""
        try:
            cv_image = self.cv_bridge.imgmsg_to_cv2(msg, 'rgb8')
            self.data_store['latest_image'] = cv_image
        except Exception as e:
            self.get_logger().warn(f'Failed to convert image: {e}')


def run_ros_node(data_store):
    """Run ROS node in background thread."""
    rclpy.init()
    node = DashboardNode(data_store)
    try:
        rclpy.spin(node)
    except Exception:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


def init_ros():
    """Initialize ROS node in background if not already running."""
    if 'ros_initialized' not in st.session_state:
        st.session_state.ros_initialized = True
        st.session_state.data_store = {
            'latest_result': None,
            'latest_image': None,
            'history': deque(maxlen=20)
        }

        # Start ROS node in background thread
        ros_thread = threading.Thread(
            target=run_ros_node,
            args=(st.session_state.data_store,),
            daemon=True
        )
        ros_thread.start()


def main():
    """Main Streamlit app."""
    st.set_page_config(
        page_title='Vision API Dashboard',
        page_icon='🤖',
        layout='wide'
    )

    # Initialize ROS
    init_ros()
    data_store = st.session_state.data_store

    # Header
    st.title('🤖 Vision API Dashboard')
    st.markdown('---')

    # Layout: two columns
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader('📷 카메라 이미지')
        image_placeholder = st.empty()

        if data_store['latest_image'] is not None:
            image_placeholder.image(
                data_store['latest_image'],
                channels='RGB',
                use_container_width=True
            )
        else:
            image_placeholder.info('카메라 이미지 대기 중...')

    with col2:
        st.subheader('🔍 최신 분석 결과')
        result_placeholder = st.empty()

        if data_store['latest_result']:
            result_placeholder.success(data_store['latest_result'])
        else:
            result_placeholder.info('분석 결과 대기 중...')

    # History section
    st.markdown('---')
    st.subheader('📜 분석 히스토리')

    if data_store['history']:
        for item in data_store['history']:
            with st.expander(f"🕐 {item['time']}", expanded=False):
                st.write(item['result'])
    else:
        st.info('아직 분석 기록이 없습니다.')

    # Auto-refresh
    st.markdown('---')
    st.caption('페이지는 2초마다 자동 새로고침됩니다.')

    # Rerun every 2 seconds
    import time
    time.sleep(2)
    st.rerun()


if __name__ == '__main__':
    main()
