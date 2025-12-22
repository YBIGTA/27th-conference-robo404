"""Vision API abstraction layer."""

from typing import Optional
from .base import VisionAPIBase, AnalysisResult
from .openai_api import OpenAIVisionAPI
from .gemini_api import GeminiVisionAPI
from .huggingface_api import HuggingFaceVisionAPI


class VisionAPIFactory:
    """Vision API factory class."""

    _providers = {
        'openai': OpenAIVisionAPI,
        'gemini': GeminiVisionAPI,
        'huggingface': HuggingFaceVisionAPI,
    }

    @classmethod
    def create(
        cls,
        provider: str,
        api_key: str,
        model: Optional[str] = None
    ) -> VisionAPIBase:
        """
        Create API instance.

        Args:
            provider: 'openai', 'gemini', 'huggingface'
            api_key: API key
            model: Model name (optional)

        Returns:
            VisionAPIBase instance
        """
        provider_lower = provider.lower()
        if provider_lower not in cls._providers:
            raise ValueError(
                f"Unknown provider: {provider}. "
                f"Available: {list(cls._providers.keys())}"
            )

        return cls._providers[provider_lower](api_key, model)

    @classmethod
    def available_providers(cls) -> list:
        """Get available API providers."""
        return list(cls._providers.keys())


__all__ = [
    'VisionAPIBase',
    'AnalysisResult',
    'VisionAPIFactory',
    'OpenAIVisionAPI',
    'GeminiVisionAPI',
    'HuggingFaceVisionAPI',
]
