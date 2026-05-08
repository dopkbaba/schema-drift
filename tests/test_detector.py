"""Tests for the DriftDetector class."""

from datetime import datetime

import pytest

from schema_drift import (
    ChangeType,
    ColumnSchema,
    DriftDetector,
    SchemaSnapshot,
    TableSchema,
)


def make_snapshot(source: str, tables: dict) -> SchemaSnapshot:
    snap = SchemaSnapshot(captured_at=datetime.utcnow(), source=source)
    for table_name, columns in tables.items():
        table = TableSchema(name=table_name)
        for col_name, col_attrs in columns.items():
            table.columns[col_name] = ColumnSchema(name=col_name, **col_attrs)
        snap.tables[table_name] = table
    return snap


@pytest.fixture
def detector():
    return DriftDetector()


def test_no_drift(detector):
    schema = {"users": {"id": {"data_type": "integer", "nullable": False}}}
    baseline = make_snapshot("v1", schema)
    current = make_snapshot("v2", schema)
    report = detector.detect(baseline, current)
    assert report.total_changes == 0
    assert not report.has_breaking_changes


def test_table_added(detector):
    baseline = make_snapshot("v1", {})
    current = make_snapshot("v2", {"orders": {"id": {"data_type": "integer"}}})
    report = detector.detect(baseline, current)
    assert len(report.table_drifts) == 1
    assert report.table_drifts[0].change_type == ChangeType.ADDED
    assert not report.has_breaking_changes


def test_table_removed_is_breaking(detector):
    baseline = make_snapshot("v1", {"orders": {"id": {"data_type": "integer"}}})
    current = make_snapshot("v2", {})
    report = detector.detect(baseline, current)
    assert report.table_drifts[0].change_type == ChangeType.REMOVED
    assert report.has_breaking_changes


def test_column_added(detector):
    baseline = make_snapshot("v1", {"users": {"id": {"data_type": "integer"}}})
    current = make_snapshot(
        "v2",
        {"users": {"id": {"data_type": "integer"}, "email": {"data_type": "varchar"}}},
    )
    report = detector.detect(baseline, current)
    assert len(report.table_drifts) == 1
    col_drift = report.table_drifts[0].column_drifts[0]
    assert col_drift.change_type == ChangeType.ADDED
    assert col_drift.column == "email"
    assert not report.has_breaking_changes


def test_column_removed_is_breaking(detector):
    baseline = make_snapshot(
        "v1",
        {"users": {"id": {"data_type": "integer"}, "email": {"data_type": "varchar"}}},
    )
    current = make_snapshot("v2", {"users": {"id": {"data_type": "integer"}}})
    report = detector.detect(baseline, current)
    assert report.has_breaking_changes


def test_column_type_change_is_breaking(detector):
    baseline = make_snapshot("v1", {"users": {"age": {"data_type": "integer"}}})
    current = make_snapshot("v2", {"users": {"age": {"data_type": "varchar"}}})
    report = detector.detect(baseline, current)
    col_drift = report.table_drifts[0].column_drifts[0]
    assert col_drift.change_type == ChangeType.MODIFIED
    assert report.has_breaking_changes


def test_report_metadata(detector):
    baseline = make_snapshot("snapshot-2024-01", {})
    current = make_snapshot("snapshot-2024-02", {})
    report = detector.detect(baseline, current)
    assert report.baseline_snapshot == "snapshot-2024-01"
    assert report.current_snapshot == "snapshot-2024-02"
    assert report.generated_at is not None
