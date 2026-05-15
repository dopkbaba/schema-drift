"""Policy-based drift evaluation: apply rules to flag changes as ignored, warned, or blocked."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from schema_drift.models import ChangeType, SchemaChange


@dataclass
class PolicyRule:
    """A single rule that matches changes and assigns a disposition."""

    change_types: List[ChangeType]
    table_pattern: Optional[str] = None  # fnmatch-style, None = match all
    disposition: str = "warn"  # "ignore" | "warn" | "block"

    def matches(self, change: SchemaChange) -> bool:
        import fnmatch

        if change.change_type not in self.change_types:
            return False
        if self.table_pattern is not None:
            return fnmatch.fnmatch(change.table, self.table_pattern)
        return True


@dataclass
class PolicyConfig:
    """Collection of rules evaluated in order; first match wins."""

    rules: List[PolicyRule] = field(default_factory=list)
    default_disposition: str = "warn"  # applied when no rule matches


@dataclass
class PolicyResult:
    change: SchemaChange
    disposition: str  # "ignore" | "warn" | "block"
    matched_rule: Optional[PolicyRule] = None

    def to_dict(self) -> dict:
        return {
            "table": self.change.table,
            "change_type": self.change.change_type.value,
            "disposition": self.disposition,
        }


def apply_policy(changes: List[SchemaChange], config: PolicyConfig) -> List[PolicyResult]:
    """Evaluate each change against the policy and return results."""
    results: List[PolicyResult] = []
    for change in changes:
        matched: Optional[PolicyRule] = None
        for rule in config.rules:
            if rule.matches(change):
                matched = rule
                break
        disposition = matched.disposition if matched else config.default_disposition
        results.append(PolicyResult(change=change, disposition=disposition, matched_rule=matched))
    return results


def has_blocked_changes(results: List[PolicyResult]) -> bool:
    return any(r.disposition == "block" for r in results)
