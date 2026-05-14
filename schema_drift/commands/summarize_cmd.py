"""CLI subcommand: summarize a drift report file."""

import argparse
import json
import sys

from schema_drift.models import DriftReport
from schema_drift.summarizer import summarize_report


def _load_report(path: str) -> DriftReport:
    with open(path) as fh:
        data = json.load(fh)
    return DriftReport.from_dict(data)


def cmd_summarize(args: argparse.Namespace) -> int:
    """Entry point for the summarize subcommand."""
    try:
        report = _load_report(args.report)
    except (FileNotFoundError, KeyError, ValueError) as exc:
        print(f"Error loading report: {exc}", file=sys.stderr)
        return 1

    summary = summarize_report(report, top_n=args.top)

    if args.format == "json":
        print(json.dumps(summary.to_dict(), indent=2))
    else:
        print(f"Risk Level : {summary.risk_level}")
        print(f"Score      : {summary.score:.1f}")
        print(f"Tables     : {summary.total_tables_affected} affected")
        print(f"Changes    : {summary.total_changes} total, {summary.total_breaking} breaking")
        if summary.top_tables:
            print("\nTop affected tables:")
            for t in summary.top_tables:
                types = ", ".join(t.change_types) or "—"
                print(f"  {t.table}: {t.breaking} breaking, {t.non_breaking} non-breaking ({types})")

    return 0


def register_summarize_subcommand(subparsers) -> None:
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "summarize",
        help="Summarize a drift report JSON file",
    )
    parser.add_argument("report", help="Path to a drift report JSON file")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=5,
        metavar="N",
        help="Number of top affected tables to show (default: 5)",
    )
    parser.set_defaults(func=cmd_summarize)
