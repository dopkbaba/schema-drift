"""Summarizes drift reports into human-readable digests."""

from dataclasses import dataclass, field
from typing import List, Dict

from schema_drift.models import DriftReport, ChangeType
from schema_drift.scorer import score_report, DriftScore


@dataclass
class TableDigest:
    table: str
    breaking: int
    non_breaking: int
    change_types: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "table": self.table,
            "breaking": self.breaking,
            "non_breaking": self.non_breaking,
            "change_types": self.change_types,
        }


@dataclass
class DriftSummary:
    total_tables_affected: int
    total_changes: int
    total_breaking: int
    risk_level: str
    score: float
    top_tables: List[TableDigest] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "total_tables_affected": self.total_tables_affected,
            "total_changes": self.total_changes,
            "total_breaking": self.total_breaking,
            "risk_level": self.risk_level,
            "score": self.score,
            "top_tables": [t.to_dict() for t in self.top_tables],
        }


def summarize_report(report: DriftReport, top_n: int = 5) -> DriftSummary:
    """Produce a concise summary of a drift report."""
    drift_score: DriftScore = score_report(report)

    table_map: Dict[str, TableDigest] = {}
    for change in report.changes:
        tbl = change.table
        if tbl not in table_map:
            table_map[tbl] = TableDigest(table=tbl, breaking=0, non_breaking=0)
        digest = table_map[tbl]
        if change.breaking:
            digest.breaking += 1
        else:
            digest.non_breaking += 1
        label = change.change_type.value if hasattr(change.change_type, "value") else str(change.change_type)
        if label not in digest.change_types:
            digest.change_types.append(label)

    sorted_tables = sorted(
        table_map.values(),
        key=lambda d: (d.breaking, d.non_breaking),
        reverse=True,
    )

    return DriftSummary(
        total_tables_affected=len(table_map),
        total_changes=drift_score.total_changes,
        total_breaking=drift_score.breaking_changes,
        risk_level=drift_score.risk_level,
        score=drift_score.score,
        top_tables=sorted_tables[:top_n],
    )
