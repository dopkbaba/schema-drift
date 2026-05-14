"""Tests for schema_drift.watcher."""

from __future__ import annotations

import os
import tempfile
from unittest.mock import MagicMock

import pytest

from schema_drift.baseline import BaselineManager
from schema_drift.models import ColumnSchema, SchemaSnapshot, TableSchema
from schema_drift.watcher import SchemaWatcher, WatchConfig


def make_snapshot(tables: dict | None = None) -> SchemaSnapshot:
    tables = tables or {}
    return SchemaSnapshot(
        tables={
            name: TableSchema(
                name=name,
                columns={c: ColumnSchema(name=c, data_type="int", nullable=False) for c in cols},
            )
            for name, cols in tables.items()
        }
    )


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture
def baseline_snapshot():
    return make_snapshot({"users": ["id", "email"]})


@pytest.fixture
def watcher_with_baseline(tmp_dir, baseline_snapshot):
    mgr = BaselineManager(tmp_dir)
    mgr.save(baseline_snapshot, "default")
    cfg = WatchConfig(
        baseline_dir=tmp_dir,
        baseline_name="default",
        interval_seconds=0,
        max_iterations=1,
    )
    return SchemaWatcher(cfg)


def test_no_drift_returns_empty_reports(watcher_with_baseline, baseline_snapshot):
    result = watcher_with_baseline.watch(lambda: baseline_snapshot)
    assert result.iterations == 1
    assert result.drift_detected_count == 0
    assert result.reports == []


def test_drift_detected_increments_count(watcher_with_baseline):
    changed = make_snapshot({"users": ["id"]})  # email column removed
    result = watcher_with_baseline.watch(lambda: changed)
    assert result.drift_detected_count == 1
    assert len(result.reports) == 1


def test_on_drift_callback_called(watcher_with_baseline):
    callback = MagicMock()
    watcher_with_baseline._config.on_drift = callback
    changed = make_snapshot({"users": ["id"]})
    watcher_with_baseline.watch(lambda: changed)
    callback.assert_called_once()


def test_on_no_drift_callback_called(watcher_with_baseline, baseline_snapshot):
    callback = MagicMock()
    watcher_with_baseline._config.on_no_drift = callback
    watcher_with_baseline.watch(lambda: baseline_snapshot)
    callback.assert_called_once()


def test_multiple_iterations(tmp_dir, baseline_snapshot):
    mgr = BaselineManager(tmp_dir)
    mgr.save(baseline_snapshot, "default")
    cfg = WatchConfig(
        baseline_dir=tmp_dir,
        baseline_name="default",
        interval_seconds=0,
        max_iterations=3,
    )
    watcher = SchemaWatcher(cfg)
    result = watcher.watch(lambda: baseline_snapshot)
    assert result.iterations == 3


def test_raises_when_no_baseline(tmp_dir, baseline_snapshot):
    cfg = WatchConfig(
        baseline_dir=tmp_dir,
        baseline_name="missing",
        interval_seconds=0,
        max_iterations=1,
    )
    watcher = SchemaWatcher(cfg)
    with pytest.raises(FileNotFoundError, match="missing"):
        watcher.watch(lambda: baseline_snapshot)


def test_drift_report_contains_expected_table(watcher_with_baseline):
    """Verify that the drift report references the table where drift occurred."""
    changed = make_snapshot({"users": ["id"]})  # email column removed
    result = watcher_with_baseline.watch(lambda: changed)
    assert len(result.reports) == 1
    report = result.reports[0]
    assert "users" in report.changes
