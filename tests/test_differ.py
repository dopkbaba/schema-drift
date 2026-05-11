"""Tests for schema_drift.differ module."""

import pytest
from unittest.mock import MagicMock
from schema_drift.models import ChangeType
from schema_drift.differ import summarize_changes, diff_columns


def make_change(change_type: ChangeType, table: str, column: str = None, breaking: bool = False, detail: str = ""):
    change = MagicMock()
    change.change_type = change_type
    change.table_name = table
    change.column_name = column
    change.breaking = breaking
    change.detail = detail
    return change


class TestSummarizeChanges:
    def test_empty_changes(self):
        summary = summarize_changes([])
        assert summary["total"] == 0
        assert summary["breaking"] == 0
        assert summary["by_type"] == {}
        assert summary["by_table"] == {}

    def test_counts_total_and_breaking(self):
        changes = [
            make_change(ChangeType.COLUMN_REMOVED, "users", "email", breaking=True),
            make_change(ChangeType.COLUMN_ADDED, "users", "phone", breaking=False),
            make_change(ChangeType.TABLE_REMOVED, "orders", breaking=True),
        ]
        summary = summarize_changes(changes)
        assert summary["total"] == 3
        assert summary["breaking"] == 2

    def test_groups_by_type(self):
        changes = [
            make_change(ChangeType.COLUMN_ADDED, "users", "x"),
            make_change(ChangeType.COLUMN_ADDED, "orders", "y"),
            make_change(ChangeType.COLUMN_REMOVED, "users", "z", breaking=True),
        ]
        summary = summarize_changes(changes)
        assert summary["by_type"][ChangeType.COLUMN_ADDED.value] == 2
        assert summary["by_type"][ChangeType.COLUMN_REMOVED.value] == 1

    def test_groups_by_table(self):
        changes = [
            make_change(ChangeType.COLUMN_ADDED, "users", "x"),
            make_change(ChangeType.COLUMN_REMOVED, "users", "z", breaking=True),
            make_change(ChangeType.TABLE_ADDED, "orders"),
        ]
        summary = summarize_changes(changes)
        assert len(summary["by_table"]["users"]) == 2
        assert len(summary["by_table"]["orders"]) == 1


class TestDiffColumns:
    OLD = {
        "id": {"data_type": "integer", "nullable": False},
        "email": {"data_type": "varchar", "nullable": True},
        "age": {"data_type": "integer", "nullable": True},
    }
    NEW = {
        "id": {"data_type": "integer", "nullable": False},
        "email": {"data_type": "text", "nullable": True},  # type changed
        "phone": {"data_type": "varchar", "nullable": True},  # added
        # age removed
    }

    def test_detects_added_column(self):
        diffs = diff_columns("users", self.OLD, self.NEW)
        added = [d for d in diffs if d["status"] == "added"]
        assert len(added) == 1
        assert added[0]["column"] == "phone"

    def test_detects_removed_column(self):
        diffs = diff_columns("users", self.OLD, self.NEW)
        removed = [d for d in diffs if d["status"] == "removed"]
        assert len(removed) == 1
        assert removed[0]["column"] == "age"

    def test_detects_modified_column(self):
        diffs = diff_columns("users", self.OLD, self.NEW)
        modified = [d for d in diffs if d["status"] == "modified"]
        assert len(modified) == 1
        assert modified[0]["column"] == "email"

    def test_no_diff_when_identical(self):
        diffs = diff_columns("users", self.OLD, self.OLD)
        assert diffs == []

    def test_nullable_change_detected(self):
        old = {"id": {"data_type": "integer", "nullable": True}}
        new = {"id": {"data_type": "integer", "nullable": False}}
        diffs = diff_columns("users", old, new)
        assert len(diffs) == 1
        assert diffs[0]["status"] == "modified"
