"""Unit Tests for ExecuteSecOpsCopilotUseCase.

Tests intent classification, duel scheduling, and cryptographic attestation.
"""

import pytest
from application.dtos.secops_copilot_dto import SecOpsCopilotRequest
from application.services.combat_duel_service import CombatDuelService
from application.use_cases.execute_secops_copilot import ExecuteSecOpsCopilotUseCase
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
def copilot_use_case():
    runner = DockerRunnerAdapter()
    ledger = AuditLedgerAdapter()
    signer = ReceiptSigner()
    repo = MissionRepository(session_factory=async_session_factory)
    llm = MockInferenceAdapter()

    duel_use_case = InitiateCombatDuelUseCase(
        runner=runner,
        ledger=ledger,
        signer=signer,
        repository=repo,
        llm_gateway=llm,
    )
    combat_service = CombatDuelService(
        duel_use_case=duel_use_case,
        llm_gateway=llm,
        repository=repo,
    )

    return ExecuteSecOpsCopilotUseCase(
        combat_duel_service=combat_service,
        ledger=ledger,
        signer=signer,
    )


@pytest.mark.asyncio
async def test_copilot_memory_intent_classification(copilot_use_case):
    """Memory exhaustion keywords route to FORK_MEMORY_EXHAUSTION."""
    dispatched_tasks = []

    def mock_schedule(fn):
        dispatched_tasks.append(fn)

    req = SecOpsCopilotRequest(
        message="Simulate recursive fork bomb memory exhaustion exploit",
    )
    result = await copilot_use_case.execute(req, schedule_background_task=mock_schedule)

    assert result.scenario == "FORK_MEMORY_EXHAUSTION"
    assert "7.5" in result.cvss_score
    assert result.status == "IMMUNIZED"
    assert len(dispatched_tasks) == 1
    assert result.pdf_report_url.startswith("/api/report/pdf/")
    assert len(result.ed25519_signature) > 30


@pytest.mark.asyncio
async def test_copilot_finance_intent_classification(copilot_use_case):
    """Finance/ledger keywords route to FINANCIAL_INVARIANT_BUG."""
    dispatched_tasks = []

    def mock_schedule(fn):
        dispatched_tasks.append(fn)

    req = SecOpsCopilotRequest(
        message="Analyze financial settlement engine for decimal precision drift",
    )
    result = await copilot_use_case.execute(req, schedule_background_task=mock_schedule)

    assert result.scenario == "FINANCIAL_INVARIANT_BUG"
    assert "8.2" in result.cvss_score
    assert result.status == "IMMUNIZED"
    assert len(dispatched_tasks) == 1


@pytest.mark.asyncio
async def test_copilot_supply_chain_intent_classification(copilot_use_case):
    """Payment/secret keywords route to SUPPLY_CHAIN_LEAK."""
    dispatched_tasks = []

    def mock_schedule(fn):
        dispatched_tasks.append(fn)

    req = SecOpsCopilotRequest(
        message="Audit payment gateway for outbound socket data exfiltration",
        code_snippet="def process(): pass",
    )
    result = await copilot_use_case.execute(req, schedule_background_task=mock_schedule)

    assert result.scenario == "SUPPLY_CHAIN_LEAK"
    assert "9.8" in result.cvss_score
    assert result.status == "IMMUNIZED"
    assert len(dispatched_tasks) == 1
    assert "### 🛡️ AegisSentinel Security Audit" in result.reply
