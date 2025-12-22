#!/usr/bin/env python3
"""
박스 A, B, C에 라벨 설정

사용법:
  python3 set_labels.py 단어1 단어2 단어3

예시:
  python3 set_labels.py A B C
  python3 set_labels.py EXIT ENTER STOP
"""

import sys
import os
from PIL import Image, ImageDraw, ImageFont

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

TEXTURE_PATHS = [
    os.path.join(SCRIPT_DIR, "models/labeled_box_a/materials/textures/label_a.png"),
    os.path.join(SCRIPT_DIR, "models/labeled_box_b/materials/textures/label_b.png"),
    os.path.join(SCRIPT_DIR, "models/labeled_box_c/materials/textures/label_c.png"),
]

def create_label(text, output_path, size=512):
    img = Image.new("RGB", (size, size), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    font_size = size // 2
    font = None
    for font_path in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    ]:
        try:
            font = ImageFont.truetype(font_path, font_size)
            break
        except:
            continue
    if font is None:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]

    if text_width > size * 0.85:
        font_size = int(font_size * (size * 0.85) / text_width)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except:
            pass
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]

    text_height = bbox[3] - bbox[1]
    x = (size - text_width) // 2
    y = (size - text_height) // 2
    draw.text((x, y), text, font=font, fill=(0, 0, 0))
    img.save(output_path)

def main():
    if len(sys.argv) != 4:
        print("사용법: python3 set_labels.py 단어1 단어2 단어3")
        print("예시:  python3 set_labels.py A B C")
        sys.exit(1)

    words = sys.argv[1:4]

    for i, (word, path) in enumerate(zip(words, TEXTURE_PATHS)):
        create_label(word, path)
        print(f"박스 {['A','B','C'][i]}: '{word}'")

    print(f"\nGazebo 실행:")
    print(f"GZ_SIM_RESOURCE_PATH={SCRIPT_DIR}/models gz sim {SCRIPT_DIR}/worlds/labeled_world.sdf")

if __name__ == "__main__":
    main()
