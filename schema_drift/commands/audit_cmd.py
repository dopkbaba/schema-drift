"""CLI subcommand for viewing and managing the drift audit log."""

from __future__ import annotations

import json
from argparse import ArgumentParser, Namespace
from pathlib import Path

from schema_drift.auditor import DriftAuditor


def cmd_audit_list(args: Namespace) -> int:
    auditor = DriftAuditor(audit_dir=args.audit_dir)
    entries = auditor.recent(n=args.last)
    if not entries:
        print("No audit entries found.")
        return 0

    if args.format == "json":
        print(json.dumps([e.to_dict() for e in entries], indent=2))
    else:
        print(f"{'Timestamp':<32} {'Label':<20} {'Changes':>8} {'Breaking':>9} {'Score':>7} {'Risk':<10} {'By':<12}")
        print("-" * 100)
        for e in entries:
            print(
                f"{e.timestamp:<32} {e.snapshot_label:<20} "
                f"{e.total_changes:>8} {e.breaking_changes:>9} "
                f"{e.score:>7.1f} {e.risk_level:<10} {e.triggered_by:<12}"
            )
    return 0


def cmd_audit_clear(args: Namespace) -> int:
    auditor = DriftAuditor(audit_dir=args.audit_dir)
    count = len(auditor.entries)
    auditor.clear()
    print(f"Cleared {count} audit entries from {args.audit_dir}.")
    return 0


def register_audit_subcommand(sub) -> None:
    parser: ArgumentParser = sub.add_parser("audit", help="View the drift audit log")
    parser.add_argument(
        "--audit-dir",
        default=".schema_drift/audit",
        help="Directory where audit logs are stored (default: .schema_drift/audit)",
    )

    audit_sub = parser.add_subparsers(dest="audit_action")

    list_parser = audit_sub.add_parser("list", help="List recent audit entries")
    list_parser.add_argument("--last", type=int, default=20, help="Number of recent entries to show")
    list_parser.add_argument("--format", choices=["text", "json"], default="text")

    audit_sub.add_parser("clear", help="Clear all audit entries")

    def _dispatch(args: Namespace) -> int:
        if args.audit_action == "list":
            return cmd_audit_list(args)
        if args.audit_action == "clear":
            return cmd_audit_clear(args)
        parser.print_help()
        return 1

    parser.set_defaults(func=_dispatch)
