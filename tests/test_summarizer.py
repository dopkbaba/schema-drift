"""Tests for schema_drift.summarizer."""

import pytest

from schema_drift.models import DriftReport, SchemaChange, ChangeType
from schema_drift.summarizer import summarize_report, DriftSummary


def make_change(
    table: str = "users",
    change_type: ChangeType = ChangeType.COLUMN_REMOVED,
    breaking: bool = True,
    column: str = "email",
) -> SchemaChange:
    return SchemaChange(
        table=table,
        change_type=change_type,
        breaking=breaking,
        column=column,
        detail="test",
    )


def make_report(*changes: SchemaChange) -> DriftReport:
    return DriftReport(changes=list(changes))


def test_empty_report_returns_zero_summary():
    summary = summarize_report(make_report())
    assert summary.total_tables_affected == 0
    assert summary.total_changes == 0
    assert summary.total_breaking == 0
    assert summary.top_tables == []


def test_single_breaking_change():
    report = make_report(make_change(table="orders", breaking=True))
    summary = summarize_report(report)
    assert summary.total_tables_affected == 1
    assert summary.total_breaking == 1
    assert len(summary.top_tables) == 1
    assert summary.top_tables[0].table == "orders"
    assert summary.top_tables[0].breaking == 1


def test_multiple_tables_sorted_by_breaking():
    changes = [
        make_change(table="a", breaking=False),
        make_change(table="b", breaking=True),
        make_change(table="b", breaking=True, column="name"),
        make_change(table="c", breaking=True),
    ]
    summary = summarize_report(make_report(*changes))
    assert summary.top_tables[0].table == "b"
    assert summary.total_tables_affected == 3


def test_top_n_limits_results():
    changes = [make_change(table=f"t{i}") for i in range(10)]
    summary = summarize_report(make_report(*changes), top_n=3)
    assert len(summary.top_tables) == 3


def test_change_types_deduplicated():
    changes = [
        make_change(table="users", change_type=ChangeType.COLUMN_REMOVED, column="a"),
        make_change(table="users", change_type=ChangeType.COLUMN_REMOVED, column="b"),
    ]
    summary = summarize_report(make_report(*changes))
    digest = summary.top_tables[0]
    assert digest.change_types.count(ChangeType.COLUMN_REMOVED.value) == 1


def test_to_dict_structure():
    report = make_report(make_change())
    summary = summarize_report(report)
    d = summary.to_dict()
    assert "total_tables_affected" in d
    assert "total_breaking" in d
    assert "risk_level" in d
    assert "score" in d
    assert isinstance(d["top_tables"], list)
    assert "table" in d["top_tables"][0]


def test_non_breaking_counted_separately():
    changes = [
        make_change(table="logs", breaking=False, change_type=ChangeType.COLUMN_ADDED),
        make_change(table="logs", breaking=False, change_type=ChangeType.COLUMN_ADDED, column="b"),
    ]
    summary = summarize_report(make_report(*changes))
    assert summary.total_breaking == 0
    assert summary.top_tables[0].non_breaking == 2
