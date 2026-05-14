"""CLI subcommand: watch — continuously monitor schema drift against a baseline."""

from __future__ import annotations

import argparse
import sys
from typing import Any

from schema_drift.baseline import BaselineManager
from schema_drift.cli import load_snapshot
from schema_drift.reporter import DriftReporter
from schema_drift.watcher import SchemaWatcher, WatchConfig


def _make_drift_handler(reporter: DriftReporter, fail_on_breaking: bool) -> Any:
    """Return a closure that prints the report and optionally exits."""

    def handler(report):
        print(reporter.as_text(report))
        if fail_on_breaking and any(c.breaking for c in report.changes):
            print("[watch] Breaking change detected — exiting.", file=sys.stderr)
            sys.exit(1)

    return handler


def cmd_watch(args: argparse.Namespace) -> None:
    """Entry point for the 'watch' subcommand."""
    reporter = DriftReporter()

    on_drift = _make_drift_handler(reporter, args.fail_on_breaking)
    on_no_drift = (
        (lambda: print("[watch] No schema drift detected."))
        if args.verbose
        else None
    )

    cfg = WatchConfig(
        baseline_dir=args.baseline_dir,
        baseline_name=args.baseline_name,
        interval_seconds=args.interval,
        max_iterations=args.max_iterations if args.max_iterations > 0 else None,
        on_drift=on_drift,
        on_no_drift=on_no_drift,
    )

    watcher = SchemaWatcher(cfg)
    snapshot_path = args.snapshot

    try:
        result = watcher.watch(lambda: load_snapshot(snapshot_path))
    except FileNotFoundError as exc:
        print(f"[watch] Error: {exc}", file=sys.stderr)
        sys.exit(2)

    print(
        f"[watch] Session complete: {result.iterations} iteration(s), "
        f"{result.drift_detected_count} drift event(s)."
    )


def register_watch_subcommand(subparsers: argparse._SubParsersAction) -> None:
    """Register the 'watch' subcommand with the given subparser group."""
    parser = subparsers.add_parser(
        "watch",
        help="Continuously monitor a snapshot for schema drift.",
    )
    parser.add_argument("snapshot", help="Path to the current snapshot JSON file.")
    parser.add_argument(
        "--baseline-dir", default=".", help="Directory containing baselines."
    )
    parser.add_argument(
        "--baseline-name", default="default", help="Name of the baseline to compare against."
    )
    parser.add_argument(
        "--interval", type=int, default=60, help="Seconds between checks (default: 60)."
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=0,
        help="Stop after N iterations (0 = run forever).",
    )
    parser.add_argument(
        "--fail-on-breaking",
        action="store_true",
        help="Exit with code 1 if a breaking change is detected.",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Print a message when no drift is detected."
    )
    parser.set_defaults(func=cmd_watch)
