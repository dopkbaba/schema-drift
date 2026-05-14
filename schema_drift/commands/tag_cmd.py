"""CLI subcommand: tag — print risk tags for a saved drift report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from schema_drift.models import DriftReport
from schema_drift.tagger import tag_report


def _load_report(path: str) -> DriftReport:
    data = json.loads(Path(path).read_text())
    return DriftReport.from_dict(data)


def cmd_tag(args: argparse.Namespace) -> int:
    try:
        report = _load_report(args.report)
    except (FileNotFoundError, KeyError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    result = tag_report(report)

    if args.format == "json":
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(f"Primary tag : {result.primary_tag}")
        print(f"All tags    : {', '.join(sorted(result.tags))}")

    if args.fail_on and result.primary_tag == args.fail_on:
        return 1
    return 0


def register_tag_subcommand(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser("tag", help="Tag a drift report with risk labels")
    p.add_argument("report", help="Path to a JSON drift report")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--fail-on",
        dest="fail_on",
        metavar="TAG",
        default=None,
        help="Exit with code 1 if the primary tag matches TAG",
    )
    p.set_defaults(func=cmd_tag)
