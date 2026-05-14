"""Tests for schema_drift.auditor."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from schema_drift.auditor import AuditEntry, DriftAuditor
from schema_drift.scorer import DriftScore


@pytest.fixture
def tmp_audit(tmp_path: Path) -> Path:
    return tmp_path / "audit"


def make_score(score: float = 5.0, total: int = 3, breaking: int = 1,
               risk: str = "medium") -> DriftScore:
    return DriftScore(score=score, total_changes=total, breaking_changes=breaking, risk_level=risk)


def test_new_auditor_has_no_entries(tmp_audit):
    auditor = DriftAuditor(audit_dir=tmp_audit)
    assert auditor.entries == []


def test_record_creates_entry(tmp_audit):
    auditor = DriftAuditor(audit_dir=tmp_audit)
    score = make_score()
    entry = auditor.record(score, snapshot_label="v1.2", triggered_by="ci")
    assert entry.snapshot_label == "v1.2"
    assert entry.triggered_by == "ci"
    assert entry.score == 5.0
    assert entry.breaking_changes == 1
    assert len(auditor.entries) == 1


def test_record_persists_to_disk(tmp_audit):
    auditor = DriftAuditor(audit_dir=tmp_audit)
    auditor.record(make_score(), snapshot_label="snap-a")
    log_path = tmp_audit / "audit_log.jsonl"
    assert log_path.exists()
    lines = log_path.read_text().strip().splitlines()
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["snapshot_label"] == "snap-a"


def test_reload_loads_existing_entries(tmp_audit):
    a1 = DriftAuditor(audit_dir=tmp_audit)
    a1.record(make_score(), snapshot_label="first")
    a1.record(make_score(score=9.0, risk="high"), snapshot_label="second")

    a2 = DriftAuditor(audit_dir=tmp_audit)
    assert len(a2.entries) == 2
    assert a2.entries[0].snapshot_label == "first"
    assert a2.entries[1].risk_level == "high"


def test_recent_returns_last_n(tmp_audit):
    auditor = DriftAuditor(audit_dir=tmp_audit)
    for i in range(5):
        auditor.record(make_score(), snapshot_label=f"snap-{i}")
    recent = auditor.recent(n=3)
    assert len(recent) == 3
    assert recent[-1].snapshot_label == "snap-4"


def test_clear_removes_entries_and_file(tmp_audit):
    auditor = DriftAuditor(audit_dir=tmp_audit)
    auditor.record(make_score(), snapshot_label="to-delete")
    auditor.clear()
    assert auditor.entries == []
    assert not (tmp_audit / "audit_log.jsonl").exists()


def test_audit_entry_round_trips_dict():
    entry = AuditEntry(
        timestamp="2024-01-01T00:00:00+00:00",
        snapshot_label="test",
        total_changes=4,
        breaking_changes=2,
        score=8.0,
        risk_level="high",
        triggered_by="test-suite",
        notes="regression check",
    )
    restored = AuditEntry.from_dict(entry.to_dict())
    assert restored.snapshot_label == entry.snapshot_label
    assert restored.notes == "regression check"
    assert restored.score == 8.0


def test_record_with_notes(tmp_audit):
    auditor = DriftAuditor(audit_dir=tmp_audit)
    entry = auditor.record(make_score(), snapshot_label="noted", notes="hotfix deploy")
    assert entry.notes == "hotfix deploy"
    reloaded = DriftAuditor(audit_dir=tmp_audit)
    assert reloaded.entries[0].notes == "hotfix deploy"
