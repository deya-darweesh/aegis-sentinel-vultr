"""SQLAlchemy Implementation of Mission Repository."""

from datetime import datetime, timezone
from typing import List, Optional

from application.ports.i_mission_repository import IMissionRepository
from infrastructure.models.database_models import (
    AuditEventModel,
    CodePatchModel,
    ExploitPayloadModel,
    ImmunityReceiptModel,
    MissionModel,
)
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class MissionRepository(IMissionRepository):
    """Adapter implementing IMissionRepository with SQLAlchemy async sessions."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    async def save_mission(
        self,
        mission_id: str,
        task_slug: str,
        status: str,
        tokens_used: int,
    ) -> None:
        async with self._session_factory() as session:
            async with session.begin():
                stmt = select(MissionModel).where(MissionModel.id == mission_id)
                res = await session.execute(stmt)
                existing = res.scalar_one_or_none()
                if existing:
                    existing.status = status
                    existing.tokens_used = tokens_used
                    if status in ("VERIFIED_PASSED", "ASSERTION_FAILED", "CONTAINMENT_TRIGGERED"):
                        existing.completed_at = datetime.now(timezone.utc)
                else:
                    new_mission = MissionModel(
                        id=mission_id,
                        task_slug=task_slug,
                        status=status,
                        tokens_used=tokens_used,
                    )
                    session.add(new_mission)

    async def save_exploit(
        self,
        mission_id: str,
        exploit_id: str,
        round_number: int,
        attack_vector: str,
        code_payload: str,
        exit_code: int,
        intercepted: bool,
    ) -> None:
        async with self._session_factory() as session:
            async with session.begin():
                exploit = ExploitPayloadModel(
                    id=exploit_id,
                    mission_id=mission_id,
                    round_number=round_number,
                    attack_vector=attack_vector,
                    code_payload=code_payload,
                    exit_code=exit_code,
                    intercepted=intercepted,
                )
                session.add(exploit)

    async def save_patch(
        self,
        mission_id: str,
        patch_id: str,
        round_number: int,
        diff_content: str,
        ast_safe: bool,
        all_passed: bool,
    ) -> None:
        async with self._session_factory() as session:
            async with session.begin():
                patch = CodePatchModel(
                    id=patch_id,
                    mission_id=mission_id,
                    round_number=round_number,
                    diff_content=diff_content,
                    ast_safe=ast_safe,
                    all_passed=all_passed,
                )
                session.add(patch)

    async def save_receipt(
        self,
        mission_id: str,
        digest_sha256: str,
        ed25519_sig: str,
        public_key: str,
        runtime_engine: str,
        duration_ms: float,
        memory_peak_mb: float,
    ) -> None:
        async with self._session_factory() as session:
            async with session.begin():
                receipt = ImmunityReceiptModel(
                    mission_id=mission_id,
                    digest_sha256=digest_sha256,
                    ed25519_signature=ed25519_sig,
                    public_key=public_key,
                    runtime_engine=runtime_engine,
                    duration_ms=duration_ms,
                    memory_peak_mb=memory_peak_mb,
                )
                session.add(receipt)

    async def save_audit_event(
        self,
        mission_id: str,
        event_type: str,
        event_hash: str,
        prev_hash: str,
        payload: dict,
    ) -> None:
        async with self._session_factory() as session:
            async with session.begin():
                event = AuditEventModel(
                    mission_id=mission_id,
                    event_type=event_type,
                    event_hash=event_hash,
                    prev_hash=prev_hash,
                    payload=payload,
                )
                session.add(event)

    async def get_mission(self, mission_id: str) -> Optional[dict]:
        async with self._session_factory() as session:
            stmt = select(MissionModel).where(MissionModel.id == mission_id)
            res = await session.execute(stmt)
            mission = res.scalar_one_or_none()
            if not mission:
                return None
            return {
                "mission_id": mission.id,
                "task_slug": mission.task_slug,
                "status": mission.status,
                "tokens_used": mission.tokens_used,
                "created_at": mission.created_at.isoformat() if mission.created_at else None,
                "completed_at": mission.completed_at.isoformat() if mission.completed_at else None,
            }

    async def list_recent_missions(self, limit: int = 20) -> List[dict]:
        async with self._session_factory() as session:
            stmt = select(MissionModel).order_by(desc(MissionModel.created_at)).limit(limit)
            res = await session.execute(stmt)
            missions = res.scalars().all()
            return [
                {
                    "mission_id": m.id,
                    "task_slug": m.task_slug,
                    "status": m.status,
                    "tokens_used": m.tokens_used,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                    "completed_at": m.completed_at.isoformat() if m.completed_at else None,
                }
                for m in missions
            ]
