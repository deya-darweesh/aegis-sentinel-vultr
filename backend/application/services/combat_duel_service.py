"""Combat Duel Application Service.

Encapsulates background duel execution pipelines, event dispatching,
and multi-modal operations away from the HTTP presentation boundary.
"""

import uuid
from typing import Awaitable, Callable, Coroutine, List, Optional, Tuple

from application.dtos.combat_duel_dto import CombatDuelRequest, CombatDuelResultDTO
from application.ports.i_llm_gateway import ILLMGateway
from application.ports.i_mission_repository import IMissionRepository
from application.use_cases.initiate_combat_duel import InitiateCombatDuelUseCase


class CombatDuelService:
    """Application Service for managing autonomous Maker-Breaker duels and multi-modal assets."""

    def __init__(
        self,
        duel_use_case: InitiateCombatDuelUseCase,
        llm_gateway: ILLMGateway,
        repository: IMissionRepository,
        broadcast_fn: Callable[[str, str, dict], Awaitable[None]],
    ):
        self.duel_use_case = duel_use_case
        self.llm = llm_gateway
        self.repository = repository
        self.broadcast = broadcast_fn

    def prepare_duel_pipeline(
        self,
        scenario_preset: str,
        target_code: Optional[str] = None,
        max_rounds: int = 3,
    ) -> Tuple[str, Callable[[], Coroutine[None, None, None]]]:
        """Prepares an asynchronous duel pipeline with streaming event callbacks."""
        mission_id = f"duel-{uuid.uuid4().hex[:8]}"

        async def run_pipeline():
            async def on_event(task_id: str, event_type: str, payload: dict):
                await self.broadcast(task_id, event_type, payload)

            req = CombatDuelRequest(
                task_slug=f"sentinel-{mission_id}",
                scenario_preset=scenario_preset,
                target_code=target_code,
                max_rounds=max_rounds,
            )
            result = await self.duel_use_case.execute(request=req, on_event=on_event)
            await self.broadcast(
                mission_id,
                "duel_completed",
                {
                    "mission_id": result.mission_id,
                    "immunity_achieved": result.immunity_achieved,
                    "summary": result.summary,
                    "receipt": result.receipt.to_dict() if result.receipt else None,
                },
            )

        return mission_id, run_pipeline

    async def transcribe_audio_command(self, audio_bytes: bytes, filename: str) -> str:
        """Transcribes voice command using whisper-large-v3-turbo."""
        return await self.llm.transcribe_audio(audio_bytes, filename)

    async def synthesize_voice_alert(self, text: str) -> bytes:
        """Generates voice alarm using qwen3-tts-12hz-1.7b."""
        return await self.llm.synthesize_speech(text)

    async def generate_threat_diagram(self, prompt: str) -> str:
        """Generates attack topology diagram using z-image-turbo."""
        return await self.llm.generate_threat_diagram(prompt)

    async def inspect_visual_artifact(self, image_bytes: bytes, prompt: str) -> str:
        """Inspects image using deepseek-v4.1-flash-1017 vision mode."""
        return await self.llm.inspect_image(image_bytes, prompt)

    async def get_recent_missions(self, limit: int = 20) -> List[dict]:
        """Queries the persistent mission repository."""
        return await self.repository.list_recent_missions(limit=limit)
