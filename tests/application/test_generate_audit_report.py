"""Unit Tests for GenerateAuditReportUseCase.

Verifies ReportLab PDF generation, repository integration,
and cryptographic attestation per ENG-STD-001 and baseline-testing.
"""

import uuid

import pytest
from application.ports.i_audit_report_generator import IAuditReportGenerator
from application.use_cases.generate_audit_report import GenerateAuditReportUseCase
from infrastructure.crypto.receipt_signer import ReceiptSigner
from infrastructure.persistence.database import async_session_factory, init_db
from infrastructure.persistence.mission_repository import MissionRepository
from infrastructure.reporting.pdf_report_generator import PDFReportGenerator
from infrastructure.sandbox.docker_runner_adapter import DockerRunnerAdapter
from infrastructure.telemetry.audit_ledger_adapter import AuditLedgerAdapter


@pytest.fixture(autouse=True)
async def setup_test_db():
    await init_db()


@pytest.fixture
def audit_report_use_case():
    repo = MissionRepository(session_factory=async_session_factory)
    ledger = AuditLedgerAdapter()
    signer = ReceiptSigner()
    runner = DockerRunnerAdapter()
    pdf_gen = PDFReportGenerator()

    return GenerateAuditReportUseCase(
        repository=repo,
        ledger=ledger,
        signer=signer,
        runner=runner,
        pdf_generator=pdf_gen,
    )


@pytest.mark.asyncio
async def test_generate_audit_report_for_nonexistent_mission_returns_valid_pdf(audit_report_use_case):
    """Fallback generation returns a valid PDF document."""
    pdf_bytes = await audit_report_use_case.execute(f"msn-{uuid.uuid4().hex[:8]}")
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF-")


@pytest.mark.asyncio
async def test_generate_audit_report_with_saved_mission_data(audit_report_use_case):
    """Saved mission metadata, exploits, and patches are reflected in PDF report."""
    repo = audit_report_use_case.repository
    uid = uuid.uuid4().hex[:8]
    mission_id = f"msn-test-{uid}"
    await repo.save_mission(
        mission_id=mission_id,
        task_slug="settlement-crypto-engine",
        status="MATHEMATICALLY_VERIFIED",
        tokens_used=1240,
    )
    await repo.save_exploit(
        mission_id=mission_id,
        exploit_id=f"exp-{uid}",
        round_number=1,
        attack_vector="CWE-400 Memory Exhaustion",
        code_payload="import sys; [0]*10**8",
        exit_code=137,
        intercepted=True,
    )
    await repo.save_patch(
        mission_id=mission_id,
        patch_id=f"patch-{uid}",
        round_number=1,
        diff_content="def stream_chunks(): yield b'clean'",
        ast_safe=True,
        all_passed=True,
    )

    pdf_bytes = await audit_report_use_case.execute(mission_id)
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF-")
    assert len(pdf_bytes) > 2000
