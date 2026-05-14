"""Tests for schema_drift.tagger."""

from __future__ import annotations

import pytest

from schema_drift.models import ChangeType, DriftReport, SchemaChange
from schema_drift.tagger import (
    TAG_ADDITIVE,
    TAG_CLEAN,
    TAG_DESTRUCTIVE,
    TAG_NULLABLE_CHANGE,
    TAG_TYPE_CHANGE,
    tag_report,
)


def make_change(change_type: ChangeType, table: str = "t") -> SchemaChange:
    return SchemaChange(
        table=table,
        change_type=change_type,
        description="test change",
        is_breaking=change_type
        in (
            ChangeType.TABLE_REMOVED,
            ChangeType.COLUMN_REMOVED,
            ChangeType.COLUMN_TYPE_CHANGED,
        ),
    )


def make_report(*changes: SchemaChange) -> DriftReport:
    return DriftReport(changes=list(changes))


def test_empty_report_is_clean():
    result = tag_report(make_report())
    assert result.primary_tag == TAG_CLEAN
    assert TAG_CLEAN in result.tags


def test_table_removed_is_destructive():
    result = tag_report(make_report(make_change(ChangeType.TABLE_REMOVED)))
    assert result.primary_tag == TAG_DESTRUCTIVE
    assert TAG_DESTRUCTIVE in result.tags


def test_column_removed_is_destructive():
    result = tag_report(make_report(make_change(ChangeType.COLUMN_REMOVED)))
    assert TAG_DESTRUCTIVE in result.tags


def test_column_added_is_additive():
    result = tag_report(make_report(make_change(ChangeType.COLUMN_ADDED)))
    assert result.primary_tag == TAG_ADDITIVE
    assert TAG_ADDITIVE in result.tags


def test_type_change_tag():
    result = tag_report(make_report(make_change(ChangeType.COLUMN_TYPE_CHANGED)))
    assert TAG_TYPE_CHANGE in result.tags
    assert result.primary_tag == TAG_TYPE_CHANGE


def test_nullable_change_tag():
    result = tag_report(make_report(make_change(ChangeType.COLUMN_NULLABLE_CHANGED)))
    assert TAG_NULLABLE_CHANGE in result.tags


def test_destructive_wins_over_additive():
    report = make_report(
        make_change(ChangeType.COLUMN_ADDED),
        make_change(ChangeType.TABLE_REMOVED),
    )
    result = tag_report(report)
    assert result.primary_tag == TAG_DESTRUCTIVE
    assert TAG_ADDITIVE in result.tags
    assert TAG_DESTRUCTIVE in result.tags


def test_to_dict_contains_expected_keys():
    result = tag_report(make_report())
    d = result.to_dict()
    assert "primary_tag" in d
    assert "tags" in d
    assert isinstance(d["tags"], list)
