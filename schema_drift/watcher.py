"""Watches a live database and detects schema drift against a saved baseline."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Optional

from schema_drift.baseline import BaselineManager
from schema_drift.detector import DriftDetector
from schema_drift.models import SchemaSnapshot, DriftReport


@dataclass
class WatchConfig:
    """Configuration for the schema watcher."""

    baseline_dir: str
    baseline_name: str = "default"
    interval_seconds: int = 60
    max_iterations: Optional[int] = None  # None means run forever
    on_drift: Optional[Callable[[DriftReport], None]] = None
    on_no_drift: Optional[Callable[[], None]] = None


@dataclass
class WatchResult:
    """Summary of a watch session."""

    iterations: int = 0
    drift_detected_count: int = 0
    reports: list[DriftReport] = field(default_factory=list)


class SchemaWatcher:
    """Polls a snapshot source and reports drift against a baseline."""

    def __init__(self, config: WatchConfig) -> None:
        self._config = config
        self._manager = BaselineManager(config.baseline_dir)
        self._detector = DriftDetector()

    def _check(self, current: SchemaSnapshot) -> Optional[DriftReport]:
        """Compare current snapshot against saved baseline."""
        if not self._manager.exists(self._config.baseline_name):
            raise FileNotFoundError(
                f"No baseline '{self._config.baseline_name}' found in "
                f"'{self._config.baseline_dir}'. Run 'baseline save' first."
            )
        baseline = self._manager.load(self._config.baseline_name)
        report = self._detector.detect(baseline, current)
        return report if report.changes else None

    def watch(
        self, snapshot_fn: Callable[[], SchemaSnapshot]
    ) -> WatchResult:
        """Run the watch loop, calling snapshot_fn each iteration."""
        cfg = self._config
        result = WatchResult()
        iteration = 0

        while True:
            if cfg.max_iterations is not None and iteration >= cfg.max_iterations:
                break

            current = snapshot_fn()
            report = self._check(current)
            result.iterations += 1

            if report:
                result.drift_detected_count += 1
                result.reports.append(report)
                if cfg.on_drift:
                    cfg.on_drift(report)
            else:
                if cfg.on_no_drift:
                    cfg.on_no_drift()

            iteration += 1

            if cfg.max_iterations is not None and iteration >= cfg.max_iterations:
                break

            time.sleep(cfg.interval_seconds)

        return result
