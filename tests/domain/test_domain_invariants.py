"""Unit tests verifying all Domain-Driven Design (DDD) security invariants."""

import os
import sys

import pytest

# Add backend to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))

from domain.aggregates.verification_mission import MissionDomainError, MissionStatus, VerificationMission
from domain.entities.code_patch import CodePatch
from domain.entities.test_suite import TestSuite
from domain.services.ast_blast_radius_guard import ASTBlastRadiusGuard
from domain.services.maker_breaker_arbiter import MakerBreakerArbiter
from domain.services.secret_scrubber import SecretScrubber
from domain.values.containment_policy import ContainmentPolicy, SecurityViolationError
from domain.values.security_violation import SecurityViolation, ViolationType
from domain.values.token_budget import TokenBudget, TokenBudgetExceededError

# ---------------------------------------------------------------------------
# 1. Containment Policy Invariant Tests
# ---------------------------------------------------------------------------


def test_valid_containment_policy_creation():
    policy = ContainmentPolicy.strict_airgap()
    assert policy.memory_limit_mb == 256
    assert policy.cpu_limit == 0.5
    assert policy.pids_limit == 64
    assert policy.network_enabled is False
    assert policy.read_only_root is True
    assert policy.user_uid == 65534


def test_reject_excessive_memory():
    with pytest.raises(SecurityViolationError, match="Memory limit"):
        ContainmentPolicy(memory_limit_mb=1024)  # Above 512MB limit


def test_reject_root_execution():
    with pytest.raises(SecurityViolationError, match="Container execution as root"):
        ContainmentPolicy(user_uid=0)


def test_reject_writeable_root():
    with pytest.raises(SecurityViolationError, match="Root filesystem must be mounted read-only"):
        ContainmentPolicy(read_only_root=False)


def test_reject_fork_bomb_capacity():
    with pytest.raises(SecurityViolationError, match="PIDs limit"):
        ContainmentPolicy(pids_limit=256)


# ---------------------------------------------------------------------------
# 2. Token Budget & Credit Conservation Invariant Tests
# ---------------------------------------------------------------------------


def test_token_budget_preserves_credits():
    budget = TokenBudget.development_safe()
    assert budget.max_tokens_per_call == 512
    assert budget.max_tokens_per_mission == 2048

    # Ensure token clamping works
    clamped = budget.validate_request(2048)
    assert clamped == 512

    # Estimated cost is fractions of a cent
    cost = budget.estimate_mission_cost_usd(2048)
    assert cost < 0.01


def test_reject_excessive_token_request():
    with pytest.raises(TokenBudgetExceededError):
        TokenBudget(max_tokens_per_call=4096)


# ---------------------------------------------------------------------------
# 3. AST Blast Radius Guard Tests
# ---------------------------------------------------------------------------


def test_ast_guard_blocks_socket_import():
    guard = ASTBlastRadiusGuard()
    malicious_code = """
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('1.1.1.1', 80))
"""
    result = guard.inspect_code(malicious_code)
    assert result.is_safe is False
    assert any("FORBIDDEN_IMPORT" in v and "socket" in v for v in result.violations)


def test_ast_guard_blocks_eval_exec():
    guard = ASTBlastRadiusGuard()
    malicious_code = 'eval(\'__import__("os").system("whoami")\')'
    result = guard.inspect_code(malicious_code)
    assert result.is_safe is False
    assert any("FORBIDDEN_CALL" in v for v in result.violations)


def test_ast_guard_approves_safe_numerical_code():
    guard = ASTBlastRadiusGuard()
    safe_code = """
import math
import json

def calculate_stats(values):
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return {"mean": mean, "std": math.sqrt(variance)}
"""
    result = guard.inspect_code(safe_code)
    assert result.is_safe is True
    assert len(result.violations) == 0


# ---------------------------------------------------------------------------
# 4. Secret Scrubber Tests (Pillar 2: Secret Hygiene)
# ---------------------------------------------------------------------------


