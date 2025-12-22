"""Huggingface Inference API implementation."""

import time
import requests
import numpy as np
from .base import VisionAPIBase, AnalysisResult


class HuggingFaceVisionAPI(VisionAPIBase):
    """Huggingface Inference API with image captioning support."""

    API_URL = "https://router.huggingface.co/hf/"
    DEFAULT_MODEL = "Salesforce/blip-image-captioning-large"

    def __init__(self, api_key: str, model: str = None):
        self._headers = None
        super().__init__(api_key, model or self.DEFAULT_MODEL)

    def _validate_credentials(self) -> None:
        """Set up API headers."""
        self._headers = {"Authorization": f"Bearer {self.api_key}"}

    def get_provider_name(self) -> str:
        return "Huggingface"

    def analyze_image(
        self,
        image: np.ndarray,
        prompt: str = "Describe what you see in this image.",
        task: str = None
    ) -> AnalysisResult:
        """
        Analyze image using Huggingface API.

        Args:
            image: BGR numpy array
            prompt: Text prompt (used for VQA models)
            task: Optional task type
        """
        import cv2

        start_time = time.time()

        try:
            # Encode image to bytes
            _, buffer = cv2.imencode('.jpg', image)
            image_bytes = buffer.tobytes()

            # API 호출
            api_url = f"{self.API_URL}{self.model}"
            response = requests.post(
                api_url,
                headers=self._headers,
                data=image_bytes,
                timeout=30
            )

            latency = (time.time() - start_time) * 1000

            if response.status_code != 200:
                return AnalysisResult(
                    success=False,
                    description="",
                    detected_objects=[],
                    confidence=0.0,
                    error_message=f"HTTP {response.status_code}: {response.text}",
                    latency_ms=latency
                )

            result = response.json()

            # 응답 파싱 (BLIP 모델은 [{"generated_text": "..."}] 형식)
            if isinstance(result, list) and len(result) > 0:
                content = result[0].get('generated_text', str(result[0]))
            elif isinstance(result, dict):
                content = result.get('generated_text', str(result))
            else:
                content = str(result)

            return AnalysisResult(
                success=True,
                description=content,
                detected_objects=[],
                confidence=0.9,
                raw_response=str(result),
                latency_ms=latency
            )

        except requests.exceptions.Timeout:
            return AnalysisResult(
                success=False,
                description="",
                detected_objects=[],
                confidence=0.0,
                error_message="Request timeout (30s)",
                latency_ms=(time.time() - start_time) * 1000
            )
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            return AnalysisResult(
                success=False,
                description="",
                detected_objects=[],
                confidence=0.0,
                error_message=error_msg,
                latency_ms=(time.time() - start_time) * 1000
            )

    def caption(self, image: np.ndarray) -> AnalysisResult:
        """Generate image caption."""
        return self.analyze_image(image)
