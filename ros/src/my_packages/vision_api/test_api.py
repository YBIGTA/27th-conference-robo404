#!/usr/bin/env python3
"""
Vision API 테스트 스크립트

사용법:
    # Huggingface 테스트 (Florence-2)
    export HF_API_KEY="hf_..."
    python test_api.py huggingface /path/to/image.jpg

    # OCR 테스트
    python test_api.py huggingface /path/to/image.jpg --task ocr

    # OpenAI 테스트
    export OPENAI_API_KEY="sk-..."
    python test_api.py openai /path/to/image.jpg

    # Gemini 테스트
    export GEMINI_API_KEY="..."
    python test_api.py gemini /path/to/image.jpg
"""

import sys
import os
import argparse

# 패키지 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vision_api.api import VisionAPIFactory


def main():
    parser = argparse.ArgumentParser(description='Vision API 테스트')
    parser.add_argument('provider', choices=['openai', 'gemini', 'huggingface'],
                        help='API 제공자')
    parser.add_argument('image_path', help='테스트할 이미지 경로')
    parser.add_argument('--task', choices=['ocr', 'caption', 'describe'],
                        default='describe', help='작업 유형 (huggingface만)')
    parser.add_argument('--prompt', default='이 이미지에서 무엇이 보이나요?',
                        help='분석 프롬프트')
    args = parser.parse_args()

    # API 키 가져오기
    key_map = {
        'openai': 'OPENAI_API_KEY',
        'gemini': 'GEMINI_API_KEY',
        'huggingface': 'HF_API_KEY',
    }

    env_key = key_map[args.provider]
    api_key = os.environ.get(env_key)

    if not api_key:
        print(f"환경변수 {env_key}가 설정되지 않았습니다.")
        print(f"  export {env_key}='your-api-key'")
        return 1

    # 이미지 로드
    if not os.path.exists(args.image_path):
        print(f"이미지 파일을 찾을 수 없습니다: {args.image_path}")
        return 1

    import cv2
    image = cv2.imread(args.image_path)
    if image is None:
        print(f"이미지를 읽을 수 없습니다: {args.image_path}")
        return 1

    print(f"이미지 로드 완료: {image.shape}")

    # API 클라이언트 생성
    try:
        client = VisionAPIFactory.create(args.provider, api_key)
        print(f"API 클라이언트 생성: {client.get_provider_name()}")
    except Exception as e:
        print(f"API 클라이언트 생성 실패: {e}")
        return 1

    # 이미지 분석
    print(f"\n분석 중... (task: {args.task})")

    if args.provider == 'huggingface':
        # Huggingface는 task 파라미터 지원
        result = client.analyze_image(image, args.prompt, task=args.task)
    else:
        result = client.analyze_image(image, args.prompt)

    # 결과 출력
    print("\n" + "=" * 50)
    print(f"성공: {result.success}")
    print(f"응답 시간: {result.latency_ms:.0f}ms")
    print("=" * 50)

    if result.success:
        print(f"\n{result.description}")
    else:
        print(f"\n오류: {result.error_message}")

    return 0 if result.success else 1


if __name__ == '__main__':
    sys.exit(main())
