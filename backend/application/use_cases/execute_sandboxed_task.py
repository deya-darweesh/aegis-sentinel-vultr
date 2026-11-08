"""Execute Sandboxed Task Use Case.

Enforces:
1. Static AST Blast Radius screening.
2. Quarantined execution via ISandboxRunner.
3. Dual-sink hash-chained audit logging.
4. Ed25519 canonical receipt signing.
"""

import uuid
from typing import Awaitable, Callable, Optional

from application.dtos.execution_receipt_dto import ExecutionReceiptDTO
from application.dtos.task_execution_dto import TaskExecutionRequest, TaskExecutionResult
from application.ports.i_audit_ledger import IAuditLedger
from application.ports.i_sandbox_runner import ISandboxRunner
from domain.aggregates.verification_mission import MissionStatus, VerificationMission
from domain.entities.code_patch import CodePatch
from domain.services.ast_blast_radius_guard import ASTBlastRadiusGuard
from domain.values.containment_policy import ContainmentPolicy
from domain.values.execution_receipt import ExecutionReceipt
from infrastructure.crypto.receipt_signer import ReceiptSigner


def _receipt_to_dto(receipt: ExecutionReceipt, public_key: str) -> ExecutionReceiptDTO:
    return ExecutionReceiptDTO(
        receipt_id=receipt.receipt_id,
        timestamp=receipt.timestamp,
        task_slug=receipt.task_slug,
        status=receipt.status.value,
        exit_code=receipt.exit_code,
        duration_ms=receipt.duration_ms,
        memory_peak_mb=receipt.memory_peak_mb,
        runtime_engine=receipt.runtime_engine,
        container_id=receipt.container_id,
        digest_sha256=receipt.compute_canonical_digest(),
        ed25519_signature=receipt.ed25519_signature,
        public_key=public_key,
        violation=receipt.violation,
    )


class ExecuteSandboxedTaskUseCase:
    """Orchestrates quarantined execution of any user or agent task."""

    def __init__(
        self,
        runner: ISandboxRunner,
        ledger: IAuditLedger,
        signer: ReceiptSigner,
        ast_guard: Optional[ASTBlastRadiusGuard] = None,
    ):
        self.runner = runner
        self.ledger = ledger
        self.signer = signer
        self.ast_guard = ast_guard or ASTBlastRadiusGuard()

    async def execute(
        self,
        request: TaskExecutionRequest,
        on_stdout_chunk: Optional[Callable[[str], Awaitable[None]]] = None,
        on_stderr_chunk: Optional[Callable[[str], Awaitable[None]]] = None,
    ) -> TaskExecutionResult:
        policy = request.policy or ContainmentPolicy.strict_airgap()
        mission = VerificationMission.create(
            task_slug=request.task_slug,
            target_file=request.target_file,
            policy=policy,
        )

        session_id = uuid.uuid4().hex[:10]

        # 1. Static AST Screening
        ast_result = self.ast_guard.inspect_code(request.code_content)
        patch = CodePatch(
            patch_id=f"ptch-{session_id}",
            target_file=request.target_file,
            code_content=request.code_content,
            ast_safe=ast_result.is_safe,
            ast_warnings=ast_result.violations,
        )

        if not ast_result.is_safe and not policy.is_chaos_probe:
            # Blocked before reaching container!
            violation_msg = "; ".join(ast_result.violations)
            self.ledger.append_event(
                event_id=uuid.uuid4().hex,
                task_slug=request.task_slug,
                event_type="AST_STATIC_VIOLATION_BLOCKED",
                payload={"violations": ast_result.violations},
            )
            mission.status = MissionStatus.POLICY_REJECTED
            receipt = mission.produce_receipt(audit_chain_hash=self.ledger.get_latest_chain_hash())
            sig = self.signer.sign_digest(receipt.compute_canonical_digest())
            signed_receipt_obj = receipt.with_signature(sig)
            self.ledger.persist_receipt(signed_receipt_obj)

            receipt_dto = _receipt_to_dto(signed_receipt_obj, self.signer.public_key_hex)

            return TaskExecutionResult(
                mission_id=mission.mission_id,
                status=mission.status.value,
                exit_code=1,
                stdout="",
                stderr=f"[AST_SECURITY_GUARD] Rejected dangerous code before execution:\n{violation_msg}",
                duration_ms=5.0,
                receipt=receipt_dto,
                is_success=False,
                violation=violation_msg,
            )

        if policy.is_chaos_probe and not ast_result.is_safe:
            self.ledger.append_event(
                event_id=uuid.uuid4().hex,
                task_slug=request.task_slug,
                event_type="CHAOS_PROBE_DISPATCHED_TO_CONTAINER",
                payload={"expected_violations": ast_result.violations},
            )

        mission.attach_patch(patch)

        # 2. Record Dispatch in Audit Ledger
        self.ledger.append_event(
            event_id=uuid.uuid4().hex,
            task_slug=request.task_slug,
            event_type="CONTAINER_DISPATCHED",
            payload={"session_id": session_id, "patch_sha256": patch.sha256_hash},
        )

        # 3. Quarantined Execution inside Docker/gVisor
        output = await self.runner.run_quarantined_script(
            script_code=request.code_content,
            policy=policy,
            session_id=session_id,
            on_stdout_chunk=on_stdout_chunk,
            on_stderr_chunk=on_stderr_chunk,
        )

        # 4. Evaluate Outcome via Aggregate Root
        mission.record_execution_outcome(
            exit_code=output.exit_code,
            stdout=output.stdout,
            stderr=output.stderr,
            duration_ms=output.duration_ms,
            violation=output.violation,
        )

        # 5. Append Execution Outcome to Hash-Chained Ledger
        self.ledger.append_event(
            event_id=uuid.uuid4().hex,
            task_slug=request.task_slug,
            event_type="CONTAINER_EXECUTION_COMPLETED",
            payload={
                "exit_code": output.exit_code,
                "duration_ms": output.duration_ms,
                "violation": output.violation.violation_type.value if output.violation else None,
            },
            container_id=output.container_id,
        )

        # 6. Generate and Sign Execution Receipt
        receipt = mission.produce_receipt(audit_chain_hash=self.ledger.get_latest_chain_hash())
        signature = self.signer.sign_digest(receipt.compute_canonical_digest())
        signed_receipt_obj = receipt.with_signature(signature)
        self.ledger.persist_receipt(signed_receipt_obj)

        receipt_dto = _receipt_to_dto(signed_receipt_obj, self.signer.public_key_hex)

        is_success = output.exit_code == 0 and mission.status in (
            MissionStatus.VERIFIED_PASSED,
            MissionStatus.INITIALIZED,
        )

        return TaskExecutionResult(
            mission_id=mission.mission_id,
            status=mission.status.value,
            exit_code=output.exit_code,
            stdout=output.stdout,
            stderr=output.stderr,
            duration_ms=output.duration_ms,
            receipt=receipt_dto,
            is_success=is_success,
            violation=output.violation.raw_message if output.violation else None,
        )
