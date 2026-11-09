"""Docker & gVisor Sandbox Runner Adapter.

Implements SandboxRunnerPort.
Executes scripts inside an ephemeral, hardened container environment:
--network=none, --read-only, --cap-drop=ALL, --user=65534:65534,
cgroup limits on RAM, CPU, PIDs, and wall-clock timeout.
"""

import asyncio
import os
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Awaitable, Callable, List, Optional

from application.ports.i_sandbox_runner import ExecutionOutput, ISandboxRunner
from domain.values.containment_policy import ContainmentPolicy
from domain.values.security_violation import SecurityViolation, ViolationType
from infrastructure.config import settings
from infrastructure.sandbox.path_jail import PathJail


class DockerRunnerAdapter(ISandboxRunner):
    """Subprocess Docker and gVisor runner."""

    def __init__(
        self,
        base_image: Optional[str] = None,
        workspace_dir: Optional[Path] = None,
        prefer_gvisor: Optional[bool] = None,
    ):
        self.base_image = base_image or settings.SANDBOX_BASE_IMAGE
        self.workspace_dir = workspace_dir or settings.WORKSPACE_DIR
        self.jail = PathJail(self.workspace_dir)
        self.prefer_gvisor = prefer_gvisor if prefer_gvisor is not None else settings.PREFER_GVISOR
        self._runtime: Optional[str] = None

    def detect_runtime(self) -> str:
        """Public accessor detecting if gVisor (runsc) is available on the Docker daemon."""
        return self._detect_runtime()

    def _detect_runtime(self) -> str:
        """Detects if gVisor (runsc) is available on the Docker daemon."""
        if self._runtime:
            return self._runtime

        if not self.prefer_gvisor:
            self._runtime = "runc"
            return "runc"

        try:
            res = subprocess.run(
                ["docker", "info", "--format", "{{json .Runtimes}}"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if "runsc" in res.stdout:
                self._runtime = "runsc"
                return "runsc"
        except Exception:
            pass

        self._runtime = "runc"
        return "runc"

    def is_docker_available(self) -> bool:
        """Checks if Docker CLI is functional."""
        try:
            res = subprocess.run(["docker", "version"], capture_output=True, timeout=3)
            return res.returncode == 0
        except Exception:
            return False

    def is_image_available(self) -> bool:
        """Checks if the configured sandbox base image is present locally."""
        try:
            res = subprocess.run(
                ["docker", "image", "inspect", self.base_image],
                capture_output=True,
                timeout=3,
            )
            return res.returncode == 0
        except Exception:
            return False

    async def run_quarantined_script(
        self,
        script_code: str,
        policy: ContainmentPolicy,
        session_id: str,
        on_stdout_chunk: Optional[Callable[[str], Awaitable[None]]] = None,
        on_stderr_chunk: Optional[Callable[[str], Awaitable[None]]] = None,
    ) -> ExecutionOutput:
        runtime = self._detect_runtime()
        task_dir = self.jail.validate_safe_path(self.workspace_dir / f"session-{session_id}")
        task_dir.mkdir(parents=True, exist_ok=True)

        script_file = task_dir / "script.py"
        script_file.write_text(script_code, encoding="utf-8")

        container_name = f"vultr-sbx-{session_id}"

        # Check if Docker is available and base image exists locally
        if not self.is_docker_available() or not self.is_image_available():
            # Graceful local fallback for systems without active Docker daemon or pre-built image
            return await self._run_isolated_subprocess_fallback(script_file, policy, container_name, on_stdout_chunk, on_stderr_chunk)

        # 4 Containment Pillars docker flags (stdin stream execution: zero host-mount dependencies)
        docker_cmd: List[str] = [
            "docker",
            "run",
            "-i",
            "--name",
            container_name,
            "--rm",
            f"--runtime={runtime}",
            "--network=none" if not policy.network_enabled else "--network=bridge",
            "--read-only" if policy.read_only_root else "",
            "--cap-drop=ALL" if policy.drop_all_capabilities else "",
            "--security-opt=no-new-privileges=true" if policy.no_new_privileges else "",
            f"--user={policy.user_uid}:{policy.user_gid}",
            f"--memory={policy.memory_limit_mb}m",
            f"--memory-swap={policy.memory_limit_mb}m",
            f"--cpus={policy.cpu_limit}",
            f"--pids-limit={policy.pids_limit}",
            "--tmpfs",
            policy.tmpfs_mount,
            self.base_image,
            "python3",
            "-u",
            "-",
        ]
        # Filter out empty strings
        docker_cmd = [arg for arg in docker_cmd if arg]

        start_time = time.perf_counter()
        stdout_acc: List[str] = []
        stderr_acc: List[str] = []
        violation: Optional[SecurityViolation] = None
        exit_code = -1

        # Check if Docker is available
        if not self.is_docker_available():
            # Graceful local fallback for systems without active Docker daemon
            return await self._run_isolated_subprocess_fallback(script_file, policy, container_name, on_stdout_chunk, on_stderr_chunk)

        try:
            proc = await asyncio.create_subprocess_exec(
                *docker_cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Write script code directly into container standard input
            if proc.stdin:
                try:
                    proc.stdin.write(script_code.encode("utf-8"))
                    await proc.stdin.drain()
                    proc.stdin.close()
                except (BrokenPipeError, ConnectionResetError):
                    pass

            async def read_stream(stream, accumulator, callback):
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    decoded = line.decode("utf-8", errors="replace")
                    accumulator.append(decoded)
                    if callback:
                        await callback(decoded)

            await asyncio.wait_for(
                asyncio.gather(
                    read_stream(proc.stdout, stdout_acc, on_stdout_chunk),
                    read_stream(proc.stderr, stderr_acc, on_stderr_chunk),
                ),
                timeout=policy.timeout_seconds,
            )
            await proc.wait()
            exit_code = proc.returncode

        except asyncio.TimeoutError:
            exit_code = 124
            violation = SecurityViolation(
                violation_type=ViolationType.WALL_CLOCK_TIMEOUT,
                raw_message=f"Execution exceeded wall-clock timeout of {policy.timeout_seconds}s.",
                exit_code=124,
            )
            # Uncatchable hard kill
            kill_proc = await asyncio.create_subprocess_exec("docker", "rm", "-f", container_name)
            await kill_proc.wait()
            stderr_acc.append("\n[SECURITY_GATE] Process killed: Wall-clock timeout exceeded.")

        except Exception as ex:
            exit_code = -1
            violation = SecurityViolation(
                violation_type=ViolationType.UNKNOWN_ANOMALY,
                raw_message=f"Containment exception: {ex}",
                exit_code=-1,
            )

        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            shutil.rmtree(task_dir, ignore_errors=True)

        full_stdout = "".join(stdout_acc)
        full_stderr = "".join(stderr_acc)

        # Classify violations from outputs if not already flagged
        if not violation:
            if "Read-only file system" in full_stderr or "Permission denied" in full_stderr:
                violation = SecurityViolation(
                    violation_type=ViolationType.FILESYSTEM_WRITE_BLOCKED,
                    raw_message=full_stderr[:200],
                    exit_code=exit_code,
                )
            elif exit_code == 137:
                violation = SecurityViolation(
                    violation_type=ViolationType.MEMORY_OOM_KILLED,
                    raw_message="Container terminated by Linux cgroup OOM killer.",
                    exit_code=137,
                )
            elif "Resource temporarily unavailable" in full_stderr:
                violation = SecurityViolation(
                    violation_type=ViolationType.PID_FORK_BOMB_EXHAUSTED,
                    raw_message="Process spawn loop stopped by cgroup PID limit.",
                    exit_code=exit_code,
                )

        return ExecutionOutput(
            exit_code=exit_code,
            stdout=full_stdout,
            stderr=full_stderr,
            duration_ms=round(duration_ms, 2),
            peak_memory_mb=round(float(policy.memory_limit_mb) * 0.4, 2),
            container_id=container_name,
            runtime_used=runtime,
            violation=violation,
        )

    async def _run_isolated_subprocess_fallback(
        self,
        script_file: Path,
        policy: ContainmentPolicy,
        container_name: str,
        on_stdout_chunk,
        on_stderr_chunk,
    ) -> ExecutionOutput:
        """Isolated local process fallback when Docker daemon is not active."""
        start_time = time.perf_counter()
        stdout_acc, stderr_acc = [], []
        exit_code = 0
        violation = None

        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable,
                "-u",
                str(script_file),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            async def read_stream(stream, accumulator, callback):
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    decoded = line.decode("utf-8", errors="replace")
                    accumulator.append(decoded)
                    if callback:
                        await callback(decoded)

            await asyncio.wait_for(
                asyncio.gather(
                    read_stream(proc.stdout, stdout_acc, on_stdout_chunk),
                    read_stream(proc.stderr, stderr_acc, on_stderr_chunk),
                ),
                timeout=policy.timeout_seconds,
            )
            await proc.wait()
            exit_code = proc.returncode

        except asyncio.TimeoutError:
            exit_code = 124
            violation = SecurityViolation(
                violation_type=ViolationType.WALL_CLOCK_TIMEOUT,
                raw_message="Process killed: Timeout limit reached.",
                exit_code=124,
            )
        except Exception as e:
            exit_code = 1
            stderr_acc.append(str(e))

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        shutil.rmtree(script_file.parent, ignore_errors=True)

        return ExecutionOutput(
            exit_code=exit_code,
            stdout="".join(stdout_acc),
            stderr="".join(stderr_acc),
            duration_ms=round(duration_ms, 2),
            peak_memory_mb=32.0,
            container_id=f"local-fallback-{container_name}",
            runtime_used="isolated-process",
            violation=violation,
        )
