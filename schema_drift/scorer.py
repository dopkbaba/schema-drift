"""Scores the severity of a drift report as a numeric risk value."""

from dataclasses import dataclass
from typing import List

from schema_drift.models import DriftReport, ChangeType

# Weights assigned to each change type for risk scoring
_WEIGHTS: dict[ChangeType, float] = {
    ChangeType.TABLE_REMOVED: 10.0,
    ChangeType.COLUMN_REMOVED: 8.0,
    ChangeType.TYPE_CHANGED: 7.0,
    ChangeType.NULLABLE_CHANGED: 5.0,
    ChangeType.COLUMN_ADDED: 2.0,
    ChangeType.TABLE_ADDED: 1.0,
}

_RISK_THRESHOLDS = [
    (20.0, "critical"),
    (10.0, "high"),
    (4.0, "medium"),
    (0.0, "low"),
]


@dataclass
class DriftScore:
    total: float
    risk_level: str
    breakdown: dict[str, float]

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "risk_level": self.risk_level,
            "breakdown": self.breakdown,
        }


def score_report(report: DriftReport) -> DriftScore:
    """Compute a numeric risk score for a drift report."""
    breakdown: dict[str, float] = {}
    total = 0.0

    for change in report.changes:
        weight = _WEIGHTS.get(change.change_type, 1.0)
        key = change.change_type.value
        breakdown[key] = breakdown.get(key, 0.0) + weight
        total += weight

    risk_level = "low"
    for threshold, label in _RISK_THRESHOLDS:
        if total >= threshold:
            risk_level = label
            break

    return DriftScore(total=round(total, 2), risk_level=risk_level, breakdown=breakdown)
