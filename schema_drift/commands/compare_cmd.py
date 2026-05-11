"""CLI subcommand for comparing two schema snapshots directly.

Allows users to compare a 'before' snapshot against an 'after' snapshot
without relying on a saved baseline, useful for ad-hoc diff workflows.
"""

import sys
import argparse
from pathlib import Path

from schema_drift.cli import load_snapshot
from schema_drift.detector import DriftDetector
from schema_drift.reporter import DriftReporter
from schema_drift.exporter import DriftExporter
from schema_drift.differ import summarize_changes


def cmd_compare(args: argparse.Namespace) -> int:
    """Execute a direct comparison between two snapshot files.

    Loads both snapshots, runs drift detection, and reports results
    via the chosen output format. Returns exit code 1 if breaking
    changes are detected and --fail-on-breaking is set.

    Args:
        args: Parsed CLI arguments containing before, after, format,
              output, and fail_on_breaking fields.

    Returns:
        0 on success or no breaking changes, 1 if breaking changes found
        and --fail-on-breaking flag is active.
    """
    before_path = Path(args.before)
    after_path = Path(args.after)

    if not before_path.exists():
        print(f"Error: 'before' snapshot not found: {before_path}", file=sys.stderr)
        return 2

    if not after_path.exists():
        print(f"Error: 'after' snapshot not found: {after_path}", file=sys.stderr)
        return 2

    before_snapshot = load_snapshot(str(before_path))
    after_snapshot = load_snapshot(str(after_path))

    detector = DriftDetector()
    report = detector.detect(before_snapshot, after_snapshot)

    reporter = DriftReporter(report)
    fmt = args.format.lower()

    if fmt == "text":
        output = reporter.as_text()
    elif fmt == "json":
        output = reporter.as_json()
    elif fmt == "markdown":
        output = reporter.as_markdown()
    else:
        print(f"Error: unsupported format '{fmt}'. Choose text, json, or markdown.", file=sys.stderr)
        return 2

    if args.output:
        exporter = DriftExporter(output_dir=str(Path(args.output).parent))
        exporter.export(report, fmt=fmt, filename=Path(args.output).name)
        print(f"Report written to {args.output}")
    else:
        print(output)

    summary = summarize_changes(report.changes)
    if args.fail_on_breaking and summary["breaking"] > 0:
        print(
            f"\n{summary['breaking']} breaking change(s) detected.",
            file=sys.stderr,
        )
        return 1

    return 0


def register_compare_subcommand(subparsers) -> None:
    """Register the 'compare' subcommand onto the given subparsers object.

    Args:
        subparsers: The argparse subparsers action to attach this command to.
    """
    parser = subparsers.add_parser(
        "compare",
        help="Compare two schema snapshots directly.",
        description="Detect schema drift between a before and after snapshot file.",
    )
    parser.add_argument(
        "before",
        help="Path to the 'before' schema snapshot (JSON).",
    )
    parser.add_argument(
        "after",
        help="Path to the 'after' schema snapshot (JSON).",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format for the drift report (default: text).",
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        default=None,
        help="Write report to FILE instead of stdout.",
    )
    parser.add_argument(
        "--fail-on-breaking",
        action="store_true",
        default=False,
        help="Exit with code 1 if any breaking changes are detected.",
    )
    parser.set_defaults(func=cmd_compare)
