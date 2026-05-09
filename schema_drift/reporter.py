"""Formats and outputs drift detection results in various formats."""

from __future__ import annotations

import json
from typing import List

from schema_drift.models import DriftReport, ChangeType


class DriftReporter:
    """Renders a DriftReport as plain text, JSON, or Markdown."""

    BREAKING_LABEL = "[BREAKING]"
    WARNING_LABEL = "[WARNING]"
    INFO_LABEL = "[INFO]   "

    def _severity_label(self, change_type: ChangeType) -> str:
        if change_type in (
            ChangeType.TABLE_REMOVED,
            ChangeType.COLUMN_REMOVED,
            ChangeType.COLUMN_TYPE_CHANGED,
            ChangeType.COLUMN_NULLABLE_CHANGED,
        ):
            return self.BREAKING_LABEL
        if change_type == ChangeType.TABLE_ADDED:
            return self.INFO_LABEL
        return self.WARNING_LABEL

    def as_text(self, report: DriftReport) -> str:
        if not report.changes:
            return "No schema drift detected."
        lines = [f"Schema drift detected: {len(report.changes)} change(s)\n"]
        for change in report.changes:
            label = self._severity_label(change.change_type)
            lines.append(
                f"  {label} [{change.table}] {change.change_type.value}"
                + (f" — {change.detail}" if change.detail else "")
            )
        return "\n".join(lines)

    def as_json(self, report: DriftReport) -> str:
        return json.dumps(
            {
                "has_breaking_changes": report.has_breaking_changes,
                "total_changes": len(report.changes),
                "changes": [
                    {
                        "table": c.table,
                        "change_type": c.change_type.value,
                        "detail": c.detail,
                        "is_breaking": c.is_breaking,
                    }
                    for c in report.changes
                ],
            },
            indent=2,
        )

    def as_markdown(self, report: DriftReport) -> str:
        if not report.changes:
            return "## Schema Drift Report\n\n✅ No schema drift detected."
        lines = [
            "## Schema Drift Report\n",
            f"**{len(report.changes)} change(s) detected** "
            f"{'— ⚠️ Breaking changes present' if report.has_breaking_changes else ''}\n",
            "| Table | Change | Detail | Breaking |",
            "|-------|--------|--------|----------|",
        ]
        for c in report.changes:
            breaking = "❌ Yes" if c.is_breaking else "✅ No"
            lines.append(
                f"| {c.table} | {c.change_type.value} | {c.detail or ''} | {breaking} |"
            )
        return "\n".join(lines)
