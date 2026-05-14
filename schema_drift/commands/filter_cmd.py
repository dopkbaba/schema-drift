"""CLI sub-command: filter — narrow a drift report before displaying it."""

from __future__ import annotations

import argparse
import json
import sys

from schema_drift.filter import FilterConfig, filter_report
from schema_drift.models import DriftReport, ChangeType
from schema_drift.reporter import DriftReporter


def _load_report_from_file(path: str) -> DriftReport:
    with open(path) as fh:
        data = json.load(fh)
    return DriftReport.from_dict(data)


def cmd_filter(args: argparse.Namespace) -> int:
    """Execute the filter sub-command."""
    try:
        report = _load_report_from_file(args.report)
    except (OSError, KeyError, ValueError) as exc:
        print(f"error: could not load report — {exc}", file=sys.stderr)
        return 2

    change_types = []
    if args.change_types:
        for raw in args.change_types:
            try:
                change_types.append(ChangeType(raw))
            except ValueError:
                print(f"error: unknown change type '{raw}'", file=sys.stderr)
                return 2

    config = FilterConfig(
        include_tables=args.include_tables or [],
        exclude_tables=args.exclude_tables or [],
        change_types=change_types,
        breaking_only=args.breaking_only,
    )

    filtered = filter_report(report, config)
    reporter = DriftReporter(filtered)

    fmt = getattr(args, "format", "text")
    if fmt == "json":
        print(reporter.as_json())
    elif fmt == "markdown":
        print(reporter.as_markdown())
    else:
        print(reporter.as_text())

    return 0


def register_filter_subcommand(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    parser = subparsers.add_parser(
        "filter",
        help="Filter a saved drift report by table or change type",
    )
    parser.add_argument("report", help="Path to a JSON drift report file")
    parser.add_argument(
        "--include-tables", nargs="+", metavar="PATTERN",
        help="Glob patterns for tables to include",
    )
    parser.add_argument(
        "--exclude-tables", nargs="+", metavar="PATTERN",
        help="Glob patterns for tables to exclude",
    )
    parser.add_argument(
        "--change-types", nargs="+", metavar="TYPE",
        help="Limit to specific change types (e.g. column_added column_removed)",
    )
    parser.add_argument(
        "--breaking-only", action="store_true",
        help="Show only breaking changes",
    )
    parser.add_argument(
        "--format", choices=["text", "json", "markdown"], default="text",
    )
    parser.set_defaults(func=cmd_filter)
