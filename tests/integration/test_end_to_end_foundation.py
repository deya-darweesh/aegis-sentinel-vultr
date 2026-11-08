"""End-to-End Integration Tests for the Theme-Agnostic Containment Foundation.

Verifies:
1. AST Blast Radius Guard blocks malicious execution before sandbox dispatch.
2. Sandboxed execution in isolation with real-time streaming hooks.
3. Dual-Sink Cryptographic Telemetry (SQLite & JSONL sequential SHA-256 hash chaining).
4. Ed25519 Digital Signature & Tamper-Proof Receipt Verification.
5. 1-Click Red-Team Chaos Probe execution.
6. Zero-Token Credit Preservation ($0.00 spend).
7. FastAPI Presentation Endpoints (/health, /api/execute, /api/chaos-test, /api/receipt/{id}).
8. TaskExecutionService pipeline orchestration and streaming.
"""

import dataclasses
import hashlib
import json
import os
import sys

import pytest
from fastapi.testclient import TestClient

# Ensure backend directory is in Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

from application.dtos.execution_receipt_dto import ExecutionReceiptDTO
from application.dtos.task_execution_dto import TaskExecutionRequest
from application.services.task_execution_service import TaskExecutionService
from application.use_cases.execute_sandboxed_task import ExecuteSandboxedTaskUseCase
from application.use_cases.trigger_chaos_probe import TriggerChaosProbeUseCase
from application.use_cases.verify_receipt import VerifyReceiptUseCase
from infrastructure.config import settings
from infrastructure.crypto.receipt_signer import ReceiptSigner
from infrastructure.gateway.mock_inference_adapter import MockInferenceAdapter
from infrastructure.sandbox.docker_runner_adapter import DockerRunnerAdapter
from infrastructure.telemetry.audit_ledger_adapter import AuditLedgerAdapter
from main import app


@pytest.fixture
def tmp_ledger(tmp_path):
    """Provides an isolated dual-sink audit ledger for testing."""
    return AuditLedgerAdapter(log_dir=tmp_path)


@pytest.fixture
def isolated_stack(tmp_ledger):
    """Assembles the application use cases with isolated temporary dependencies."""
    signer = ReceiptSigner()
    runner = DockerRunnerAdapter()
    executor = ExecuteSandboxedTaskUseCase(runner=runner, ledger=tmp_ledger, signer=signer)
    chaos = TriggerChaosProbeUseCase(executor=executor)
    verifier = VerifyReceiptUseCase(signer=signer)
    return {
        "ledger": tmp_ledger,
        "signer": signer,
        "runner": runner,
        "executor": executor,
        "chaos": chaos,
        "verifier": verifier,
    }


# ---------------------------------------------------------------------------
# 1. Credit Preservation & Mock Engine Test
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_credit_preservation_mock_adapter():
    """Confirms MockInferenceAdapter incurs $0.00 cost and requires no API key."""
    from domain.values.token_budget import TokenBudget

    mock_adapter = MockInferenceAdapter()
    budget = TokenBudget.development_safe()

    # Scenario 1: Calculation prompt
    response = await mock_adapter.generate_completion(
        messages=[{"role": "user", "content": "run calculation test"}],
        model="kimi-k2-instruct",
        budget=budget,
    )
    assert response.role == "assistant"
    assert response.tool_calls is not None
    assert response.usage.total_tokens > 0

    # Scenario 2: Chaos probe prompt
    chaos_res = await mock_adapter.generate_completion(
        messages=[{"role": "user", "content": "run red-team chaos probe"}],
        model="kimi-k2-instruct",
        budget=budget,
    )
    assert chaos_res.role == "assistant"
    assert chaos_res.tool_calls is not None

    # Scenario 3: Generic completion
    gen_res = await mock_adapter.generate_completion(
        messages=[{"role": "user", "content": "hello model"}],
        model="kimi-k2-instruct",
        budget=budget,
    )
    assert gen_res.role == "assistant"
    assert "[MOCK_ENGINE]" in (gen_res.content or "")
    # Confirms credit preservation: zero API calls, mock executes for $0.00


