"""Huggingface Inference API implementation."""

import time
import numpy as np
from .base import VisionAPIBase, AnalysisResult


class HuggingFaceVisionAPI(VisionAPIBase):
    """Huggingface Inference API implementation."""

    DEFAULT_MODEL = "Salesforce/blip-image-captioning-large"

    def __init__(self, api_key: str, model: str = None):
        super().__init__(api_key, model or self.DEFAULT_MODEL)
        self._client = None

    def _validate_credentials(self) -> None:
        """Initialize Huggingface client."""
        try:
            from huggingface_hub import InferenceClient
            self._client = InferenceClient(token=self.api_key)
        except ImportError:
            raise ImportError(
                "huggingface-hub package not installed. "
                "Run: pip install huggingface-hub"
            )

    def get_provider_name(self) -> str:
        return "Huggingface"

    def analyze_image(
        self,
        image: np.ndarray,
        prompt: str = "Describe what you see in this image."
    ) -> AnalysisResult:
        import cv2
        from io import BytesIO

        start_time = time.time()

        try:
            # Encode image to bytes
            _, buffer = cv2.imencode('.jpg', image)
            image_bytes = BytesIO(buffer.tobytes())

            # Use image-to-text for captioning models
            if 'blip' in self.model.lower() or 'caption' in self.model.lower():
                result = self._client.image_to_text(
                    image=image_bytes,
                    model=self.model
                )
                content = result if isinstance(result, str) else str(result)
            else:
                # For VLM models that support text generation
                result = self._client.visual_question_answering(
                    image=image_bytes,
                    question=prompt,
                    model=self.model
                )
                content = result[0]['answer'] if result else ""

            latency = (time.time() - start_time) * 1000

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
