"""CLI sub-command: compare two snapshot files with tagging and scoring."""
from __future__ import annotations

import argparse
import json
import sys

from schema_drift.baseline import BaselineManager
from schema_drift.cli import load_snapshot
from schema_drift.comparator import SnapshotComparator
from schema_drift.reporter import DriftReporter


def cmd_comparator(args: argparse.Namespace) -> int:
    baseline_snap = load_snapshot(args.baseline)
    current_snap = load_snapshot(args.current)

    comparator = SnapshotComparator(tag=not args.no_tag, score=not args.no_score)
    result = comparator.compare(
        baseline=baseline_snap,
        current=current_snap,
        baseline_name=args.baseline,
        current_name=args.current,
    )

    if args.format == "json":
        print(json.dumps(result.to_dict(), indent=2))
    elif args.format == "markdown":
        reporter = DriftReporter(result.report)
        print(reporter.as_markdown())
    else:
        reporter = DriftReporter(result.report)
        print(reporter.as_text())
        if result.tags:
            print(f"Tags : {', '.join(result.tags)}")
        if result.score:
            s = result.score
            print(f"Score: {s.total_score} (risk={s.risk_level})")

    has_breaking = any(c.breaking for c in result.report.changes)
    if args.fail_on_breaking and has_breaking:
        return 1
    return 0


def register_comparator_subcommand(subparsers) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "comparator",
        help="Compare two snapshots with tagging and scoring.",
    )
    p.add_argument("baseline", help="Path to baseline snapshot JSON")
    p.add_argument("current", help="Path to current snapshot JSON")
    p.add_argument(
        "--format",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--fail-on-breaking",
        action="store_true",
        default=False,
        help="Exit with code 1 if breaking changes are detected.",
    )
    p.add_argument("--no-tag", action="store_true", default=False)
    p.add_argument("--no-score", action="store_true", default=False)
    p.set_defaults(func=cmd_comparator)
