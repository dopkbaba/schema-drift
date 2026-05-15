"""Annotates drift reports with human-readable descriptions and remediation hints."""
from dataclasses import dataclass, field
from typing import List, Optional

from schema_drift.models import ChangeType, DriftReport, SchemaChange


_HINTS: dict[ChangeType, str] = {
    ChangeType.TABLE_ADDED: "Ensure downstream consumers are aware of the new table.",
    ChangeType.TABLE_REMOVED: "This is a breaking change. Verify no active queries reference this table.",
    ChangeType.COLUMN_ADDED: "New column added. Check for NOT NULL constraints without defaults.",
    ChangeType.COLUMN_REMOVED: "Breaking change. Update all queries and ORM models referencing this column.",
    ChangeType.TYPE_CHANGED: "Data type changed. Validate compatibility with existing application logic.",
    ChangeType.NULLABLE_CHANGED: "Nullability changed. Ensure application handles the new constraint correctly.",
}

_DESCRIPTIONS: dict[ChangeType, str] = {
    ChangeType.TABLE_ADDED: "A new table was introduced in the latest snapshot.",
    ChangeType.TABLE_REMOVED: "A table present in the baseline no longer exists.",
    ChangeType.COLUMN_ADDED: "A column was added to an existing table.",
    ChangeType.COLUMN_REMOVED: "A column was removed from an existing table.",
    ChangeType.TYPE_CHANGED: "The data type of a column was modified.",
    ChangeType.NULLABLE_CHANGED: "The nullable property of a column was modified.",
}


@dataclass
class AnnotatedChange:
    change: SchemaChange
    description: str
    hint: str
    severity: str

    def to_dict(self) -> dict:
        return {
            "change": self.change.to_dict(),
            "description": self.description,
            "hint": self.hint,
            "severity": self.severity,
        }


@dataclass
class AnnotationResult:
    annotated: List[AnnotatedChange] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.annotated)

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "annotated": [a.to_dict() for a in self.annotated],
        }


def _severity_for(change: SchemaChange) -> str:
    if change.breaking:
        return "critical" if change.change_type in (ChangeType.TABLE_REMOVED, ChangeType.COLUMN_REMOVED) else "high"
    return "low"


def annotate_report(report: DriftReport) -> AnnotationResult:
    """Annotate every change in *report* with a description and remediation hint."""
    result = AnnotationResult()
    for change in report.changes:
        desc = _DESCRIPTIONS.get(change.change_type, "Schema change detected.")
        hint = _HINTS.get(change.change_type, "Review the change carefully before deploying.")
        severity = _severity_for(change)
        result.annotated.append(AnnotatedChange(change=change, description=desc, hint=hint, severity=severity))
    return result
