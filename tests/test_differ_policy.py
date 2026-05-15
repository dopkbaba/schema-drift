"""Tests for schema_drift.differ_policy."""

from __future__ import annotations

import pytest

from schema_drift.models import ChangeType, SchemaChange
from schema_drift.differ_policy import (
    PolicyConfig,
    PolicyRule,
    PolicyResult,
    apply_policy,
    has_blocked_changes,
)


def make_change(
    table: str = "users",
    change_type: ChangeType = ChangeType.COLUMN_REMOVED,
    column: str | None = "email",
    breaking: bool = True,
) -> SchemaChange:
    return SchemaChange(
        table=table,
        change_type=change_type,
        column=column,
        detail="",
        breaking=breaking,
    )


def test_no_rules_uses_default_disposition():
    config = PolicyConfig(default_disposition="warn")
    results = apply_policy([make_change()], config)
    assert len(results) == 1
    assert results[0].disposition == "warn"
    assert results[0].matched_rule is None


def test_matching_rule_overrides_default():
    rule = PolicyRule(change_types=[ChangeType.COLUMN_REMOVED], disposition="block")
    config = PolicyConfig(rules=[rule], default_disposition="warn")
    results = apply_policy([make_change(change_type=ChangeType.COLUMN_REMOVED)], config)
    assert results[0].disposition == "block"
    assert results[0].matched_rule is rule


def test_non_matching_rule_falls_through_to_default():
    rule = PolicyRule(change_types=[ChangeType.TABLE_ADDED], disposition="ignore")
    config = PolicyConfig(rules=[rule], default_disposition="warn")
    results = apply_policy([make_change(change_type=ChangeType.COLUMN_REMOVED)], config)
    assert results[0].disposition == "warn"


def test_table_pattern_restricts_match():
    rule = PolicyRule(
        change_types=[ChangeType.COLUMN_REMOVED],
        table_pattern="audit_*",
        disposition="ignore",
    )
    config = PolicyConfig(rules=[rule], default_disposition="warn")
    ignored = make_change(table="audit_log")
    warned = make_change(table="users")
    results = apply_policy([ignored, warned], config)
    assert results[0].disposition == "ignore"
    assert results[1].disposition == "warn"


def test_first_matching_rule_wins():
    rule1 = PolicyRule(change_types=[ChangeType.COLUMN_REMOVED], disposition="block")
    rule2 = PolicyRule(change_types=[ChangeType.COLUMN_REMOVED], disposition="ignore")
    config = PolicyConfig(rules=[rule1, rule2])
    results = apply_policy([make_change()], config)
    assert results[0].disposition == "block"


def test_has_blocked_changes_false_when_none_blocked():
    results = [
        PolicyResult(change=make_change(), disposition="warn"),
        PolicyResult(change=make_change(), disposition="ignore"),
    ]
    assert not has_blocked_changes(results)


def test_has_blocked_changes_true_when_any_blocked():
    results = [
        PolicyResult(change=make_change(), disposition="warn"),
        PolicyResult(change=make_change(), disposition="block"),
    ]
    assert has_blocked_changes(results)


def test_to_dict_shape():
    change = make_change()
    result = PolicyResult(change=change, disposition="block")
    d = result.to_dict()
    assert d["table"] == change.table
    assert d["change_type"] == change.change_type.value
    assert d["disposition"] == "block"
