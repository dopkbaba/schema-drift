"""Tests for DriftReporter output formatting."""

from __future__ import annotations

import json
import pytest

from schema_drift.models import ChangeType, DriftChange, DriftReport
from schema_drift.reporter import DriftReporter


@pytest.fixture()
def reporter() -> DriftReporter:
    return DriftReporter()


def make_report(*changes: DriftChange) -> DriftReport:
    return DriftReport(changes=list(changes))


def make_change(
    table: str = "users",
    change_type: ChangeType = ChangeType.COLUMN_REMOVED,
    detail: str | None = "col: email",
) -> DriftChange:
    return DriftChange(table=table, change_type=change_type, detail=detail)


def test_text_no_drift(reporter):
    report = make_report()
    assert reporter.as_text(report) == "No schema drift detected."


def test_text_with_breaking_change(reporter):
    change = make_change(change_type=ChangeType.COLUMN_REMOVED, detail="col: email")
    text = reporter.as_text(make_report(change))
    assert "[BREAKING]" in text
    assert "users" in text
    assert "col: email" in text


def test_text_table_added_is_info(reporter):
    change = make_change(change_type=ChangeType.TABLE_ADDED, detail=None)
    text = reporter.as_text(make_report(change))
    assert "[INFO]" in text


def test_json_structure(reporter):
    change = make_change()
    payload = json.loads(reporter.as_json(make_report(change)))
    assert payload["has_breaking_changes"] is True
    assert payload["total_changes"] == 1
    assert payload["changes"][0]["table"] == "users"
    assert payload["changes"][0]["is_breaking"] is True


def test_json_no_drift(reporter):
    payload = json.loads(reporter.as_json(make_report()))
    assert payload["has_breaking_changes"] is False
    assert payload["total_changes"] == 0


def test_markdown_no_drift(reporter):
    md = reporter.as_markdown(make_report())
    assert "No schema drift detected" in md


def test_markdown_has_table(reporter):
    change = make_change(change_type=ChangeType.TABLE_REMOVED, detail=None)
    md = reporter.as_markdown(make_report(change))
    assert "| Table |" in md
    assert "users" in md
    assert "❌ Yes" in md
