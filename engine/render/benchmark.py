"""
Benchmarking Tracker for Reel Editor.
Measures wall-clock time, CPU/memory stats, and generates structured reports.
"""
import time
from typing import Dict, Any

class Benchmark:
    def __init__(self):
        self.timers: Dict[str, float] = {}
        self.durations: Dict[str, float] = {}
        self.metrics: Dict[str, Any] = {}
        self.total_start = time.perf_counter()

    def start(self, stage: str):
        self.timers[stage] = time.perf_counter()

    def end(self, stage: str) -> float:
        if stage in self.timers:
            elapsed = time.perf_counter() - self.timers[stage]
            self.durations[stage] = round(elapsed, 3)
            return self.durations[stage]
        return 0.0

    def record_metric(self, key: str, value: Any):
        self.metrics[key] = value

    def finish(self) -> Dict[str, Any]:
        self.durations["total"] = round(time.perf_counter() - self.total_start, 3)
        return {
            "durations": self.durations,
            "metrics": self.metrics
        }

    def format_table(self) -> str:
        report = ["Stage Timing Summary:"]
        report.append("-" * 40)
        for stage, duration in self.durations.items():
            report.append(f"{stage:<25} : {duration:>7.2f}s")
        report.append("-" * 40)
        return "\n".join(report)
