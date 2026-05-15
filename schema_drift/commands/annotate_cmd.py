"""CLI sub-command: annotate — attach descriptions and hints to a drift report."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from schema_drift.annotator import annotate_report
from schema_drift.models import DriftReport


def _load_report(path: str) -> DriftReport:
    data = json.loads(Path(path).read_text())
    return DriftReport.from_dict(data)


def cmd_annotate(args: argparse.Namespace) -> int:
    try:
        report = _load_report(args.report)
    except (FileNotFoundError, KeyError, ValueError) as exc:
        print(f"error: could not load report — {exc}", file=sys.stderr)
        return 2

    result = annotate_report(report)

    if args.format == "json":
        print(json.dumps(result.to_dict(), indent=2))
    else:
        if result.total == 0:
            print("No changes to annotate.")
        else:
            for ann in result.annotated:
                c = ann.change
                print(f"[{ann.severity.upper()}] {c.table}.{c.column or '—'} ({c.change_type.value})")
                print(f"  Description : {ann.description}")
                print(f"  Hint        : {ann.hint}")
                print()

    return 0


def register_annotate_subcommand(sub: argparse.Action) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("annotate", help="Annotate a drift report with descriptions and remediation hints")
    p.add_argument("report", help="Path to a JSON drift report")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.set_defaults(func=cmd_annotate)
