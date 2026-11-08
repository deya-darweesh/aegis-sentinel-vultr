"""Verification Mission Aggregate Root.

The primary Consistency Boundary governing the complete autonomous verification lifecycle:
1. Orchestrates the Maker-Breaker dynamic (Synthesizer vs. Adversarial Fuzzer).
2. Enforces the Golden Rule: Only deterministic POSIX exit codes determine PASS/FAIL.
3. Guards against credit depletion by checking TokenBudget.
4. Produces immutable, cryptographically verifiable ExecutionReceipts.
"""

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from domain.entities.code_patch import CodePatch
from domain.entities.exploit_payload import ExploitPayload
from domain.entities.sandbox_session import SandboxSession, SessionState
from domain.entities.test_suite import TestSuite
from domain.values.containment_policy import ContainmentPolicy
from domain.values.execution_receipt import ExecutionReceipt, SecurityStatus
from domain.values.security_violation import SecurityViolation
from domain.values.token_budget import TokenBudget


class MissionStatus(str, Enum):
    INITIALIZED = "INITIALIZED"
    IN_QUARANTINE = "IN_QUARANTINE"
    ADVERSARIAL_CHALLENGE = "ADVERSARIAL_CHALLENGE"
    VERIFIED_PASSED = "VERIFIED_PASSED"
    CONTAINMENT_TRIGGERED = "CONTAINMENT_TRIGGERED"
    ASSERTION_FAILED = "ASSERTION_FAILED"
    POLICY_REJECTED = "POLICY_REJECTED"
    TERMINATED = "TERMINATED"


class MissionDomainError(Exception):
    """Raised when an aggregate invariant is breached."""

    pass


