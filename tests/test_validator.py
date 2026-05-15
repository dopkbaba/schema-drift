"""Tests for schema_drift.validator."""

from __future__ import annotations

import pytest

from schema_drift.models import ChangeType, DriftReport, SchemaChange
from schema_drift.validator import (
    ValidationRule,
    ValidationResult,
    validate_report,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_change(
    change_type: ChangeType = ChangeType.COLUMN_REMOVED,
    breaking: bool = True,
    table: str = "users",
) -> SchemaChange:
    return SchemaChange(
        table=table,
        change_type=change_type,
        description="test change",
        breaking=breaking,
    )


def make_report(*changes: SchemaChange) -> DriftReport:
    report: dict = {}
    for c in changes:
        report.setdefault(c.table, []).append(c)
    return DriftReport(changes=report)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_empty_report_passes_all_rules():
    rules = [
        ValidationRule(name="no_breaking", change_type=None, max_allowed=0),
        ValidationRule(name="no_removed", change_type=ChangeType.COLUMN_REMOVED, max_allowed=0),
    ]
    result = validate_report(make_report(), rules)
    assert result.passed
    assert result.violations == []


def test_no_rules_always_passes():
    report = make_report(make_change())
    result = validate_report(report, rules=[])
    assert result.passed


def test_breaking_change_violates_zero_tolerance_rule():
    report = make_report(make_change(breaking=True))
    rules = [ValidationRule(name="no_breaking", change_type=None, max_allowed=0)]
    result = validate_report(report, rules)
    assert not result.passed
    assert len(result.violations) == 1
    assert result.violations[0].actual == 1


def test_non_breaking_change_does_not_violate_breaking_rule():
    report = make_report(make_change(change_type=ChangeType.COLUMN_ADDED, breaking=False))
    rules = [ValidationRule(name="no_breaking", change_type=None, max_allowed=0)]
    result = validate_report(report, rules)
    assert result.passed


def test_specific_change_type_rule_only_counts_that_type():
    report = make_report(
        make_change(change_type=ChangeType.COLUMN_REMOVED, breaking=True),
        make_change(change_type=ChangeType.COLUMN_ADDED, breaking=False),
    )
    rules = [
        ValidationRule(name="max_one_removed", change_type=ChangeType.COLUMN_REMOVED, max_allowed=1),
    ]
    result = validate_report(report, rules)
    assert result.passed


def test_exceeding_specific_type_limit_is_violation():
    report = make_report(
        make_change(change_type=ChangeType.COLUMN_REMOVED, table="a"),
        make_change(change_type=ChangeType.COLUMN_REMOVED, table="b"),
    )
    rules = [
        ValidationRule(name="max_one_removed", change_type=ChangeType.COLUMN_REMOVED, max_allowed=1),
    ]
    result = validate_report(report, rules)
    assert not result.passed
    assert result.violations[0].actual == 2


def test_to_dict_structure():
    report = make_report(make_change())
    rules = [ValidationRule(name="no_breaking", change_type=None, max_allowed=0)]
    result = validate_report(report, rules)
    d = result.to_dict()
    assert "passed" in d
    assert "violation_count" in d
    assert "violations" in d
    assert d["violations"][0]["rule"]["name"] == "no_breaking"
