"""CLI sub-commands for snapshot archiving."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from schema_drift.archiver import SnapshotArchiver
from schema_drift.models import DatabaseSnapshot


def _load_snapshot(path: str) -> DatabaseSnapshot:
    data = json.loads(Path(path).read_text())
    return DatabaseSnapshot.from_dict(data)


def cmd_archive_save(args) -> int:
    """Save a snapshot to the archive."""
    archiver = SnapshotArchiver(archive_dir=args.archive_dir)
    snapshot = _load_snapshot(args.snapshot)
    entry = archiver.save(snapshot, label=args.label or "")
    print(f"Archived snapshot '{entry.label}' with id {entry.snapshot_id}")
    return 0


def cmd_archive_list(args) -> int:
    """List all archived snapshots."""
    archiver = SnapshotArchiver(archive_dir=args.archive_dir)
    entries = archiver.list_entries()
    if not entries:
        print("No archived snapshots found.")
        return 0
    for e in entries:
        print(f"[{e.snapshot_id}] {e.label}  ({e.created_at})")
    return 0


def cmd_archive_load(args) -> int:
    """Load and print a snapshot from the archive by id."""
    archiver = SnapshotArchiver(archive_dir=args.archive_dir)
    snapshot = archiver.load(args.snapshot_id)
    if snapshot is None:
        print(f"No snapshot found with id '{args.snapshot_id}'", file=sys.stderr)
        return 1
    print(json.dumps(snapshot.to_dict(), indent=2))
    return 0


def register_archive_subcommands(subparsers) -> None:
    archive_parser = subparsers.add_parser("archive", help="Manage snapshot archive")
    archive_sub = archive_parser.add_subparsers(dest="archive_cmd")

    save_p = archive_sub.add_parser("save", help="Save a snapshot to the archive")
    save_p.add_argument("snapshot", help="Path to snapshot JSON file")
    save_p.add_argument("--archive-dir", default=".schema_archive", help="Archive directory")
    save_p.add_argument("--label", default="", help="Human-readable label")
    save_p.set_defaults(func=cmd_archive_save)

    list_p = archive_sub.add_parser("list", help="List archived snapshots")
    list_p.add_argument("--archive-dir", default=".schema_archive", help="Archive directory")
    list_p.set_defaults(func=cmd_archive_list)

    load_p = archive_sub.add_parser("load", help="Load a snapshot by id")
    load_p.add_argument("snapshot_id", help="Snapshot id to load")
    load_p.add_argument("--archive-dir", default=".schema_archive", help="Archive directory")
    load_p.set_defaults(func=cmd_archive_load)

    def _dispatch(args) -> int:
        if not hasattr(args, "func"):
            archive_parser.print_help()
            return 1
        return args.func(args)

    archive_parser.set_defaults(func=_dispatch)