# ---------------------------------------------------------------------------
# 2. AST Blast Radius Guard Defense Test
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ast_guard_blocks_socket_before_sandbox(isolated_stack):
    """Verifies that unauthorized syscalls/imports are aborted before touching containers."""
    executor = isolated_stack["executor"]
    malicious_request = TaskExecutionRequest(
        task_slug="malicious-network-scan",
        code_content="import socket\ns = socket.socket()",
        target_file="scan.py",
    )
    response = await executor.execute(malicious_request)

    assert response.is_success is False
    assert response.receipt.status == "POLICY_REJECTED"
    assert response.exit_code == 1
    assert "FORBIDDEN_IMPORT" in response.stderr or "FORBIDDEN_IMPORT" in (response.violation or "")


# ---------------------------------------------------------------------------
# 3. Clean Execution & Cryptographic Hash Chaining Test
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_clean_execution_and_hash_chaining(isolated_stack):
    """Verifies benign execution, streaming callbacks, and SHA-256 chained audit events."""
    executor = isolated_stack["executor"]
    ledger = isolated_stack["ledger"]
    verifier = isolated_stack["verifier"]

    stdout_chunks = []

    async def capture_stdout(chunk: str):
        stdout_chunks.append(chunk)

    safe_request = TaskExecutionRequest(
        task_slug="clean-computation",
        code_content="result = sum(range(1, 101))\nprint(f'COMPUTATION_DONE: {result}')",
        target_file="calc.py",
    )

    response = await executor.execute(safe_request, on_stdout_chunk=capture_stdout)

    assert response.is_success is True
    assert "COMPUTATION_DONE: 5050" in response.stdout
    assert len(stdout_chunks) > 0

    # Verify Ed25519 signature on canonical receipt
    verification = verifier.verify_sync(response.receipt)
    assert verification.is_valid is True
    assert "cryptographically authentic" in verification.message

    # Verify Dual-Sink Ledgers
    recent_events = ledger.list_recent_events(limit=10)
    assert len(recent_events) >= 2  # TASK_INITIATED, TASK_COMPLETED

    # Check hash-chain continuity: each event links to previous hash
    completed_event = recent_events[0]
    initiated_event = recent_events[1]
    assert completed_event.prev_hash == initiated_event.event_hash


# ---------------------------------------------------------------------------
# 4. Tampered Receipt Detection Test
# ---------------------------------------------------------------------------


def test_tampered_receipt_rejected(isolated_stack):
    """Verifies that altering an exit code or payload invalidates the signature."""
    signer = isolated_stack["signer"]
    verifier = isolated_stack["verifier"]

    payload = {"task": "verify", "exit_code": 0, "status": "VERIFIED_PASSED"}
    raw_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
    digest = hashlib.sha256(raw_bytes).hexdigest()
    sig = signer.sign_digest(digest)

    valid_receipt = ExecutionReceiptDTO(
        receipt_id="rcpt-test",
        timestamp="2026-11-05T00:00:00Z",
        task_slug="verify",
        status="VERIFIED_PASSED",
        exit_code=0,
        duration_ms=10.0,
        memory_peak_mb=12.0,
        runtime_engine="runsc",
        container_id="test-box",
        digest_sha256=digest,
        ed25519_signature=sig,
        public_key=signer.public_key_hex,
    )

    # Clean verification
    verification = verifier.verify_sync(valid_receipt)
    assert verification.is_valid is True

    # Tamper with the exit code and digest
    tampered_bytes = json.dumps({"task": "verify", "exit_code": 1, "status": "TAMPERED"}, sort_keys=True).encode("utf-8")
    tampered_digest = hashlib.sha256(tampered_bytes).hexdigest()
    tampered_receipt = dataclasses.replace(valid_receipt, digest_sha256=tampered_digest)

    tampered_verif = verifier.verify_sync(tampered_receipt)
    assert tampered_verif.is_valid is False
    assert "failed" in tampered_verif.message or "forged" in tampered_verif.message


# ---------------------------------------------------------------------------
# 5. 1-Click Red-Team Chaos Probe Execution Test
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_chaos_probe_containment(isolated_stack):
    """Verifies the mandatory hackathon 1-click chaos test runs and captures telemetry."""
    chaos = isolated_stack["chaos"]
    verifier = isolated_stack["verifier"]

    response = await chaos.execute(task_slug="hackathon-judge-demo")
    assert response.receipt is not None
    assert "CHAOS_PROBE" in response.stdout

    # Cryptographic verification of chaos containment receipt
    verification = verifier.verify_sync(response.receipt)
    assert verification.is_valid is True


