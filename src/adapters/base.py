import asyncio
import os
import shutil
import signal
import subprocess
import sys


class BaseSubprocessAdapter:
    """Helper base class for OSINT adapters executing CLI subprocesses safely."""

    @staticmethod
    def is_binary_available(binary_name: str) -> bool:
        return shutil.which(binary_name) is not None

    @staticmethod
    async def _kill_process_tree(proc: asyncio.subprocess.Process) -> None:
        """Kills the subprocess and attempts to terminate its process group."""
        try:
            if sys.platform != "win32":
                try:
                    pgid = os.getpgid(proc.pid)
                    os.killpg(pgid, signal.SIGKILL)
                except Exception:
                    proc.kill()
            else:
                proc.kill()
        except (ProcessLookupError, OSError):
            pass

        try:
            await proc.wait()
        except Exception:
            pass

    @staticmethod
    async def run_subprocess_safely(
        args: list[str],
        timeout_seconds: float = 30.0,
        cancel_event: asyncio.Event | None = None,
        max_output_bytes: int = 2_000_000,
    ) -> tuple[int, str, str]:
        """
        Executes a command safely passing arguments as a list (never shell=True)
        to prevent shell injection vulnerabilities. Supports responsive cancellation,
        process tree termination, and output truncation.
        """
        if cancel_event and cancel_event.is_set():
            raise asyncio.CancelledError("Adapter cancelled prior to execution")

        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        communicate_task = asyncio.create_task(proc.communicate())

        async def _wait_for_cancel() -> None:
            if cancel_event is not None:
                await cancel_event.wait()
                raise asyncio.CancelledError("Adapter cancelled during execution")
            # If no cancel_event, sleep until communicate completes
            await asyncio.Event().wait()

        cancel_task = asyncio.create_task(_wait_for_cancel())

        try:
            done, pending = await asyncio.wait(
                [communicate_task, cancel_task],
                timeout=timeout_seconds,
                return_when=asyncio.FIRST_COMPLETED,
            )

            # Cancel remaining background monitoring tasks
            for p in pending:
                p.cancel()
                try:
                    await p
                except (asyncio.CancelledError, Exception):
                    pass

            if not done:
                # Timeout occurred
                await BaseSubprocessAdapter._kill_process_tree(proc)
                raise TimeoutError(f"Process {' '.join(args)} exceeded timeout of {timeout_seconds}s")

            if cancel_task in done:
                # Cancel task completed first, meaning cancel_event was triggered
                await BaseSubprocessAdapter._kill_process_tree(proc)
                raise asyncio.CancelledError("Adapter execution cancelled")

            stdout_data, stderr_data = communicate_task.result()

            # Truncate output if exceeding safety limit
            if len(stdout_data) > max_output_bytes:
                stdout_data = stdout_data[:max_output_bytes] + b"\n...[output truncated by OpenIntel]..."
            if len(stderr_data) > max_output_bytes:
                stderr_data = stderr_data[:max_output_bytes] + b"\n...[stderr truncated by OpenIntel]..."

            return (
                proc.returncode or 0,
                stdout_data.decode("utf-8", errors="replace"),
                stderr_data.decode("utf-8", errors="replace"),
            )

        except (TimeoutError, asyncio.CancelledError):
            await BaseSubprocessAdapter._kill_process_tree(proc)
            raise
        except Exception:
            await BaseSubprocessAdapter._kill_process_tree(proc)
            raise
