"""Filter drift reports by table name patterns or change types."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from typing import List, Optional

from schema_drift.models import DriftReport, SchemaChange, ChangeType


@dataclass
class FilterConfig:
    """Configuration for filtering drift results."""

    include_tables: List[str] = field(default_factory=list)
    exclude_tables: List[str] = field(default_factory=list)
    change_types: List[ChangeType] = field(default_factory=list)
    breaking_only: bool = False

    def matches_table(self, table_name: str) -> bool:
        """Return True if the table name passes include/exclude rules."""
        if self.include_tables:
            if not any(fnmatch.fnmatch(table_name, pat) for pat in self.include_tables):
                return False
        if self.exclude_tables:
            if any(fnmatch.fnmatch(table_name, pat) for pat in self.exclude_tables):
                return False
        return True

    def matches_change(self, change: SchemaChange) -> bool:
        """Return True if the change passes type and breaking filters."""
        if self.breaking_only and not change.breaking:
            return False
        if self.change_types and change.change_type not in self.change_types:
            return False
        return True


def filter_report(report: DriftReport, config: FilterConfig) -> DriftReport:
    """Return a new DriftReport containing only changes that match the filter."""
    filtered_changes: List[SchemaChange] = [
        change
        for change in report.changes
        if config.matches_table(change.table) and config.matches_change(change)
    ]
    return DriftReport(
        changes=filtered_changes,
        generated_at=report.generated_at,
    )
