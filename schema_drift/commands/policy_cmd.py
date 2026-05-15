"""CLI sub-command: evaluate a drift report against a policy file."""

from __future__ import annotations

import json
import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path

from schema_drift.differ_policy import (
    PolicyConfig,
    PolicyRule,
    apply_policy,
    has_blocked_changes,
)
from schema_drift.models import ChangeType, SchemaChange


def _load_report(path: str) -> list:
    with open(path) as fh:
        data = json.load(fh)
    changes = []
    for entry in data.get("changes", []):
        changes.append(
            SchemaChange(
                table=entry["table"],
                change_type=ChangeType(entry["change_type"]),
                column=entry.get("column"),
                detail=entry.get("detail", ""),
                breaking=entry.get("breaking", False),
            )
        )
    return changes


def _load_policy(path: str) -> PolicyConfig:
    with open(path) as fh:
        raw = json.load(fh)
    rules = []
    for r in raw.get("rules", []):
        rules.append(
            PolicyRule(
                change_types=[ChangeType(ct) for ct in r["change_types"]],
                table_pattern=r.get("table_pattern"),
                disposition=r.get("disposition", "warn"),
            )
        )
    return PolicyConfig(
        rules=rules,
        default_disposition=raw.get("default_disposition", "warn"),
    )


def cmd_policy(args: Namespace) -> int:
    changes = _load_report(args.report)
    config = _load_policy(args.policy)
    results = apply_policy(changes, config)

    for r in results:
        if args.format == "json":
            print(json.dumps(r.to_dict()))
        else:
            mark = {"ignore": "--", "warn": "!!", "block": "XX"}[r.disposition]
            col = f" ({r.change.column})" if r.change.column else ""
            print(f"[{mark}] {r.change.table}{col}: {r.change.change_type.value}")

    if has_blocked_changes(results):
        print("Policy evaluation: BLOCKED", file=sys.stderr)
        return 1
    print("Policy evaluation: OK")
    return 0


def register_policy_subcommand(sub) -> None:
    p: ArgumentParser = sub.add_parser("policy", help="Evaluate drift report against a policy")
    p.add_argument("report", help="Path to drift report JSON")
    p.add_argument("policy", help="Path to policy JSON file")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.set_defaults(func=cmd_policy)
