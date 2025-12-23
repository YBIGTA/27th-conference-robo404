#!/usr/bin/env python3
"""
ROS 2 Node/Topic Architecture Visualization
ROBO 404 - 위험 탐지 AI 로봇 프로젝트
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

# 한글 폰트 설정
plt.rcParams['font.family'] = ['DejaVu Sans', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

fig, ax = plt.subplots(1, 1, figsize=(20, 14))
ax.set_xlim(0, 20)
ax.set_ylim(0, 14)
ax.set_aspect('equal')
ax.axis('off')

# 색상 정의
colors = {
    'gazebo': '#FF6B6B',      # 빨강 - Gazebo
    'bridge': '#4ECDC4',      # 청록 - Bridge
    'yolo': '#45B7D1',        # 파랑 - YOLO
    'tracker': '#96CEB4',     # 초록 - Tracker
    'vision': '#FFEAA7',      # 노랑 - Vision API
    'topic': '#DDA0DD',       # 연보라 - Topic
    'external': '#C0C0C0',    # 회색 - External
}

def draw_node(ax, x, y, width, height, label, color, sublabel=None):
    """노드 박스 그리기"""
    box = FancyBboxPatch((x - width/2, y - height/2), width, height,
                         boxstyle="round,pad=0.05,rounding_size=0.2",
                         facecolor=color, edgecolor='black', linewidth=2)
    ax.add_patch(box)
    ax.text(x, y + 0.1, label, ha='center', va='center', fontsize=10, fontweight='bold')
    if sublabel:
        ax.text(x, y - 0.25, sublabel, ha='center', va='center', fontsize=7, style='italic')

def draw_topic(ax, x, y, label, color='#DDA0DD'):
    """토픽 (타원) 그리기"""
    ellipse = mpatches.Ellipse((x, y), 2.2, 0.6, facecolor=color, edgecolor='black', linewidth=1.5)
    ax.add_patch(ellipse)
    ax.text(x, y, label, ha='center', va='center', fontsize=7, fontweight='bold')

def draw_arrow(ax, start, end, color='black', style='->', curved=False):
    """화살표 그리기"""
    if curved:
        arrow = FancyArrowPatch(start, end, connectionstyle="arc3,rad=0.2",
                                arrowstyle=style, mutation_scale=15,
                                color=color, linewidth=1.5)
    else:
        arrow = FancyArrowPatch(start, end, arrowstyle=style, mutation_scale=15,
                                color=color, linewidth=1.5)
    ax.add_patch(arrow)

# ========== 타이틀 ==========
ax.text(10, 13.5, 'ROBO 404 - ROS 2 Node/Topic Architecture',
        ha='center', va='center', fontsize=16, fontweight='bold')
ax.text(10, 13.0, 'Danger Detection AI Robot System',
        ha='center', va='center', fontsize=12, style='italic', color='gray')

# ========== Gazebo Simulator Layer ==========
gazebo_box = FancyBboxPatch((0.5, 10), 5, 2.5, boxstyle="round,pad=0.1",
                            facecolor='#FFE5E5', edgecolor='#FF6B6B', linewidth=3)
ax.add_patch(gazebo_box)
ax.text(3, 12.2, 'Gazebo Simulator', ha='center', fontsize=11, fontweight='bold', color='#FF6B6B')

draw_node(ax, 2, 11.2, 1.8, 0.7, 'Camera', colors['gazebo'], 'Sensor')
draw_node(ax, 4.2, 11.2, 1.8, 0.7, 'LiDAR', colors['gazebo'], 'Sensor')
draw_node(ax, 3, 10.4, 2.2, 0.6, 'Robot Model', colors['gazebo'], 'TurtleBot3')

# ========== ROS-Gazebo Bridge ==========
bridge_box = FancyBboxPatch((6, 9.5), 3.5, 3, boxstyle="round,pad=0.1",
                            facecolor='#E5FFFF', edgecolor='#4ECDC4', linewidth=3)
ax.add_patch(bridge_box)
ax.text(7.75, 12.2, 'ROS-Gazebo Bridge', ha='center', fontsize=10, fontweight='bold', color='#4ECDC4')

bridge_topics = [
    '/camera/image_raw',
    '/camera/camera_info',
    '/scan',
    '/odom',
    '/cmd_vel',
    '/tf'
]
for i, topic in enumerate(bridge_topics):
    y_pos = 11.6 - i * 0.35
    ax.text(7.75, y_pos, topic, ha='center', fontsize=7, family='monospace')

# ========== YOLO Node ==========
draw_node(ax, 12, 11, 2.5, 1.2, 'YOLO Node', colors['yolo'], 'yolo_ros')
ax.text(12, 10.2, 'model: yolov8n or', ha='center', fontsize=6, color='gray')
ax.text(12, 9.95, 'chair_state_v1', ha='center', fontsize=6, color='gray')

# ========== Camera Tracker Node ==========
draw_node(ax, 12, 7, 2.8, 1.4, 'Camera Tracker', colors['tracker'], 'camera_tracker_node')
ax.text(12, 6.1, 'PID Control', ha='center', fontsize=7, color='gray')

# ========== Vision Analyzer Node ==========
draw_node(ax, 17, 7, 2.8, 1.4, 'Vision Analyzer', colors['vision'], 'vision_api_node')
ax.text(17, 6.1, 'OpenAI/Gemini/HF', ha='center', fontsize=7, color='gray')

# ========== Topics (타원) ==========
# YOLO -> Tracker
draw_topic(ax, 12, 9, '/yolo/detections')

# Tracker -> Gazebo
draw_topic(ax, 7.75, 6, '/camera/pan_cmd')
draw_topic(ax, 7.75, 5.2, '/camera/tilt_cmd')
draw_topic(ax, 14.5, 5.2, '/camera/stable')

# Vision output
draw_topic(ax, 17, 4.5, '/vision/analysis_result')

# Camera image topic
draw_topic(ax, 14.5, 9, '/camera/image_raw', '#FFB6C1')

# ========== Navigation Stack ==========
nav_box = FancyBboxPatch((1, 2), 5, 2.5, boxstyle="round,pad=0.1",
                         facecolor='#F0F0F0', edgecolor='#808080', linewidth=2)
ax.add_patch(nav_box)
ax.text(3.5, 4.2, 'Navigation Stack (Nav2)', ha='center', fontsize=10, fontweight='bold', color='#606060')
ax.text(3.5, 3.5, '/cmd_vel, /scan, /odom', ha='center', fontsize=8, family='monospace')
ax.text(3.5, 3.0, 'SLAM / Path Planning', ha='center', fontsize=8, color='gray')
ax.text(3.5, 2.5, 'Autonomous Navigation', ha='center', fontsize=8, color='gray')

# ========== External Output ==========
output_box = FancyBboxPatch((14, 2), 5, 2, boxstyle="round,pad=0.1",
                            facecolor='#FFFACD', edgecolor='#DAA520', linewidth=2)
ax.add_patch(output_box)
ax.text(16.5, 3.7, 'Analysis Output', ha='center', fontsize=10, fontweight='bold', color='#B8860B')
ax.text(16.5, 3.0, 'Danger Detection Results', ha='center', fontsize=8)
ax.text(16.5, 2.5, 'JSON / Text Response', ha='center', fontsize=8, color='gray')

# ========== 화살표 연결 ==========
# Gazebo -> Bridge
draw_arrow(ax, (5.5, 11), (6, 11), color='#FF6B6B')

# Bridge -> Camera Image Topic
draw_arrow(ax, (9.5, 10.5), (13.3, 9.2), color='#4ECDC4')

# Camera Image -> YOLO
draw_arrow(ax, (14.5, 9.4), (13.1, 10.4), color='gray')

# Camera Image -> Vision
draw_arrow(ax, (15.6, 9), (16.2, 6.7), color='gray')

# YOLO -> Detection Topic
draw_arrow(ax, (12, 10.4), (12, 9.35), color='#45B7D1')

# Detection -> Tracker
draw_arrow(ax, (12, 8.65), (12, 7.7), color='#45B7D1')

# Tracker -> Pan/Tilt Topics
draw_arrow(ax, (10.6, 6.8), (8.8, 6.1), color='#96CEB4')
draw_arrow(ax, (10.6, 6.5), (8.8, 5.3), color='#96CEB4')

# Pan/Tilt -> Bridge
draw_arrow(ax, (6.65, 6), (6, 9.5), color='#96CEB4', curved=True)

# Tracker -> Stable Topic
draw_arrow(ax, (13.4, 6.8), (14.5, 5.55), color='#96CEB4')

# Stable -> Vision
draw_arrow(ax, (14.8, 5.5), (16, 6.3), color='#96CEB4')

# Vision -> Result
draw_arrow(ax, (17, 6.3), (17, 4.85), color='#FFEAA7')

# Result -> Output
draw_arrow(ax, (17, 4.15), (16.8, 4), color='#DAA520')

# Bridge -> Nav
draw_arrow(ax, (6, 9.5), (4.5, 4.5), color='#4ECDC4', curved=True)

# ========== 범례 ==========
legend_elements = [
    mpatches.Patch(facecolor=colors['gazebo'], edgecolor='black', label='Gazebo Components'),
    mpatches.Patch(facecolor=colors['bridge'], edgecolor='black', label='ROS-Gazebo Bridge'),
    mpatches.Patch(facecolor=colors['yolo'], edgecolor='black', label='YOLO Detection'),
    mpatches.Patch(facecolor=colors['tracker'], edgecolor='black', label='Camera Tracker'),
    mpatches.Patch(facecolor=colors['vision'], edgecolor='black', label='Vision API'),
    mpatches.Patch(facecolor=colors['topic'], edgecolor='black', label='ROS Topics'),
]
ax.legend(handles=legend_elements, loc='lower right', fontsize=8, framealpha=0.9)

# ========== Data Flow 표시 ==========
ax.text(0.8, 1, 'Data Flow:', fontsize=9, fontweight='bold')
ax.text(0.8, 0.6, '1. Gazebo Camera -> Image -> YOLO Detection', fontsize=7)
ax.text(0.8, 0.3, '2. YOLO Detections -> Camera Tracker -> Pan/Tilt Control', fontsize=7)
ax.text(8, 0.6, '3. Camera Stable -> Vision API -> Analysis Result', fontsize=7)
ax.text(8, 0.3, '4. Parallel: Nav2 uses /scan, /odom for autonomous navigation', fontsize=7)

plt.tight_layout()
plt.savefig('/home/junchan/github/27th-conference-robo404/ros_architecture.png', dpi=150, bbox_inches='tight',
            facecolor='white', edgecolor='none')
plt.savefig('/home/junchan/github/27th-conference-robo404/ros_architecture.pdf', bbox_inches='tight',
            facecolor='white', edgecolor='none')
print("Architecture diagram saved to:")
print("  - ros_architecture.png")
print("  - ros_architecture.pdf")
