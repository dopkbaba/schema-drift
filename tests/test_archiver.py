"""Tests for SnapshotArchiver."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from schema_drift.archiver import SnapshotArchiver
from schema_drift.models import ColumnSchema, DatabaseSnapshot, TableSchema


def make_snapshot(table_name: str = "users") -> DatabaseSnapshot:
    col = ColumnSchema(name="id", data_type="integer", nullable=False)
    table = TableSchema(name=table_name, columns=[col])
    return DatabaseSnapshot(tables={table_name: table})


@pytest.fixture
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path / "archive"


@pytest.fixture
def archiver(tmp_dir: Path) -> SnapshotArchiver:
    return SnapshotArchiver(archive_dir=tmp_dir)


def test_new_archiver_has_no_entries(archiver: SnapshotArchiver) -> None:
    assert archiver.list_entries() == []


def test_save_creates_entry(archiver: SnapshotArchiver) -> None:
    snap = make_snapshot()
    entry = archiver.save(snap, label="v1")
    assert entry.label == "v1"
    assert entry.snapshot_id != ""
    assert Path(entry.path).exists()


def test_save_persists_to_index(archiver: SnapshotArchiver, tmp_dir: Path) -> None:
    snap = make_snapshot()
    archiver.save(snap, label="release-1")
    # Re-load archiver from same dir
    fresh = SnapshotArchiver(archive_dir=tmp_dir)
    entries = fresh.list_entries()
    assert len(entries) == 1
    assert entries[0].label == "release-1"


def test_multiple_saves_accumulate(archiver: SnapshotArchiver) -> None:
    archiver.save(make_snapshot("orders"), label="a")
    archiver.save(make_snapshot("products"), label="b")
    assert len(archiver.list_entries()) == 2


def test_load_returns_correct_snapshot(archiver: SnapshotArchiver) -> None:
    snap = make_snapshot("payments")
    entry = archiver.save(snap, label="pay-v1")
    loaded = archiver.load(entry.snapshot_id)
    assert loaded is not None
    assert "payments" in loaded.tables


def test_load_unknown_id_returns_none(archiver: SnapshotArchiver) -> None:
    result = archiver.load("nonexistent_id")
    assert result is None


def test_latest_returns_last_saved(archiver: SnapshotArchiver) -> None:
    archiver.save(make_snapshot("a"), label="first")
    archiver.save(make_snapshot("b"), label="second")
    latest = archiver.latest()
    assert latest is not None
    assert latest.label == "second"


def test_latest_on_empty_returns_none(archiver: SnapshotArchiver) -> None:
    assert archiver.latest() is None


def test_archive_dir_created_automatically(tmp_path: Path) -> None:
    deep = tmp_path / "a" / "b" / "c"
    arch = SnapshotArchiver(archive_dir=deep)
    assert deep.exists()
