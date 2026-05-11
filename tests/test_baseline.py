"""Tests for schema_drift.baseline.BaselineManager."""

import json
import os
import pytest

from schema_drift.baseline import BaselineManager
from schema_drift.models import ColumnSchema, DatabaseSnapshot, TableSchema


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_snapshot(name: str = "db") -> DatabaseSnapshot:
    col = ColumnSchema(name="id", data_type="integer", nullable=False)
    table = TableSchema(name="users", columns=[col])
    return DatabaseSnapshot(name=name, tables=[table])


@pytest.fixture()
def mgr(tmp_path):
    return BaselineManager(baseline_dir=str(tmp_path / ".schema_drift"))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_exists_returns_false_when_no_baseline(mgr):
    assert mgr.exists() is False


def test_save_creates_file(mgr):
    snap = make_snapshot()
    path = mgr.save(snap)
    assert os.path.exists(path)


def test_save_returns_correct_path(mgr, tmp_path):
    snap = make_snapshot()
    path = mgr.save(snap)
    assert path.endswith("baseline.json")


def test_exists_returns_true_after_save(mgr):
    mgr.save(make_snapshot())
    assert mgr.exists() is True


def test_load_raises_when_missing(mgr):
    with pytest.raises(FileNotFoundError, match="No baseline found"):
        mgr.load()


def test_save_and_load_roundtrip(mgr):
    original = make_snapshot("prod")
    mgr.save(original)
    loaded = mgr.load()
    assert loaded.name == "prod"
    assert len(loaded.tables) == 1
    assert loaded.tables[0].name == "users"
    assert loaded.tables[0].columns[0].data_type == "integer"


def test_save_stores_label(mgr, tmp_path):
    mgr.save(make_snapshot(), label="v1.2.0")
    raw = json.loads(open(mgr._baseline_path).read())
    assert raw["label"] == "v1.2.0"


def test_metadata_returns_saved_at_and_label(mgr):
    mgr.save(make_snapshot(), label="release")
    meta = mgr.metadata()
    assert "saved_at" in meta
    assert meta["label"] == "release"


def test_metadata_raises_when_missing(mgr):
    with pytest.raises(FileNotFoundError):
        mgr.metadata()


def test_save_overwrites_previous_baseline(mgr):
    mgr.save(make_snapshot("first"))
    mgr.save(make_snapshot("second"))
    loaded = mgr.load()
    assert loaded.name == "second"
