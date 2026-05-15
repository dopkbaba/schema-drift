"""Tests for schema_drift.merger."""

import pytest

from schema_drift.models import ChangeType
from schema_drift.reporter import DriftReport, SchemaChange
from schema_drift.merger import merge_reports, MergeResult


def make_change(
    table: str = "users",
    column: str | None = "id",
    change_type: ChangeType = ChangeType.COLUMN_REMOVED,
    breaking: bool = True,
    detail: str = "",
) -> SchemaChange:
    return SchemaChange(
        table=table,
        column=column,
        change_type=change_type,
        breaking=breaking,
        detail=detail,
    )


def make_report(*changes: SchemaChange) -> DriftReport:
    return DriftReport(changes=list(changes))


def test_merge_empty_reports_returns_zero_totals():
    result = merge_reports(make_report(), make_report())
    assert result.total == 0
    assert result.breaking == 0
    assert result.changes == []


def test_merge_single_report_preserves_changes():
    c = make_change()
    result = merge_reports(make_report(c))
    assert result.total == 1
    assert result.breaking == 1
    assert result.changes[0].table == "users"


def test_merge_two_reports_combines_changes():
    c1 = make_change(table="orders", column="total")
    c2 = make_change(table="products", column="price")
    result = merge_reports(make_report(c1), make_report(c2))
    assert result.total == 2
    tables = {c.table for c in result.changes}
    assert tables == {"orders", "products"}


def test_merge_deduplicates_identical_changes_by_default():
    c = make_change(table="users", column="email", change_type=ChangeType.COLUMN_REMOVED)
    result = merge_reports(make_report(c), make_report(c))
    assert result.total == 1


def test_merge_no_dedup_keeps_duplicates():
    c = make_change()
    result = merge_reports(make_report(c), make_report(c), deduplicate=False)
    assert result.total == 2


def test_merge_source_labels_are_stored():
    result = merge_reports(
        make_report(), make_report(), source_labels=["db_a", "db_b"]
    )
    assert result.sources == ["db_a", "db_b"]


def test_merge_default_source_labels_generated():
    result = merge_reports(make_report(), make_report())
    assert result.sources == ["report_0", "report_1"]


def test_merge_counts_only_breaking_changes():
    c1 = make_change(breaking=True)
    c2 = make_change(table="orders", column="status", change_type=ChangeType.COLUMN_ADDED, breaking=False)
    result = merge_reports(make_report(c1, c2))
    assert result.total == 2
    assert result.breaking == 1


def test_to_dict_structure():
    c = make_change()
    result = merge_reports(make_report(c), source_labels=["snap1"])
    d = result.to_dict()
    assert "sources" in d
    assert "total" in d
    assert "breaking" in d
    assert "changes" in d
    assert d["changes"][0]["table"] == "users"
    assert d["changes"][0]["change_type"] == ChangeType.COLUMN_REMOVED.value
