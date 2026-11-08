"""Application Unit Tests for Combat Duel Use Case and Service."""

import uuid
import pytest
from application.dtos.combat_duel_dto import CombatDuelRequest
from application.services.combat_duel_service import CombatDuelService
from application.use_cases.initiate_combat_duel import InitiateCombatDuelUseCase
from infrastructure.crypto.receipt_signer import ReceiptSigner
from infrastructure.gateway.mock_inference_adapter import MockInferenceAdapter
from infrastructure.persistence.database import async_session_factory, init_db
from infrastructure.persistence.mission_repository import MissionRepository
from infrastructure.sandbox.docker_runner_adapter import DockerRunnerAdapter
from infrastructure.telemetry.audit_ledger_adapter import AuditLedgerAdapter


@pytest.fixture(autouse=True)
async def setup_test_db():
    await init_db()


@pytest.fixture
def duel_components():
    runner = DockerRunnerAdapter()
    ledger = AuditLedgerAdapter()
    signer = ReceiptSigner()
    repo = MissionRepository(session_factory=async_session_factory)
    llm = MockInferenceAdapter()

    use_case = InitiateCombatDuelUseCase(
        runner=runner,
        ledger=ledger,
        signer=signer,
        repository=repo,
        llm_gateway=llm,
    )
    return use_case, llm, repo


@pytest.mark.asyncio
async def test_initiate_combat_duel_supply_chain_scenario(duel_components):
    use_case, llm, repo = duel_components
    events_received = []

    async def on_event(mid: str, stage: str, payload: dict):
        events_received.append((stage, payload))

    req = CombatDuelRequest(
        task_slug="test-supply-chain",
        scenario_preset="SUPPLY_CHAIN_BACKDOOR",
        max_rounds=3,
    )

    result = await use_case.execute(request=req, on_event=on_event)

    assert result.mission_id.startswith("msn-")
    assert result.task_slug == "test-supply-chain"
    assert result.immunity_achieved
    assert result.receipt is not None
    assert result.receipt.status == "MATHEMATICALLY_VERIFIED"
    assert len(result.rounds) == 2
    assert result.rounds[0].stage == "RED_ATTACK"
    assert result.rounds[0].intercepted
    assert result.rounds[1].stage == "BLUE_PATCH_VERIFIED"

    # Verify stage events were broadcast
    stages = [s for s, _ in events_received]
    assert "DUEL_INITIALIZED" in stages
    assert "RED_ROUND_COMPLETED" in stages
    assert "DUEL_FINISHED" in stages


@pytest.mark.asyncio
async def test_initiate_combat_duel_financial_invariant_scenario(duel_components):
    use_case, llm, repo = duel_components

    req = CombatDuelRequest(
        task_slug="test-financial",
        scenario_preset="FINANCIAL_INVARIANT_TAMPER",
        max_rounds=3,
    )

    result = await use_case.execute(request=req)
    assert result.immunity_achieved
    assert result.receipt is not None
    assert result.receipt.exit_code == 0


@pytest.mark.asyncio
async def test_combat_duel_service_pipeline(duel_components):
    use_case, llm, repo = duel_components
    broadcasted = []

    async def mock_broadcast(task_id: str, event_type: str, payload: dict):
        broadcasted.append((task_id, event_type))

    service = CombatDuelService(
        duel_use_case=use_case,
        llm_gateway=llm,
        repository=repo,
        broadcast_fn=mock_broadcast,
    )

    mission_id, run_pipeline = service.prepare_duel_pipeline(
        scenario_preset="FORK_MEMORY_EXHAUSTION",
    )
    assert mission_id.startswith("duel-")
    await run_pipeline()

    # Verify duel completed event was dispatched
    event_types = [et for _, et in broadcasted]
    assert "duel_completed" in event_types


@pytest.mark.asyncio
async def test_multi_modal_pipeline_methods(duel_components):
    use_case, llm, repo = duel_components

    async def mock_broadcast(task_id: str, event_type: str, payload: dict):
        pass

    service = CombatDuelService(
        duel_use_case=use_case,
        llm_gateway=llm,
        repository=repo,
        broadcast_fn=mock_broadcast,
    )

    # 1. Voice transcription (whisper)
    transcription = await service.transcribe_audio_command(b"test audio bytes", "cmd.wav")
    assert len(transcription) > 0
    empty_transcription = await service.transcribe_audio_command(b"", "empty.wav")
    assert empty_transcription == ""

    # 2. Voice alert synthesis (qwen-tts)
    audio_wav = await service.synthesize_voice_alert("Security alert triggered")
    assert audio_wav.startswith(b"RIFF")

    # 3. Threat diagram generation (z-image)
    diagram = await service.generate_threat_diagram("AegisSentinel attack map")
    assert "svg" in diagram or "data:image" in diagram

    # 4. Vision inspection (deepseek-vision)
    inspection = await service.inspect_visual_artifact(b"mock png bytes", "Check log image")
    assert "Analyzed image artifact" in inspection


@pytest.mark.asyncio
async def test_repository_and_service_mission_history(duel_components):
    use_case, llm, repo = duel_components
    target_id = f"msn-history-{uuid.uuid4().hex[:8]}"

    await repo.save_mission(
        mission_id=target_id,
        task_slug="history-test",
        status="VERIFIED_PASSED",
        tokens_used=50,
    )
    await repo.save_audit_event(
        mission_id=target_id,
        event_type="TEST_EVENT",
        event_hash="hash1",
        prev_hash="hash0",
        payload={"k": "v"},
    )

    fetched = await repo.get_mission(target_id)
    assert fetched is not None
    assert fetched["task_slug"] == "history-test"

    missing = await repo.get_mission("msn-nonexistent")
    assert missing is None

    history = await repo.list_recent_missions(limit=50)
    assert len(history) > 0
    assert any(m["mission_id"] == target_id for m in history)
