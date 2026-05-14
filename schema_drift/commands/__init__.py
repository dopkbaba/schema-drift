"""schema_drift.commands — CLI sub-command registry."""

from schema_drift.commands.baseline_cmd import register_baseline_subcommands
from schema_drift.commands.compare_cmd import register_compare_subcommand
from schema_drift.commands.filter_cmd import register_filter_subcommand
from schema_drift.commands.notify_cmd import register_notify_subcommand
from schema_drift.commands.score_cmd import register_score_subcommand
from schema_drift.commands.watch_cmd import register_watch_subcommand

__all__ = [
    "register_baseline_subcommands",
    "register_compare_subcommand",
    "register_filter_subcommand",
    "register_notify_subcommand",
    "register_score_subcommand",
    "register_watch_subcommand",
]


def register_all(subparsers) -> None:  # type: ignore[type-arg]
    """Register every sub-command onto *subparsers*."""
    register_compare_subcommand(subparsers)
    register_baseline_subcommands(subparsers)
    register_watch_subcommand(subparsers)
    register_score_subcommand(subparsers)
    register_filter_subcommand(subparsers)
    register_notify_subcommand(subparsers)