def test_secret_scrubber_sanitizes_text():
    scrubber = SecretScrubber()
    dirty_text = "Here is my token: vultr_inference_key='vultr_secret_abc1234567890123' and sk-12345678901234567890"
    cleaned = scrubber.sanitize_text(dirty_text)
    assert "vultr_secret" not in cleaned
    assert "[REDACTED_BY_SECRET_HYGIENE_PILLAR]" in cleaned


def test_secret_scrubber_filters_environment():
    scrubber = SecretScrubber()
    host_env = {
        "PATH": "/usr/bin:/bin",
        "HOME": "/workspace",
        "VULTR_INFERENCE_API_KEY": "super_secret_vultr_token",
        "DATABASE_URL": "postgres://user:pass@localhost/db",
    }
    sanitized = scrubber.filter_environment(host_env)
    assert "VULTR_INFERENCE_API_KEY" not in sanitized
    assert "DATABASE_URL" not in sanitized
    assert "PATH" in sanitized


# ---------------------------------------------------------------------------
# 5. Maker-Breaker Arbiter Tests
# ---------------------------------------------------------------------------


def test_maker_breaker_evaluates_exit_code_zero():
    arbiter = MakerBreakerArbiter()
    patch = CodePatch(patch_id="p1", target_file="algo.py", code_content="def add(a, b): return a + b", ast_safe=True)

    std_suite = TestSuite(suite_id="s1", test_code="assert add(1, 2) == 3")
    std_suite.record_result("test_add", passed=True, duration_ms=2.0)

    verdict = arbiter.evaluate_round(
        patch=patch,
        standard_suite=std_suite,
        adversarial_suite=None,
        exit_code=0,
        stderr="",
    )
    assert verdict.is_ready_for_release is True
    assert verdict.synthesizer_passed_standard is True


def test_maker_breaker_catches_adversarial_vulnerability():
    arbiter = MakerBreakerArbiter()
    patch = CodePatch(patch_id="p1", target_file="algo.py", code_content="def div(a, b): return a / b", ast_safe=True)

    std_suite = TestSuite(suite_id="s1", test_code="assert div(4, 2) == 2")
    std_suite.record_result("test_div_normal", passed=True, duration_ms=1.5)

    # Breaker injects b=0
    adv_suite = TestSuite(suite_id="s2", test_code="assert div(4, 0)", is_adversarial=True)
    adv_suite.record_result("test_zero_division", passed=False, duration_ms=1.0, error_message="ZeroDivisionError")

    verdict = arbiter.evaluate_round(
        patch=patch,
        standard_suite=std_suite,
        adversarial_suite=adv_suite,
        exit_code=0,
        stderr="",
    )
    assert verdict.is_ready_for_release is False
    assert verdict.breaker_found_vulnerability is True
    assert "ZeroDivisionError" in verdict.remediation_prompt or "test_zero_division" in verdict.remediation_prompt


# ---------------------------------------------------------------------------
# 6. Aggregate Root Invariant Tests (VerificationMission)
# ---------------------------------------------------------------------------


def test_mission_enforces_golden_rule():
    mission = VerificationMission.create(
        task_slug="reconcile-tx",
        target_file="tx.py",
    )
    assert mission.status == MissionStatus.INITIALIZED

    # Attach AST-validated patch
    patch = CodePatch(patch_id="p1", target_file="tx.py", code_content="x = 42", ast_safe=True)
    mission.attach_patch(patch)
    assert len(mission.audit_chain) == 1

    # Deterministic exit code 0 marks PASSED
    mission.record_execution_outcome(exit_code=0, stdout="OK", stderr="", duration_ms=45.0)
    assert mission.status == MissionStatus.VERIFIED_PASSED

    # Generate verifiable receipt
    receipt = mission.produce_receipt(audit_chain_hash="feedbeef1234567890")
    assert receipt.status.value == "MATHEMATICALLY_VERIFIED"
    assert receipt.exit_code == 0
    assert len(receipt.digest_sha256 if hasattr(receipt, "digest_sha256") else receipt.compute_canonical_digest()) == 64


