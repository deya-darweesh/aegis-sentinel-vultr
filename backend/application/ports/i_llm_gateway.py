"""LLM Gateway Port Protocol.

Defines the interface for querying language models within strict token budgets.
"""

from typing import Dict, List, Optional, Protocol

from application.dtos.llm_completion_dto import LLMCompletionDTO
from domain.values.token_budget import TokenBudget


class ILLMGateway(Protocol):
    """Protocol for invoking Vultr Serverless Inference or local mock models."""

    async def generate_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        budget: TokenBudget,
        tools: Optional[List[dict]] = None,
        temperature: float = 0.2,
    ) -> LLMCompletionDTO:
        """Issues an inference request honoring token budget limits."""
        ...

    async def transcribe_audio(self, audio_bytes: bytes, filename: str) -> str:
        """Transcribes spoken audio into text using whisper-large-v3-turbo."""
        ...

    async def synthesize_speech(self, text: str) -> bytes:
        """Synthesizes text into audio bytes using qwen3-tts-12hz-1.7b."""
        ...

    async def generate_threat_diagram(self, prompt: str) -> str:
        """Generates architectural threat diagram using z-image-turbo."""
        ...

    async def inspect_image(self, image_bytes: bytes, prompt: str) -> str:
        """Inspects image screenshot or log graphic using vision model."""
        ...
