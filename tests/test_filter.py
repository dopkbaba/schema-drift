"""Tests for schema_drift.filter."""

from __future__ import annotations

import pytest

from schema_drift.filter import FilterConfig, filter_report
from schema_drift.models import ChangeType, DriftReport, SchemaChange


def make_change(
    table: str = "users",
    change_type: ChangeType = ChangeType.COLUMN_ADDED,
    breaking: bool = False,
) -> SchemaChange:
    return SchemaChange(
        table=table,
        change_type=change_type,
        description="test change",
        breaking=breaking,
    )


def make_report(*changes: SchemaChange) -> DriftReport:
    return DriftReport(changes=list(changes))


# ---------------------------------------------------------------------------
# FilterConfig.matches_table
# ---------------------------------------------------------------------------

class TestMatchesTable:
    def test_no_rules_matches_all(self):
        cfg = FilterConfig()
        assert cfg.matches_table("orders") is True

    def test_include_pattern_matches(self):
        cfg = FilterConfig(include_tables=["user*"])
        assert cfg.matches_table("users") is True
        assert cfg.matches_table("orders") is False

    def test_exclude_pattern_blocks(self):
        cfg = FilterConfig(exclude_tables=["tmp_*"])
        assert cfg.matches_table("tmp_cache") is False
        assert cfg.matches_table("users") is True

    def test_include_and_exclude_combined(self):
        cfg = FilterConfig(include_tables=["user*"], exclude_tables=["user_archive"])
        assert cfg.matches_table("users") is True
        assert cfg.matches_table("user_archive") is False


# ---------------------------------------------------------------------------
# FilterConfig.matches_change
# ---------------------------------------------------------------------------

class TestMatchesChange:
    def test_no_filters_matches_all(self):
        cfg = FilterConfig()
        assert cfg.matches_change(make_change()) is True

    def test_breaking_only_excludes_non_breaking(self):
        cfg = FilterConfig(breaking_only=True)
        assert cfg.matches_change(make_change(breaking=False)) is False
        assert cfg.matches_change(make_change(breaking=True)) is True

    def test_change_type_filter(self):
        cfg = FilterConfig(change_types=[ChangeType.COLUMN_REMOVED])
        assert cfg.matches_change(make_change(change_type=ChangeType.COLUMN_ADDED)) is False
        assert cfg.matches_change(make_change(change_type=ChangeType.COLUMN_REMOVED)) is True


# ---------------------------------------------------------------------------
# filter_report
# ---------------------------------------------------------------------------

class TestFilterReport:
    def test_empty_report_stays_empty(self):
        result = filter_report(make_report(), FilterConfig())
        assert result.changes == []

    def test_all_changes_pass_with_no_filters(self):
        report = make_report(
            make_change("users"),
            make_change("orders"),
        )
        result = filter_report(report, FilterConfig())
        assert len(result.changes) == 2

    def test_table_filter_applied(self):
        report = make_report(
            make_change("users"),
            make_change("orders"),
        )
        result = filter_report(report, FilterConfig(include_tables=["orders"]))
        assert len(result.changes) == 1
        assert result.changes[0].table == "orders"

    def test_breaking_only_filter(self):
        report = make_report(
            make_change(breaking=True),
            make_change(breaking=False),
        )
        result = filter_report(report, FilterConfig(breaking_only=True))
        assert len(result.changes) == 1
        assert result.changes[0].breaking is True

    def test_preserves_generated_at(self):
        report = make_report()
        report.generated_at = "2024-01-01T00:00:00"
        result = filter_report(report, FilterConfig())
        assert result.generated_at == "2024-01-01T00:00:00"
