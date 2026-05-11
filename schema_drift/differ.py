"""Computes a human-readable diff summary between two snapshots."""

from typing import List, Dict, Any
from schema_drift.models import SchemaSnapshot, SchemaChange, ChangeType


def _type_changed(old: str, new: str) -> bool:
    return old.lower().strip() != new.lower().strip()


def _nullable_changed(old: bool, new: bool) -> bool:
    return old != new


def summarize_changes(changes: List[SchemaChange]) -> Dict[str, Any]:
    """Return a structured summary dict grouping changes by type and table."""
    summary: Dict[str, Any] = {
        "total": len(changes),
        "breaking": sum(1 for c in changes if c.breaking),
        "by_type": {},
        "by_table": {},
    }

    for change in changes:
        type_key = change.change_type.value
        summary["by_type"].setdefault(type_key, 0)
        summary["by_type"][type_key] += 1

        summary["by_table"].setdefault(change.table_name, [])
        summary["by_table"][change.table_name].append(
            {
                "type": type_key,
                "breaking": change.breaking,
                "column": change.column_name,
                "detail": change.detail,
            }
        )

    return summary


def diff_columns(
    table_name: str,
    old_columns: Dict[str, Any],
    new_columns: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Return a list of per-column diff records for display purposes."""
    diffs: List[Dict[str, Any]] = []

    all_cols = set(old_columns) | set(new_columns)
    for col in sorted(all_cols):
        if col not in old_columns:
            diffs.append(
                {"table": table_name, "column": col, "status": "added", "old": None, "new": new_columns[col]}
            )
        elif col not in new_columns:
            diffs.append(
                {"table": table_name, "column": col, "status": "removed", "old": old_columns[col], "new": None}
            )
        else:
            old_c = old_columns[col]
            new_c = new_columns[col]
            if _type_changed(old_c.get("data_type", ""), new_c.get("data_type", "")) or _nullable_changed(
                old_c.get("nullable", True), new_c.get("nullable", True)
            ):
                diffs.append(
                    {"table": table_name, "column": col, "status": "modified", "old": old_c, "new": new_c}
                )

    return diffs
