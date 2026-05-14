"""Tests for schema_drift.scorer."""

import pytest

from schema_drift.models import ChangeType, SchemaChange, DriftReport
from schema_drift.scorer import score_report, DriftScore, _riskier_than


def make_change(change_type: ChangeType) -> SchemaChange:
    return SchemaChange(
        table="orders",
        change_type=change_type,
        description=f"{change_type.value} on orders",
        is_breaking=change_type
        in {
            ChangeType.TABLE_REMOVED,
            ChangeType.COLUMN_REMOVED,
            ChangeType.TYPE_CHANGED,
        },
    )


def make_report(*change_types: ChangeType) -> DriftReport:
    changes = [make_change(ct) for ct in change_types]
    return DriftReport(changes=changes)


def test_empty_report_scores_zero():
    report = make_report()
    score = score_report(report)
    assert score.total == 0.0
    assert score.risk_level == "low"
    assert score.breakdown == {}


def test_single_table_removed_is_critical():
    report = make_report(ChangeType.TABLE_REMOVED, ChangeType.TABLE_REMOVED)
    score = score_report(report)
    assert score.total == 20.0
    assert score.risk_level == "critical"


def test_column_added_scores_low():
    report = make_report(ChangeType.COLUMN_ADDED)
    score = score_report(report)
    assert score.total == 2.0
    assert score.risk_level == "low"


def test_breakdown_aggregates_by_type():
    report = make_report(
        ChangeType.COLUMN_REMOVED,
        ChangeType.COLUMN_REMOVED,
        ChangeType.TYPE_CHANGED,
    )
    score = score_report(report)
    assert score.breakdown[ChangeType.COLUMN_REMOVED.value] == 16.0
    assert score.breakdown[ChangeType.TYPE_CHANGED.value] == 7.0
    assert score.total == 23.0
    assert score.risk_level == "critical"


def test_medium_risk_threshold():
    # nullable_changed = 5.0, column_added = 2.0 => total 7 => medium
    report = make_report(ChangeType.NULLABLE_CHANGED, ChangeType.COLUMN_ADDED)
    score = score_report(report)
    assert score.risk_level == "medium"


def test_to_dict_contains_expected_keys():
    score = DriftScore(total=5.0, risk_level="medium", breakdown={"col_removed": 5.0})
    d = score.to_dict()
    assert set(d.keys()) == {"total", "risk_level", "breakdown"}


def test_riskier_than_low_includes_all():
    result = _riskier_than("low")
    assert result == ["low", "medium", "high", "critical"]


def test_riskier_than_critical_includes_only_critical():
    result = _riskier_than("critical")
    assert result == ["critical"]
