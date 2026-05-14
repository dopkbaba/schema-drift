"""Tests for schema_drift.notifier."""

from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from schema_drift.models import ChangeType, DriftReport, SchemaChange
from schema_drift.notifier import DriftNotifier, NotifyConfig
from schema_drift.scorer import DriftScore


def make_score(severity: str = "low", total: float = 1.0) -> DriftScore:
    return DriftScore(total=total, severity=severity, breakdown={})


def make_report(breaking: int = 0) -> DriftReport:
    changes = []
    for i in range(breaking):
        changes.append(
            SchemaChange(
                table=f"tbl_{i}",
                change_type=ChangeType.TABLE_REMOVED,
                breaking=True,
            )
        )
    return DriftReport(changes=changes)


@pytest.fixture
def tmp_log(tmp_path):
    return str(tmp_path / "drift.log")


def test_no_notification_below_threshold():
    cfg = NotifyConfig(min_severity="high")
    notifier = DriftNotifier(cfg)
    result = notifier.notify(make_report(), make_score(severity="low"))
    assert result.sent_to == []
    assert result.success


def test_meets_threshold_exact_match():
    cfg = NotifyConfig(min_severity="medium")
    notifier = DriftNotifier(cfg)
    score = make_score(severity="medium", total=5.0)
    result = notifier.notify(make_report(breaking=1), score)
    # No sinks configured — still counts as success
    assert result.success
    assert result.sent_to == []


def test_log_file_written(tmp_log):
    cfg = NotifyConfig(log_file=tmp_log, min_severity="low")
    notifier = DriftNotifier(cfg)
    result = notifier.notify(make_report(breaking=1), make_score(severity="high", total=10.0))
    assert result.success
    assert tmp_log in result.sent_to
    lines = open(tmp_log).readlines()
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["severity"] == "high"
    assert data["breaking_changes"] == 1


def test_log_file_appends(tmp_log):
    cfg = NotifyConfig(log_file=tmp_log, min_severity="low")
    notifier = DriftNotifier(cfg)
    score = make_score(severity="low", total=1.0)
    notifier.notify(make_report(), score)
    notifier.notify(make_report(), score)
    lines = open(tmp_log).readlines()
    assert len(lines) == 2


def test_log_file_error_captured(tmp_path):
    bad_path = str(tmp_path / "no_dir" / "drift.log")
    cfg = NotifyConfig(log_file=bad_path, min_severity="low")
    notifier = DriftNotifier(cfg)
    result = notifier.notify(make_report(), make_score())
    assert not result.success
    assert any("log_file" in e for e in result.errors)


def test_webhook_called():
    cfg = NotifyConfig(webhook_url="http://example.com/hook", min_severity="low")
    notifier = DriftNotifier(cfg)
    with patch("urllib.request.urlopen") as mock_open:
        mock_open.return_value = MagicMock()
        result = notifier.notify(make_report(breaking=2), make_score(severity="critical", total=20.0))
    assert result.success
    assert "http://example.com/hook" in result.sent_to


def test_webhook_error_captured():
    cfg = NotifyConfig(webhook_url="http://bad.invalid/hook", min_severity="low")
    notifier = DriftNotifier(cfg)
    with patch("urllib.request.urlopen", side_effect=OSError("conn refused")):
        result = notifier.notify(make_report(), make_score())
    assert not result.success
    assert any("webhook" in e for e in result.errors)