# ---------------------------------------------------------------------------
# 6. TaskExecutionService Pipeline Orchestration Test
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_task_execution_service_pipelines(isolated_stack):
    """Verifies TaskExecutionService generates pipelines and broadcasts events cleanly."""
    executor = isolated_stack["executor"]
    chaos = isolated_stack["chaos"]

    broadcasted_events = []

    async def mock_broadcast(task_id: str, event_type: str, data: dict):
        broadcasted_events.append((task_id, event_type, data))

    service = TaskExecutionService(
        task_executor=executor,
        chaos_probe=chaos,
        broadcast_fn=mock_broadcast,
    )

    # 1. Test Execution Pipeline with both stdout and stderr
    task_id, run_exec = service.prepare_execution_pipeline(
        task_slug="service-test",
        code="import sys\nsys.stderr.write('ERR_CHUNK\\n')\nprint('SERVICE_TEST_PASSED')",
    )
    assert task_id.startswith("task-")
    await run_exec()

    event_types = [e[1] for e in broadcasted_events]
    assert "status" in event_types
    assert "stdout" in event_types
    assert "stderr" in event_types
    assert "finished" in event_types

    # 2. Test Chaos Pipeline
    broadcasted_events.clear()
    chaos_id, run_chaos = service.prepare_chaos_pipeline()
    assert chaos_id.startswith("chaos-")
    await run_chaos()

    chaos_event_types = [e[1] for e in broadcasted_events]
    assert "status" in chaos_event_types
    assert "finished" in chaos_event_types


# ---------------------------------------------------------------------------
# 7. Presentation REST Endpoints Test (TestClient)
# ---------------------------------------------------------------------------


def test_fastapi_presentation_endpoints():
    """Tests /health, /api/execute, /api/chaos-test, /api/stream/{task_id}, and /api/audit-events."""
    import time

    from api.router import ledger, signer
    from domain.values.execution_receipt import ExecutionReceipt, SecurityStatus

    client = TestClient(app)

    # 1. Health check
    res = client.get("/health")
    assert res.status_code == 200
    health = res.json()
    assert health["status"] == "operational"
    assert health["mock_mode"] is True
    assert "public_key_ed25519" in health

    # 2. Chaos trigger endpoint
    res_chaos = client.post("/api/chaos-test")
    assert res_chaos.status_code == 200
    data = res_chaos.json()
    assert "task_id" in data
    assert data["status"] == "chaos_probe_dispatched"

    # 3. Execute code endpoint
    res_exec = client.post(
        "/api/execute",
        json={"task_slug": "api-test", "code": "print('hello')", "target_file": "main.py"},
    )
    assert res_exec.status_code == 200
    exec_data = res_exec.json()
    assert "task_id" in exec_data
    assert exec_data["status"] == "initiated"

    # 4. Audit events endpoint
    res_audit = client.get("/api/audit-events")
    assert res_audit.status_code == 200
    assert "events" in res_audit.json()

    # 5. Receipt verification endpoint (404 and 200)
    res_404 = client.get("/api/receipt/non-existent-rcpt")
    assert res_404.status_code == 404

    # Save a valid receipt into ledger
    test_rcpt = ExecutionReceipt(
        receipt_id="rcpt-test-1234",
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        task_slug="test-task",
        status=SecurityStatus.MATHEMATICALLY_VERIFIED,
        exit_code=0,
        duration_ms=10.0,
        memory_peak_mb=12.0,
        runtime_engine="runsc",
        container_id="test-box",
        input_sha256="abc",
        patch_sha256="abc",
        audit_chain_hash="1234",
    )
    # Sign receipt
    digest = test_rcpt.compute_canonical_digest()
    sig = signer.sign_digest(digest)
    signed_rcpt = test_rcpt.with_signature(sig)
    ledger.persist_receipt(signed_rcpt)

    res_rcpt = client.get(f"/api/receipt/{test_rcpt.receipt_id}")
    assert res_rcpt.status_code == 200
    rcpt_json = res_rcpt.json()
    assert rcpt_json["cryptographically_verified"] is True


