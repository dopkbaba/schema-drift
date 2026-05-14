"""CLI sub-command: notify — send drift report to configured sinks."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from schema_drift.models import DriftReport
from schema_drift.notifier import DriftNotifier, NotifyConfig
from schema_drift.scorer import score_report


def _load_report(path: str) -> DriftReport:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return DriftReport.from_dict(raw)


def cmd_notify(args: argparse.Namespace) -> int:
    try:
        report = _load_report(args.report)
    except (OSError, KeyError, ValueError) as exc:
        print(f"[error] Could not load report: {exc}", file=sys.stderr)
        return 2

    score = score_report(report)

    cfg = NotifyConfig(
        webhook_url=args.webhook,
        log_file=args.log_file,
        min_severity=args.min_severity,
        include_summary=not args.no_summary,
    )

    notifier = DriftNotifier(cfg)
    result = notifier.notify(report, score)

    if result.sent_to:
        for dest in result.sent_to:
            print(f"[ok] Notified: {dest}")
    else:
        print("[info] No notifications sent (threshold not met or no sinks configured).")

    if result.errors:
        for err in result.errors:
            print(f"[warn] {err}", file=sys.stderr)
        return 1

    return 0


def register_notify_subcommand(subparsers) -> None:  # type: ignore[type-arg]
    p: argparse.ArgumentParser = subparsers.add_parser(
        "notify",
        help="Send a drift report to webhook / log-file sinks.",
    )
    p.add_argument("report", help="Path to a JSON drift report file.")
    p.add_argument("--webhook", metavar="URL", default=None, help="Webhook URL to POST to.")
    p.add_argument("--log-file", metavar="PATH", default=None, help="Append notification to a log file.")
    p.add_argument(
        "--min-severity",
        choices=["low", "medium", "high", "critical"],
        default="low",
        help="Only notify when drift severity is at least this level.",
    )
    p.add_argument("--no-summary", action="store_true", help="Omit the table list from the payload.")
    p.set_defaults(func=cmd_notify)
