"""Tests for schema_drift.annotator."""
import pytest

from schema_drift.annotator import AnnotatedChange, annotate_report
from schema_drift.models import ChangeType, DriftReport, SchemaChange


def make_change(
    change_type: ChangeType = ChangeType.COLUMN_REMOVED,
    table: str = "users",
    column: str | None = "email",
    breaking: bool = True,
) -> SchemaChange:
    return SchemaChange(table=table, column=column, change_type=change_type, breaking=breaking)


def make_report(*changes: SchemaChange) -> DriftReport:
    return DriftReport(changes=list(changes))


def test_empty_report_returns_zero_annotations():
    result = annotate_report(make_report())
    assert result.total == 0
    assert result.annotated == []


def test_single_column_removed_annotated():
    report = make_report(make_change(ChangeType.COLUMN_REMOVED, breaking=True))
    result = annotate_report(report)
    assert result.total == 1
    ann = result.annotated[0]
    assert ann.severity == "critical"
    assert "removed" in ann.description.lower()
    assert "breaking" in ann.hint.lower() or "update" in ann.hint.lower()


def test_table_removed_is_critical():
    report = make_report(make_change(ChangeType.TABLE_REMOVED, column=None, breaking=True))
    result = annotate_report(report)
    assert result.annotated[0].severity == "critical"


def test_table_added_is_low_severity():
    report = make_report(make_change(ChangeType.TABLE_ADDED, column=None, breaking=False))
    result = annotate_report(report)
    assert result.annotated[0].severity == "low"


def test_type_changed_breaking_is_high():
    report = make_report(make_change(ChangeType.TYPE_CHANGED, breaking=True))
    result = annotate_report(report)
    assert result.annotated[0].severity == "high"


def test_nullable_changed_non_breaking_is_low():
    report = make_report(make_change(ChangeType.NULLABLE_CHANGED, breaking=False))
    result = annotate_report(report)
    assert result.annotated[0].severity == "low"


def test_to_dict_structure():
    report = make_report(make_change(ChangeType.COLUMN_ADDED, breaking=False))
    result = annotate_report(report)
    d = result.to_dict()
    assert d["total"] == 1
    ann_dict = d["annotated"][0]
    assert "description" in ann_dict
    assert "hint" in ann_dict
    assert "severity" in ann_dict
    assert "change" in ann_dict


def test_multiple_changes_all_annotated():
    report = make_report(
        make_change(ChangeType.COLUMN_REMOVED, breaking=True),
        make_change(ChangeType.COLUMN_ADDED, breaking=False),
        make_change(ChangeType.TABLE_ADDED, column=None, breaking=False),
    )
    result = annotate_report(report)
    assert result.total == 3
    severities = {a.severity for a in result.annotated}
    assert "critical" in severities
    assert "low" in severities