def test_mission_records_containment_violation():
    mission = VerificationMission.create(
        task_slug="rogue-task",
        target_file="probe.py",
    )
    violation = SecurityViolation(
        violation_type=ViolationType.FILESYSTEM_WRITE_BLOCKED,
        raw_message="Read-only file system: /etc/shadow",
        exit_code=1,
    )
    mission.record_execution_outcome(exit_code=1, stdout="", stderr="Read-only file system", duration_ms=10.0, violation=violation)

    assert mission.status == MissionStatus.CONTAINMENT_TRIGGERED
    receipt = mission.produce_receipt(audit_chain_hash="1122334455")
    assert receipt.status.value == "CONTAINMENT_TRIGGERED"
    assert receipt.violation is not None


def test_mission_rejects_unsafe_patch_without_chaos_flag():
    mission = VerificationMission.create(task_slug="test-unsafe", target_file="main.py")
    unsafe_patch = CodePatch(patch_id="p2", target_file="main.py", code_content="import socket", ast_safe=False)
    with pytest.raises(MissionDomainError, match="AST safety"):
        mission.attach_patch(unsafe_patch)


def test_mission_lifecycle_suites_and_sessions():
    from domain.entities.sandbox_session import SandboxSession, SessionState

    mission = VerificationMission.create(task_slug="test-lifecycle", target_file="main.py")

    # Attach standard test suite
    std_suite = TestSuite(suite_id="std1", test_code="assert 1 == 1", is_adversarial=False)
    mission.attach_test_suite(std_suite)
    assert mission.status == MissionStatus.IN_QUARANTINE

    # Attach adversarial test suite
    adv_suite = TestSuite(suite_id="adv1", test_code="assert 1 == 0", is_adversarial=True)
    mission.attach_test_suite(adv_suite)
    assert mission.status == MissionStatus.ADVERSARIAL_CHALLENGE

    # Bind sandbox session
    session = SandboxSession(
        session_id="sess-1",
        container_name="test-box",
        policy=ContainmentPolicy.strict_airgap(),
    )
    mission.bind_sandbox_session(session)
    assert mission.active_session is not None

    # Consume tokens within budget
    mission.consume_tokens(500)
    assert mission.tokens_consumed == 500

    # Consume tokens exceeding budget
    with pytest.raises(MissionDomainError, match="Token budget exceeded"):
        mission.consume_tokens(50000)
    assert mission.status == MissionStatus.POLICY_REJECTED

    # Deterministic failures and retry threshold (max_attempts = 3)
    mission.record_execution_outcome(exit_code=1, stdout="", stderr="AssertionError", duration_ms=15.0)
    assert mission.status == MissionStatus.IN_QUARANTINE  # First attempt triggers self healing

    mission.record_execution_outcome(exit_code=1, stdout="", stderr="AssertionError", duration_ms=15.0)
    assert mission.status == MissionStatus.IN_QUARANTINE  # Second attempt triggers self healing

    # Third failure reaches max_attempts (3)
    mission.record_execution_outcome(exit_code=1, stdout="", stderr="AssertionError", duration_ms=15.0)
    assert mission.status == MissionStatus.ASSERTION_FAILED
    failed_receipt = mission.produce_receipt(audit_chain_hash="deadbeef")
    assert failed_receipt.status.value == "ASSERTION_FAILED"


def test_sandbox_session_lifecycle():
    from domain.entities.sandbox_session import SandboxSession, SessionState

    session = SandboxSession(
        session_id="sess-life",
        container_name="cnt-life",
        policy=ContainmentPolicy.strict_airgap(),
    )
    assert session.state == SessionState.PROVISIONING
    assert session.is_active is False

    session.transition_to(SessionState.READY)
    assert session.state == SessionState.READY
    assert session.is_active is True

    session.transition_to(SessionState.EXECUTING)
    assert session.state == SessionState.EXECUTING

    # Illegal transition
    with pytest.raises(ValueError, match="Illegal state transition"):
        session.transition_to(SessionState.PROVISIONING)

    violation = SecurityViolation(
        violation_type=ViolationType.NETWORK_EGRESS_BLOCKED,
        raw_message="No network",
        exit_code=1,
    )
    session.record_violation(violation)
    assert session.state == SessionState.CONTAINED
    assert len(session.violations) == 1

    session.transition_to(SessionState.TERMINATED)
    assert session.state == SessionState.TERMINATED
    assert session.lifetime_seconds >= 0.0


