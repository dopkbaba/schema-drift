"""Tests for the schema-drift CLI."""

from __future__ import annotations

import json
import os
import tempfile

import pytest

from schema_drift.cli import main


def write_snapshot(data: dict, directory: str, name: str) -> str:
    path = os.path.join(directory, name)
    with open(path, "w") as fh:
        json.dump(data, fh)
    return path


BASELINE = {
    "name": "baseline",
    "tables": {
        "users": {
            "name": "users",
            "columns": {
                "id": {"name": "id", "data_type": "integer", "nullable": False, "default": None},
                "email": {"name": "email", "data_type": "varchar", "nullable": False, "default": None},
            },
        }
    },
}

CURRENT_NO_DRIFT = json.loads(json.dumps(BASELINE))  # deep copy
CURRENT_NO_DRIFT["name"] = "current"

CURRENT_BREAKING = {
    "name": "current",
    "tables": {
        "users": {
            "name": "users",
            "columns": {
                "id": {"name": "id", "data_type": "integer", "nullable": False, "default": None},
            },
        }
    },
}


@pytest.fixture()
def tmpdir():
    with tempfile.TemporaryDirectory() as d:
        yield d


def test_cli_no_drift_exits_zero(tmpdir):
    b = write_snapshot(BASELINE, tmpdir, "baseline.json")
    c = write_snapshot(CURRENT_NO_DRIFT, tmpdir, "current.json")
    assert main([b, c]) == 0


def test_cli_breaking_change_exits_zero_without_flag(tmpdir):
    b = write_snapshot(BASELINE, tmpdir, "baseline.json")
    c = write_snapshot(CURRENT_BREAKING, tmpdir, "current.json")
    assert main([b, c]) == 0


def test_cli_breaking_change_exits_one_with_flag(tmpdir):
    b = write_snapshot(BASELINE, tmpdir, "baseline.json")
    c = write_snapshot(CURRENT_BREAKING, tmpdir, "current.json")
    assert main([b, c, "--fail-on-breaking"]) == 1


def test_cli_json_format(tmpdir, capsys):
    b = write_snapshot(BASELINE, tmpdir, "baseline.json")
    c = write_snapshot(CURRENT_BREAKING, tmpdir, "current.json")
    main([b, c, "--format", "json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["has_breaking_changes"] is True


def test_cli_markdown_format(tmpdir, capsys):
    b = write_snapshot(BASELINE, tmpdir, "baseline.json")
    c = write_snapshot(CURRENT_NO_DRIFT, tmpdir, "current.json")
    main([b, c, "--format", "markdown"])
    captured = capsys.readouterr()
    assert "## Schema Drift Report" in captured.out