@dataclass
class VerificationMission:
    """Aggregate Root for SentinelQA Verification Missions."""

    mission_id: str
    task_slug: str
    target_file: str
    policy: ContainmentPolicy
    budget: TokenBudget = field(default_factory=TokenBudget.development_safe)
    status: MissionStatus = MissionStatus.INITIALIZED

    # Aggregated Entities
    current_patch: Optional[CodePatch] = None
    standard_tests: Optional[TestSuite] = None
    adversarial_tests: Optional[TestSuite] = None
    active_session: Optional[SandboxSession] = None
    exploits: List[ExploitPayload] = field(default_factory=list)
    patches: List[CodePatch] = field(default_factory=list)

    # Audit & Tracking State
    attempts: int = 0
    max_attempts: int = 3
    tokens_consumed: int = 0
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    audit_chain: List[dict] = field(default_factory=list)
    last_violation: Optional[SecurityViolation] = None

    @classmethod
    def create(
        cls,
        task_slug: str,
        target_file: str,
        policy: Optional[ContainmentPolicy] = None,
        budget: Optional[TokenBudget] = None,
    ) -> "VerificationMission":
        """Factory method enforcing clean mission initialization."""
        return cls(
            mission_id=f"msn-{uuid.uuid4().hex[:10]}",
            task_slug=task_slug,
            target_file=target_file,
            policy=policy or ContainmentPolicy.strict_airgap(),
            budget=budget or TokenBudget.development_safe(),
        )

    def attach_patch(self, patch: CodePatch):
        """Attaches candidate code for verification."""
        if not patch.ast_safe and not self.policy.is_chaos_probe:
            raise MissionDomainError("Cannot attach patch that has not passed AST safety checks.")
        self.current_patch = patch
        self.patches.append(patch)
        self._record_audit_event("PATCH_ATTACHED", {"patch_sha256": patch.sha256_hash})

    def attach_exploit(self, exploit: ExploitPayload) -> None:
        """Attaches an adversarial exploit payload."""
        self.exploits.append(exploit)
        self._record_audit_event(
            "EXPLOIT_ATTACHED",
            {
                "exploit_id": exploit.exploit_id,
                "attack_vector": exploit.attack_vector,
                "round_number": exploit.round_number,
                "sha256": exploit.sha256_hash,
            },
        )

    def attach_test_suite(self, suite: TestSuite):
        """Attaches a test suite (standard or adversarial)."""
        if suite.is_adversarial:
            self.adversarial_tests = suite
            self.status = MissionStatus.ADVERSARIAL_CHALLENGE
            self._record_audit_event("ADVERSARIAL_TESTS_ATTACHED", {"suite_sha256": suite.sha256_hash})
        else:
            self.standard_tests = suite
            self.status = MissionStatus.IN_QUARANTINE
            self._record_audit_event("STANDARD_TESTS_ATTACHED", {"suite_sha256": suite.sha256_hash})

    def bind_sandbox_session(self, session: SandboxSession):
        """Associates an active quarantine container with this mission."""
        self.active_session = session
        self._record_audit_event("SANDBOX_BOUND", {"session_id": session.session_id, "runtime": session.runtime})

    def consume_tokens(self, tokens: int):
        """Enforces token budget invariants to prevent credit runaway."""
        if self.tokens_consumed + tokens > self.budget.max_tokens_per_mission:
            self.status = MissionStatus.POLICY_REJECTED
            raise MissionDomainError(f"Token budget exceeded: {self.tokens_consumed + tokens} > {self.budget.max_tokens_per_mission}")
        self.tokens_consumed += tokens

    def record_execution_outcome(
        self,
        exit_code: int,
        stdout: str,
        stderr: str,
        duration_ms: float,
        violation: Optional[SecurityViolation] = None,
    ):
        """Enforces the Golden Rule: Deterministic exit codes own the verdict.

        Language models are NEVER trusted to say 'this passed'.
        """
        self.attempts += 1

        if violation:
            self.last_violation = violation
            self.status = MissionStatus.CONTAINMENT_TRIGGERED
            self._record_audit_event(
                "CONTAINMENT_TRIGGERED",
                {
                    "violation_type": violation.violation_type.value,
                    "summary": violation.human_readable_summary,
                    "exit_code": exit_code,
                },
            )
            return

        if exit_code == 0:
            # Deterministic PASS
            if self.adversarial_tests and not self.adversarial_tests.all_passed:
                # Still waiting on adversarial challenge completion
                self.status = MissionStatus.ADVERSARIAL_CHALLENGE
            else:
                self.status = MissionStatus.VERIFIED_PASSED
                self.completed_at = time.time()
            self._record_audit_event("DETERMINISTIC_PASS", {"exit_code": 0, "duration_ms": duration_ms})
        else:
            # Deterministic FAIL
            if self.attempts >= self.max_attempts:
                self.status = MissionStatus.ASSERTION_FAILED
                self.completed_at = time.time()
                self._record_audit_event("MISSION_FAILED_MAX_RETRIES", {"attempts": self.attempts})
            else:
                self.status = MissionStatus.IN_QUARANTINE  # Ready for self-healing iteration
                self._record_audit_event("SELF_HEALING_REQUIRED", {"exit_code": exit_code, "attempt": self.attempts})

    def produce_receipt(self, audit_chain_hash: str) -> ExecutionReceipt:
        """Compiles the immutable, verifiable containment receipt."""
        status_map = {
            MissionStatus.VERIFIED_PASSED: SecurityStatus.MATHEMATICALLY_VERIFIED,
            MissionStatus.CONTAINMENT_TRIGGERED: SecurityStatus.CONTAINMENT_TRIGGERED,
            MissionStatus.ASSERTION_FAILED: SecurityStatus.ASSERTION_FAILED,
            MissionStatus.POLICY_REJECTED: SecurityStatus.POLICY_REJECTED,
        }

        sec_status = status_map.get(self.status, SecurityStatus.POLICY_REJECTED)

        return ExecutionReceipt(
            receipt_id=f"rcpt-{uuid.uuid4().hex[:8]}",
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            task_slug=self.task_slug,
            status=sec_status,
            exit_code=0 if sec_status == SecurityStatus.MATHEMATICALLY_VERIFIED else 1,
            duration_ms=round((time.time() - self.created_at) * 1000.0, 2),
            memory_peak_mb=self.active_session.peak_memory_mb if self.active_session else 0.0,
            runtime_engine=self.active_session.runtime if self.active_session else "runsc",
            container_id=self.active_session.container_name if self.active_session else "none",
            input_sha256=self.current_patch.sha256_hash if self.current_patch else "none",
            patch_sha256=self.current_patch.sha256_hash if self.current_patch else "none",
            audit_chain_hash=audit_chain_hash,
            violation=self.last_violation.human_readable_summary if self.last_violation else None,
        )

    def _record_audit_event(self, event_type: str, payload: dict):
        self.audit_chain.append(
            {
                "timestamp": time.time(),
                "event_type": event_type,
                "payload": payload,
            }
        )
