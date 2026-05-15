"""CLI subcommand: lint a schema snapshot for anti-patterns."""
from __future__ import annotations

import json
import sys

from ..baseline import BaselineManager
from ..linter import lint_snapshot


def cmd_lint(args) -> int:
    """Run lint checks on a snapshot file and report results."""
    mgr = BaselineManager(args.baseline_dir)
    snapshot = mgr.load(args.snapshot)
    if snapshot is None:
        print(f"Error: snapshot file not found: {args.snapshot}", file=sys.stderr)
        return 2

    result = lint_snapshot(snapshot)

    if args.format == "json":
        print(json.dumps(result.to_dict(), indent=2))
    else:
        if not result.warnings:
            print("✓ No lint issues found.")
        else:
            for w in result.warnings:
                col_part = f":{w.column}" if w.column else ""
                label = w.severity.upper()
                print(f"[{label}] {w.table}{col_part}  [{w.code}] {w.message}")
            print()
            print(f"  {result.error_count} error(s), {result.warning_count} warning(s)")

    if args.strict and not result.passed:
        return 1
    return 0


def register_lint_subcommand(subparsers) -> None:
    parser = subparsers.add_parser(
        "lint",
        help="Lint a schema snapshot for anti-patterns.",
    )
    parser.add_argument(
        "snapshot",
        help="Path to the snapshot JSON file to lint.",
    )
    parser.add_argument(
        "--baseline-dir",
        default=".schema_drift",
        help="Directory used by BaselineManager to locate snapshots.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Exit with code 1 if any errors are found.",
    )
    parser.set_defaults(func=cmd_lint)
