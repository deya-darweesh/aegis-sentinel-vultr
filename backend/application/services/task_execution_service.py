"""Task Execution Pipeline Application Service.

Encapsulates background execution pipeline lifecycle, output stream hooks,
and real-time event broadcasting (ENG-STD-001 & AGENTS.md Rule 5).
"""

import uuid
from typing import Awaitable, Callable, Coroutine, Tuple

from application.dtos.task_execution_dto import TaskExecutionRequest
from application.use_cases.execute_sandboxed_task import ExecuteSandboxedTaskUseCase
from application.use_cases.trigger_chaos_probe import TriggerChaosProbeUseCase


class TaskExecutionService:
    """Orchestrates asynchronous execution tasks and streams progress events."""

    def __init__(
        self,
        task_executor: ExecuteSandboxedTaskUseCase,
        chaos_probe: TriggerChaosProbeUseCase,
        broadcast_fn: Callable[[str, str, dict], Awaitable[None]],
    ):
        self.task_executor = task_executor
        self.chaos_probe = chaos_probe
        self.broadcast = broadcast_fn

    def prepare_execution_pipeline(
        self,
        task_slug: str,
        code: str,
        target_file: str = "main.py",
    ) -> Tuple[str, Callable[[], Coroutine[None, None, None]]]:
        """Prepares a background pipeline closure for quarantined code execution."""
        task_id = f"task-{uuid.uuid4().hex[:8]}"

        async def run_pipeline():
            async def on_stdout(chunk: str):
                await self.broadcast(task_id, "stdout", {"text": chunk})

            async def on_stderr(chunk: str):
                await self.broadcast(task_id, "stderr", {"text": chunk})

            await self.broadcast(task_id, "status", {"stage": "PROVISIONING_QUARANTINE"})
            response = await self.task_executor.execute(
                request=TaskExecutionRequest(
                    task_slug=f"{task_slug}-{task_id}",
                    code_content=code,
                    target_file=target_file,
                ),
                on_stdout_chunk=on_stdout,
                on_stderr_chunk=on_stderr,
            )
            await self.broadcast(task_id, "finished", response.receipt.to_dict())

        return task_id, run_pipeline

    def prepare_chaos_pipeline(self) -> Tuple[str, Callable[[], Coroutine[None, None, None]]]:
        """Prepares a background pipeline closure for the 1-click red-team chaos probe."""
        task_id = f"chaos-{uuid.uuid4().hex[:8]}"

        async def run_pipeline():
            async def on_stdout(chunk: str):
                await self.broadcast(task_id, "stdout", {"text": chunk})

            async def on_stderr(chunk: str):
                await self.broadcast(task_id, "stderr", {"text": chunk})

            await self.broadcast(task_id, "status", {"stage": "DETONATING_REDTEAM_PROBE"})
            response = await self.chaos_probe.execute(
                task_slug=f"redteam-{task_id}",
                on_stdout_chunk=on_stdout,
                on_stderr_chunk=on_stderr,
            )
            await self.broadcast(task_id, "finished", response.receipt.to_dict())

        return task_id, run_pipeline
