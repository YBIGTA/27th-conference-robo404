"""Google Gemini Vision API implementation."""

import time
import cv2
import numpy as np
from .base import VisionAPIBase, AnalysisResult


class GeminiVisionAPI(VisionAPIBase):
    """Google Gemini Vision API implementation."""

    DEFAULT_MODEL = "gemini-1.5-flash"

    def __init__(self, api_key: str, model: str = None):
        super().__init__(api_key, model or self.DEFAULT_MODEL)
        self._model_instance = None

    def _validate_credentials(self) -> None:
        """Initialize Gemini client."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._model_instance = genai.GenerativeModel(self.model)
        except ImportError:
            raise ImportError(
                "google-generativeai package not installed. "
                "Run: pip install google-generativeai"
            )

    def get_provider_name(self) -> str:
        return "Google Gemini"

    def analyze_image(
        self,
        image: np.ndarray,
        prompt: str = "Describe what you see in this image."
    ) -> AnalysisResult:
        start_time = time.time()

        try:
            from PIL import Image

            # Convert BGR to RGB for PIL
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_image)

            response = self._model_instance.generate_content([prompt, pil_image])

            latency = (time.time() - start_time) * 1000
            content = response.text

            return AnalysisResult(
                success=True,
                description=content,
                detected_objects=[],
                confidence=0.9,
                raw_response=content,
                latency_ms=latency
            )

        except Exception as e:
            return AnalysisResult(
                success=False,
                description="",
                detected_objects=[],
                confidence=0.0,
                error_message=str(e),
                latency_ms=(time.time() - start_time) * 1000
            )
