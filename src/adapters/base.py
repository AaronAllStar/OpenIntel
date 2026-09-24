import asyncio
import shutil
import subprocess


class BaseSubprocessAdapter:
    """Helper base class for OSINT adapters executing CLI subprocesses."""

    @staticmethod
    def is_binary_available(binary_name: str) -> bool:
        return shutil.which(binary_name) is not None

    @staticmethod
    async def run_subprocess_safely(
        args: list[str],
        timeout_seconds: float = 30.0,
        cancel_event: asyncio.Event | None = None,
    ) -> tuple[int, str, str]:
        """
        Executes a command safely passing arguments as a list (never shell=True)
        to prevent shell injection vulnerabilities.
        """
        if cancel_event and cancel_event.is_set():
            raise asyncio.CancelledError("Adapter cancelled prior to execution")

        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        try:
            stdout_data, stderr_data = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout_seconds,
            )
            return (
                proc.returncode or 0,
                stdout_data.decode("utf-8", errors="replace"),
                stderr_data.decode("utf-8", errors="replace"),
            )
        except TimeoutError as exc:
            proc.kill()
            await proc.wait()
            raise TimeoutError(f"Process {' '.join(args)} exceeded timeout of {timeout_seconds}s") from exc
        except asyncio.CancelledError:
            proc.kill()
            await proc.wait()
            raise
