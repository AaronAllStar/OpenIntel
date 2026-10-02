import threading
import time
from collections import defaultdict


class MetricsCollector:
    """
    Lightweight, thread-safe Prometheus metrics collector and exporter.
    Does not require heavy external C dependencies.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._start_time = time.time()
        self._investigations_total: dict[tuple[str, str], int] = defaultdict(int)
        self._adapter_runs_total: dict[tuple[str, str], int] = defaultdict(int)
        self._adapter_durations: dict[str, list[float]] = defaultdict(list)
        self._circuit_breakers: dict[str, int] = defaultdict(int)
        self._active_connections = 0

    def inc_investigation(self, status: str, target_kind: str) -> None:
        with self._lock:
            self._investigations_total[(status, target_kind)] += 1

    def inc_adapter_run(self, engine: str, status: str, duration_s: float = 0.0) -> None:
        with self._lock:
            self._adapter_runs_total[(engine, status)] += 1
            if duration_s > 0:
                self._adapter_durations[engine].append(duration_s)
                # Keep sliding window of last 100 durations
                if len(self._adapter_durations[engine]) > 100:
                    self._adapter_durations[engine].pop(0)

    def set_circuit_breaker(self, engine: str, state: int) -> None:
        with self._lock:
            self._circuit_breakers[engine] = state

    def set_active_connections(self, count: int) -> None:
        with self._lock:
            self._active_connections = count

    def generate_prometheus_text(self) -> str:
        with self._lock:
            lines = [
                "# HELP openintel_uptime_seconds Process uptime in seconds.",
                "# TYPE openintel_uptime_seconds gauge",
                f"openintel_uptime_seconds {time.time() - self._start_time:.2f}",
                "",
                "# HELP openintel_active_sse_connections Active real-time SSE stream connections.",
                "# TYPE openintel_active_sse_connections gauge",
                f"openintel_active_sse_connections {self._active_connections}",
                "",
                "# HELP openintel_investigations_total Total investigations launched by status and target kind.",
                "# TYPE openintel_investigations_total counter",
            ]

            for (st, tk), count in self._investigations_total.items():
                lines.append(f'openintel_investigations_total{{status="{st}",target_kind="{tk}"}} {count}')

            lines.extend([
                "",
                "# HELP openintel_adapter_runs_total Total adapter executions by engine and status.",
                "# TYPE openintel_adapter_runs_total counter",
            ])

            for (eng, st), count in self._adapter_runs_total.items():
                lines.append(f'openintel_adapter_runs_total{{engine="{eng}",status="{st}"}} {count}')

            lines.extend([
                "",
                "# HELP openintel_circuit_breaker_state Current circuit breaker state (0=closed, 1=open, 2=half-open).",
                "# TYPE openintel_circuit_breaker_state gauge",
            ])

            for eng, state in self._circuit_breakers.items():
                lines.append(f'openintel_circuit_breaker_state{{engine="{eng}"}} {state}')

            lines.append("")
            return "\n".join(lines)


metrics = MetricsCollector()
