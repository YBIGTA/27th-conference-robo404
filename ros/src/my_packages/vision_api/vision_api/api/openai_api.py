"""OpenAI GPT-4 Vision API implementation."""

import time
import numpy as np
from .base import VisionAPIBase, AnalysisResult


class OpenAIVisionAPI(VisionAPIBase):
    """OpenAI GPT-4 Vision API implementation."""

    DEFAULT_MODEL = "gpt-4o"

    def __init__(self, api_key: str, model: str = None):
        super().__init__(api_key, model or self.DEFAULT_MODEL)

    def _validate_credentials(self) -> None:
        """Initialize OpenAI client."""
        try:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")

    def get_provider_name(self) -> str:
        return "OpenAI"

    def analyze_image(
        self,
        image: np.ndarray,
        prompt: str = "Describe what you see in this image."
    ) -> AnalysisResult:
        start_time = time.time()

        try:
            base64_image = self._encode_image_base64(image)

            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )

            latency = (time.time() - start_time) * 1000
            content = response.choices[0].message.content

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
