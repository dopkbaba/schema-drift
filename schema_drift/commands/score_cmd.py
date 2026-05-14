"""CLI subcommand: score — compute a risk score for a drift between two snapshots."""

import argparse
import json
import sys

from schema_drift.commands.compare_cmd import _load_and_compare
from schema_drift.scorer import score_report


def cmd_score(args: argparse.Namespace) -> int:
    """Run the score subcommand and return an exit code."""
    report = _load_and_compare(args.baseline, args.current)
    score = score_report(report)

    if args.format == "json":
        print(json.dumps(score.to_dict(), indent=2))
    else:
        print(f"Risk level : {score.risk_level.upper()}")
        print(f"Total score: {score.total}")
        if score.breakdown:
            print("Breakdown:")
            for change_type, points in sorted(score.breakdown.items()):
                print(f"  {change_type:<22} {points}")
        else:
            print("No schema changes detected.")

    if args.fail_on and score.risk_level in _riskier_than(args.fail_on):
        return 1
    return 0


def _riskier_than(threshold: str) -> list[str]:
    """Return risk levels that are >= the given threshold."""
    levels = ["low", "medium", "high", "critical"]
    idx = levels.index(threshold) if threshold in levels else 0
    return levels[idx:]


def register_score_subcommand(subparsers) -> None:
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "score",
        help="Compute a numeric risk score for schema drift between two snapshots.",
    )
    parser.add_argument("baseline", help="Path to baseline snapshot JSON")
    parser.add_argument("current", help="Path to current snapshot JSON")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--fail-on",
        dest="fail_on",
        choices=["low", "medium", "high", "critical"],
        default=None,
        help="Exit with code 1 if risk level meets or exceeds this threshold",
    )
    parser.set_defaults(func=cmd_score)
