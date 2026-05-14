"""Tests for schema_drift.commands.audit_cmd."""

from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import pytest

from schema_drift.auditor import DriftAuditor
from schema_drift.commands.audit_cmd import cmd_audit_clear, cmd_audit_list
from schema_drift.scorer import DriftScore


@pytest.fixture
def tmp_audit(tmp_path: Path) -> Path:
    return tmp_path / "audit"


def _score() -> DriftScore:
    return DriftScore(score=3.0, total_changes=2, breaking_changes=0, risk_level="low")


def _populated_auditor(tmp_audit: Path) -> DriftAuditor:
    auditor = DriftAuditor(audit_dir=tmp_audit)
    auditor.record(_score(), snapshot_label="release-1.0", triggered_by="ci")
    auditor.record(_score(), snapshot_label="release-1.1", triggered_by="developer")
    return auditor


def test_list_text_no_entries(tmp_audit, capsys):
    args = Namespace(audit_dir=str(tmp_audit), last=10, format="text")
    rc = cmd_audit_list(args)
    assert rc == 0
    captured = capsys.readouterr()
    assert "No audit entries" in captured.out


def test_list_text_with_entries(tmp_audit, capsys):
    _populated_auditor(tmp_audit)
    args = Namespace(audit_dir=str(tmp_audit), last=10, format="text")
    rc = cmd_audit_list(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "release-1.0" in out
    assert "release-1.1" in out


def test_list_json_format(tmp_audit, capsys):
    _populated_auditor(tmp_audit)
    args = Namespace(audit_dir=str(tmp_audit), last=10, format="json")
    rc = cmd_audit_list(args)
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["snapshot_label"] == "release-1.0"


def test_list_respects_last_param(tmp_audit, capsys):
    _populated_auditor(tmp_audit)
    args = Namespace(audit_dir=str(tmp_audit), last=1, format="json")
    cmd_audit_list(args)
    data = json.loads(capsys.readouterr().out)
    assert len(data) == 1
    assert data[0]["snapshot_label"] == "release-1.1"


def test_clear_removes_entries(tmp_audit, capsys):
    _populated_auditor(tmp_audit)
    args = Namespace(audit_dir=str(tmp_audit))
    rc = cmd_audit_clear(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "Cleared 2" in out
    auditor = DriftAuditor(audit_dir=tmp_audit)
    assert auditor.entries == []