def test_ast_guard_syntax_error():
    guard = ASTBlastRadiusGuard()
    result = guard.inspect_code("def broken_syntax(:\n  return 1")
    assert result.is_safe is False
    assert any("SYNTAX_ERROR" in v for v in result.violations)


def test_containment_policy_invalid_bounds():
    with pytest.raises(SecurityViolationError, match="CPU limit"):
        ContainmentPolicy(cpu_limit=4.0)

    with pytest.raises(SecurityViolationError, match="Timeout"):
        ContainmentPolicy(timeout_seconds=120)

    with pytest.raises(SecurityViolationError, match="capabilities"):
        ContainmentPolicy(drop_all_capabilities=False)

    with pytest.raises(SecurityViolationError, match="Privilege escalation"):
        ContainmentPolicy(no_new_privileges=False)

    chaos = ContainmentPolicy.chaos_stress_test()
    assert chaos.is_chaos_probe is True


def test_code_patch_metadata_and_validation():
    patch = CodePatch(patch_id="p-meta", target_file="utils.py", code_content="a = 1\nb = 2\nc = 3")
    assert patch.line_count == 3
    patch.mark_ast_validated(is_safe=True, warnings=["Consider type hints"])
    assert patch.ast_safe is True
    assert "Consider type hints" in patch.ast_warnings


def test_ast_guard_from_import_detection():
    guard = ASTBlastRadiusGuard()
    malicious_code = "from subprocess import Popen\nPopen(['ls'])"
    result = guard.inspect_code(malicious_code)
    assert result.is_safe is False
    assert any("FORBIDDEN_IMPORT" in v and "subprocess" in v for v in result.violations)


def test_maker_breaker_arbiter_failures():
    arbiter = MakerBreakerArbiter()
    patch = CodePatch(patch_id="p-fail", target_file="algo.py", code_content="def sub(a, b): return a - b", ast_safe=True)

    # 1. Non-zero exit code
    verdict_crash = arbiter.evaluate_round(
        patch=patch,
        standard_suite=None,
        adversarial_suite=None,
        exit_code=137,
        stderr="OOMKilled",
    )
    assert verdict_crash.is_ready_for_release is False
    assert "Exit Code 137" in verdict_crash.summary

    # 2. Standard functional test failure
    std_suite = TestSuite(suite_id="std-fail", test_code="assert sub(5, 2) == 3")
    std_suite.record_result("test_sub", passed=False, duration_ms=1.0, error_message="AssertionError")
    verdict_std = arbiter.evaluate_round(
        patch=patch,
        standard_suite=std_suite,
        adversarial_suite=None,
        exit_code=0,
        stderr="",
    )
    assert verdict_std.is_ready_for_release is False
    assert "Standard functional assertions failed" in verdict_std.summary


def test_secret_scrubber_detect_secrets():
    scrubber = SecretScrubber()
    found = scrubber.detect_secrets("api_key = 'vultr_secret_abc1234567890123'")
    assert len(found) > 0


def test_token_budget_boundary_and_live_eval():
    with pytest.raises(TokenBudgetExceededError, match="runaway protection"):
        TokenBudget(max_calls_per_mission=25)

    live_budget = TokenBudget.live_evaluation()
    assert live_budget.max_tokens_per_call == 1024
    assert live_budget.max_tokens_per_mission == 4096


def test_mission_adversarial_not_all_passed():
    mission = VerificationMission.create(task_slug="adv-pending", target_file="main.py")
    adv_suite = TestSuite(suite_id="adv-p", test_code="assert 1 == 1", is_adversarial=True)
    adv_suite.record_result("test_adv", passed=False, duration_ms=1.0)
    mission.attach_test_suite(adv_suite)

    mission.record_execution_outcome(exit_code=0, stdout="", stderr="", duration_ms=10.0)
    assert mission.status == MissionStatus.ADVERSARIAL_CHALLENGE
