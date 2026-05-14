"""Register all CLI subcommands."""

from __future__ import annotations


def register_all(sub) -> None:
    from schema_drift.commands.baseline_cmd import register_baseline_subcommands
    from schema_drift.commands.compare_cmd import register_compare_subcommand
    from schema_drift.commands.watch_cmd import register_watch_subcommand
    from schema_drift.commands.score_cmd import register_score_subcommand
    from schema_drift.commands.filter_cmd import register_filter_subcommand
    from schema_drift.commands.notify_cmd import register_notify_subcommand
    from schema_drift.commands.summarize_cmd import register_summarize_subcommand
    from schema_drift.commands.audit_cmd import register_audit_subcommand

    register_baseline_subcommands(sub)
    register_compare_subcommand(sub)
    register_watch_subcommand(sub)
    register_score_subcommand(sub)
    register_filter_subcommand(sub)
    register_notify_subcommand(sub)
    register_summarize_subcommand(sub)
    register_audit_subcommand(sub)
