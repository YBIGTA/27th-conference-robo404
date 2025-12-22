"""Base class for Vision API implementations."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List
import base64
import cv2
import numpy as np


@dataclass
class AnalysisResult:
    """API analysis result data class."""
    success: bool
    description: str
    detected_objects: List[str]
    confidence: float
    raw_response: Optional[str] = None
    error_message: Optional[str] = None
    latency_ms: float = 0.0


class VisionAPIBase(ABC):
    """Abstract base class for Vision APIs."""

    def __init__(self, api_key: str, model: str = None):
        self.api_key = api_key
        self.model = model
        self._validate_credentials()

    @abstractmethod
    def _validate_credentials(self) -> None:
        """Validate API credentials."""
        pass

    @abstractmethod
    def analyze_image(
        self,
        image: np.ndarray,
        prompt: str = "Describe what you see in this image."
    ) -> AnalysisResult:
        """
        Analyze image.

        Args:
            image: BGR numpy array (OpenCV format)
            prompt: Analysis prompt

        Returns:
            AnalysisResult
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Get API provider name."""
        pass

    def _encode_image_base64(self, image: np.ndarray) -> str:
        """Encode image to base64 string."""
        _, buffer = cv2.imencode('.jpg', image)
        return base64.b64encode(buffer).decode('utf-8')
