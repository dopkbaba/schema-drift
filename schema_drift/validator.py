"""Validates a DriftReport against a set of user-defined rules.

A ValidationRule specifies a maximum allowed count for a given ChangeType
(or for breaking changes in general).  validate_report returns a
ValidationResult that lists every rule that was violated.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from schema_drift.models import ChangeType, DriftReport


@dataclass
class ValidationRule:
    """A single threshold rule."""
    name: str
    change_type: Optional[ChangeType] = None  # None means "any breaking change"
    max_allowed: int = 0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "change_type": self.change_type.value if self.change_type else None,
            "max_allowed": self.max_allowed,
        }


@dataclass
class RuleViolation:
    rule: ValidationRule
    actual: int

    def to_dict(self) -> dict:
        return {
            "rule": self.rule.to_dict(),
            "actual": self.actual,
            "message": (
                f"Rule '{self.rule.name}' violated: "
                f"found {self.actual}, max allowed {self.rule.max_allowed}"
            ),
        }


@dataclass
class ValidationResult:
    violations: List[RuleViolation] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.violations) == 0

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "violation_count": len(self.violations),
            "violations": [v.to_dict() for v in self.violations],
        }


def validate_report(
    report: DriftReport,
    rules: List[ValidationRule],
) -> ValidationResult:
    """Check *report* against every rule and return a ValidationResult."""
    violations: List[RuleViolation] = []

    all_changes = [
        change
        for table_changes in report.changes.values()
        for change in table_changes
    ]

    for rule in rules:
        if rule.change_type is None:
            # Count all breaking changes
            count = sum(1 for c in all_changes if c.breaking)
        else:
            count = sum(
                1 for c in all_changes if c.change_type == rule.change_type
            )

        if count > rule.max_allowed:
            violations.append(RuleViolation(rule=rule, actual=count))

    return ValidationResult(violations=violations)
