"""Notification hooks for drift events — supports console, webhook, and file sinks."""

from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass, field
from typing import List, Optional

from schema_drift.models import DriftReport
from schema_drift.scorer import DriftScore


@dataclass
class NotifyConfig:
    webhook_url: Optional[str] = None
    log_file: Optional[str] = None
    min_severity: str = "low"  # low | medium | high | critical
    include_summary: bool = True


@dataclass
class NotifyResult:
    sent_to: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return len(self.errors) == 0


class DriftNotifier:
    """Dispatches drift notifications to configured sinks."""

    _SEVERITY_ORDER = ["low", "medium", "high", "critical"]

    def __init__(self, config: NotifyConfig) -> None:
        self._config = config

    def notify(self, report: DriftReport, score: DriftScore) -> NotifyResult:
        result = NotifyResult()
        if not self._meets_threshold(score):
            return result

        payload = self._build_payload(report, score)

        if self._config.webhook_url:
            self._send_webhook(payload, result)

        if self._config.log_file:
            self._write_log(payload, result)

        return result

    def _meets_threshold(self, score: DriftScore) -> bool:
        order = self._SEVERITY_ORDER
        min_idx = order.index(self._config.min_severity) if self._config.min_severity in order else 0
        actual_idx = order.index(score.severity) if score.severity in order else 0
        return actual_idx >= min_idx

    def _build_payload(self, report: DriftReport, score: DriftScore) -> dict:
        payload: dict = {
            "severity": score.severity,
            "total_score": score.total,
            "breaking_changes": report.breaking_count,
            "total_changes": report.total_changes,
        }
        if self._config.include_summary:
            payload["tables_affected"] = [c.table for c in report.changes]
        return payload

    def _send_webhook(self, payload: dict, result: NotifyResult) -> None:
        try:
            data = json.dumps(payload).encode()
            req = urllib.request.Request(
                self._config.webhook_url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=5)
            result.sent_to.append(self._config.webhook_url)
        except Exception as exc:  # noqa: BLE001
            result.errors.append(f"webhook: {exc}")

    def _write_log(self, payload: dict, result: NotifyResult) -> None:
        try:
            with open(self._config.log_file, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(payload) + "\n")
            result.sent_to.append(self._config.log_file)
        except OSError as exc:
            result.errors.append(f"log_file: {exc}")
