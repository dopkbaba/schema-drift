"""Tests for SnapshotComparator."""
from __future__ import annotations

import pytest

from schema_drift.models import (
    ChangeType,
    ColumnSchema,
    SchemaSnapshot,
    TableSchema,
)
from schema_drift.comparator import SnapshotComparator, CompareResult


def make_snapshot(tables: dict[str, list[tuple[str, str, bool]]]) -> SchemaSnapshot:
    schema = {}
    for tname, cols in tables.items():
        columns = [
            ColumnSchema(name=c[0], data_type=c[1], nullable=c[2]) for c in cols
        ]
        schema[tname] = TableSchema(name=tname, columns=columns)
    return SchemaSnapshot(tables=schema)


@pytest.fixture()
def comparator() -> SnapshotComparator:
    return SnapshotComparator(tag=True, score=True)


def test_no_drift_returns_empty_result(comparator):
    snap = make_snapshot({"users": [("id", "int", False)]})
    result = comparator.compare(snap, snap, "v1", "v2")
    assert isinstance(result, CompareResult)
    assert result.report.changes == []
    assert result.tags == []
    assert result.score.total_score == 0


def test_table_removed_is_detected(comparator):
    baseline = make_snapshot({"orders": [("id", "int", False)]})
    current = make_snapshot({})
    result = comparator.compare(baseline, current)
    assert any(c.change_type == ChangeType.TABLE_REMOVED for c in result.report.changes)


def test_column_removed_tagged_destructive(comparator):
    baseline = make_snapshot({"users": [("id", "int", False), ("email", "varchar", True)]})
    current = make_snapshot({"users": [("id", "int", False)]})
    result = comparator.compare(baseline, current)
    assert "destructive" in result.tags


def test_score_is_populated(comparator):
    baseline = make_snapshot({"users": [("id", "int", False)]})
    current = make_snapshot({})
    result = comparator.compare(baseline, current)
    assert result.score is not None
    assert result.score.total_score > 0


def test_to_dict_structure(comparator):
    baseline = make_snapshot({"users": [("id", "int", False)]})
    current = make_snapshot({"users": [("id", "bigint", False)]})
    result = comparator.compare(baseline, current, "snap_a", "snap_b")
    d = result.to_dict()
    assert d["baseline_name"] == "snap_a"
    assert d["current_name"] == "snap_b"
    assert "report" in d
    assert "changes" in d["report"]


def test_no_tag_flag_skips_tagging():
    comp = SnapshotComparator(tag=False, score=True)
    baseline = make_snapshot({"users": [("id", "int", False)]})
    current = make_snapshot({})
    result = comp.compare(baseline, current)
    assert result.tags == []


def test_no_score_flag_skips_scoring():
    comp = SnapshotComparator(tag=True, score=False)
    baseline = make_snapshot({"users": [("id", "int", False)]})
    current = make_snapshot({})
    result = comp.compare(baseline, current)
    assert result.score is None
