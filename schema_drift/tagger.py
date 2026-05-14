"""Assigns human-readable risk tags to drift reports based on change patterns."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from schema_drift.models import DriftReport, ChangeType


TAG_DESTRUCTIVE = "destructive"
TAG_ADDITIVE = "additive"
TAG_TYPE_CHANGE = "type-change"
TAG_NULLABLE_CHANGE = "nullable-change"
TAG_CLEAN = "clean"


@dataclass
class TagResult:
    tags: List[str] = field(default_factory=list)
    primary_tag: str = TAG_CLEAN

    def to_dict(self) -> dict:
        return {"primary_tag": self.primary_tag, "tags": sorted(self.tags)}


def tag_report(report: DriftReport) -> TagResult:
    """Analyse a DriftReport and return a TagResult with applicable tags."""
    tags: set[str] = set()

    for change in report.changes:
        ct = change.change_type
        if ct in (ChangeType.TABLE_REMOVED, ChangeType.COLUMN_REMOVED):
            tags.add(TAG_DESTRUCTIVE)
        if ct in (ChangeType.TABLE_ADDED, ChangeType.COLUMN_ADDED):
            tags.add(TAG_ADDITIVE)
        if ct == ChangeType.COLUMN_TYPE_CHANGED:
            tags.add(TAG_TYPE_CHANGE)
        if ct == ChangeType.COLUMN_NULLABLE_CHANGED:
            tags.add(TAG_NULLABLE_CHANGE)

    if not tags:
        return TagResult(tags=[TAG_CLEAN], primary_tag=TAG_CLEAN)

    # Priority order for primary tag
    priority = [
        TAG_DESTRUCTIVE,
        TAG_TYPE_CHANGE,
        TAG_NULLABLE_CHANGE,
        TAG_ADDITIVE,
    ]
    primary = next((t for t in priority if t in tags), TAG_ADDITIVE)
    return TagResult(tags=list(tags), primary_tag=primary)