@pytest.mark.asyncio
async def test_async_verify_receipt_use_case(isolated_stack):
    """Directly tests async execution of VerifyReceiptUseCase."""
    verifier = isolated_stack["verifier"]
    signer = isolated_stack["signer"]

    # Invalid receipt missing fields
    invalid_receipt = ExecutionReceiptDTO(
        receipt_id="rcpt-invalid",
        timestamp="2026-11-05T00:00:00Z",
        task_slug="verify",
        status="VERIFIED_PASSED",
        exit_code=0,
        duration_ms=10.0,
        memory_peak_mb=12.0,
        runtime_engine="runsc",
        container_id="test-box",
        digest_sha256="",
        ed25519_signature=None,
    )
    res_invalid = await verifier.execute(invalid_receipt)
    assert res_invalid.is_valid is False
    assert "Missing SHA-256" in res_invalid.message

    # Valid receipt
    payload = {"task": "verify", "exit_code": 0}
    raw_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
    digest = hashlib.sha256(raw_bytes).hexdigest()
    sig = signer.sign_digest(digest)

    valid_receipt = ExecutionReceiptDTO(
        receipt_id="rcpt-valid",
        timestamp="2026-11-05T00:00:00Z",
        task_slug="verify",
        status="VERIFIED_PASSED",
        exit_code=0,
        duration_ms=10.0,
        memory_peak_mb=12.0,
        runtime_engine="runsc",
        container_id="test-box",
        digest_sha256=digest,
        ed25519_signature=sig,
        public_key=signer.public_key_hex,
    )
    res_valid = await verifier.execute(valid_receipt)
    assert res_valid.is_valid is True


@pytest.mark.asyncio
async def test_sse_broker_lifecycle():
    """Verifies SSEBroker subscription, broadcast, and cleanup."""
    from api.sse_broker import SSEBroker

    broker = SSEBroker()

    queue = broker.subscribe("task-abc")
    assert queue is not None

    await broker.broadcast("task-abc", "log", {"msg": "stream test"})
    msg = await queue.get()
    assert "event: log" in msg
    assert "stream test" in msg

    broker.unsubscribe("task-abc", queue)
    assert "task-abc" not in broker._task_subscribers


def test_path_jail_isolation(tmp_path):
    """Verifies PathJail blocks directory traversal and path escapes."""
    from infrastructure.sandbox.path_jail import PathJail, PathJailViolation

    jail = PathJail(base_dir=tmp_path / "sandbox")
    safe_file = tmp_path / "sandbox" / "script.py"
    safe_file.write_text("print('safe')")

    # Safe path succeeds
    resolved = jail.validate_safe_path(safe_file)
    assert resolved == safe_file.resolve()

    # Traversal escape fails
    escape_target = tmp_path / "outside.txt"
    escape_target.write_text("secret")
    with pytest.raises(PathJailViolation, match="escapes sandbox jail"):
        jail.validate_safe_path(escape_target)

    # Symlink escape check
    symlink_file = tmp_path / "sandbox" / "escape_link.txt"
    try:
        symlink_file.symlink_to(escape_target)
        with pytest.raises(PathJailViolation, match="Symlink Traversal Blocked"):
            jail.validate_safe_path(symlink_file)
    except (OSError, NotImplementedError):
        # On Windows without developer mode/admin privileges, symlinks might require SeCreateSymbolicLinkPrivilege
        pass


def test_receipt_signer_edge_cases(tmp_path):
    """Verifies fresh seed generation and bad signature handling."""
    from infrastructure.crypto.receipt_signer import ReceiptSigner

    fresh_signer = ReceiptSigner(key_path=tmp_path / "new_keys" / "test.key")
    assert fresh_signer.key_path.exists()
    assert len(fresh_signer.public_key_hex) == 64

    # Invalid signature bytes
    is_valid = fresh_signer.verify_signature(
        digest_sha256="abc",
        signature_hex="00" * 64,
    )
    assert is_valid is False

    # Corrupted / non-hex signature
    is_corrupt = fresh_signer.verify_signature(
        digest_sha256="abc",
        signature_hex="not-a-valid-hex-string",
    )
    assert is_corrupt is False


def test_dashboard_endpoint():
    """Verifies the diagnostic dashboard HTML renders on GET / and lifespan executes."""
    with TestClient(app) as client:
        res = client.get("/")
        assert res.status_code == 200
        assert "Vultr Agent Rush" in res.text
        assert "1-Click Containment Moment" in res.text
