"""Command-line interface for schema-drift."""

from __future__ import annotations

import argparse
import json
import sys

from schema_drift.detector import DriftDetector
from schema_drift.models import DatabaseSnapshot
from schema_drift.reporter import DriftReporter


def load_snapshot(path: str) -> DatabaseSnapshot:
    """Load a DatabaseSnapshot from a JSON file."""
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return DatabaseSnapshot.from_dict(data)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="schema-drift",
        description="Detect and report schema changes between two database snapshots.",
    )
    parser.add_argument("baseline", help="Path to the baseline snapshot JSON file.")
    parser.add_argument("current", help="Path to the current snapshot JSON file.")
    parser.add_argument(
        "--format",
        choices=["text", "json", "markdown"],
        default="text",
        dest="fmt",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--fail-on-breaking",
        action="store_true",
        help="Exit with code 1 if breaking changes are detected.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    baseline = load_snapshot(args.baseline)
    current = load_snapshot(args.current)

    detector = DriftDetector()
    report = detector.detect(baseline, current)

    reporter = DriftReporter()
    formatters = {
        "text": reporter.as_text,
        "json": reporter.as_json,
        "markdown": reporter.as_markdown,
    }
    print(formatters[args.fmt](report))

    if args.fail_on_breaking and report.has_breaking_changes:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
