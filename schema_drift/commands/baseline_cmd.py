"""CLI sub-commands for baseline management (save / info)."""

import argparse
import sys

from schema_drift.baseline import BaselineManager
from schema_drift.cli import load_snapshot


def cmd_baseline_save(args: argparse.Namespace) -> int:
    """Persist the given snapshot file as the new baseline."""
    try:
        snapshot = load_snapshot(args.snapshot)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    mgr = BaselineManager(baseline_dir=args.baseline_dir)
    path = mgr.save(snapshot, label=args.label or "")
    print(f"Baseline saved to {path}")
    if args.label:
        print(f"Label: {args.label}")
    return 0


def cmd_baseline_info(args: argparse.Namespace) -> int:
    """Display metadata about the current baseline."""
    mgr = BaselineManager(baseline_dir=args.baseline_dir)
    try:
        meta = mgr.metadata()
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Baseline location : {mgr._baseline_path}")
    print(f"Saved at          : {meta['saved_at']}")
    label = meta.get("label") or "(none)"
    print(f"Label             : {label}")
    return 0


def register_baseline_subcommands(
    subparsers: argparse._SubParsersAction,
    baseline_dir_default: str = ".schema_drift",
) -> None:
    """Attach 'baseline save' and 'baseline info' to an existing subparsers group."""
    baseline_parser = subparsers.add_parser(
        "baseline", help="Manage the reference baseline snapshot"
    )
    baseline_sub = baseline_parser.add_subparsers(dest="baseline_cmd", required=True)

    # -- save --
    save_p = baseline_sub.add_parser("save", help="Save a snapshot as the new baseline")
    save_p.add_argument("snapshot", help="Path to snapshot JSON file")
    save_p.add_argument("--label", default="", help="Optional human-readable label")
    save_p.add_argument(
        "--baseline-dir", default=baseline_dir_default, dest="baseline_dir"
    )
    save_p.set_defaults(func=cmd_baseline_save)

    # -- info --
    info_p = baseline_sub.add_parser("info", help="Show current baseline metadata")
    info_p.add_argument(
        "--baseline-dir", default=baseline_dir_default, dest="baseline_dir"
    )
    info_p.set_defaults(func=cmd_baseline_info)
