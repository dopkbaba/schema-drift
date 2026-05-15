"""Tests for the comparator CLI sub-command."""
from __future__ import annotations

import argparse
import json
import os
import tempfile

import pytest

from schema_drift.commands.comparator_cmd import cmd_comparator


def _write(path: str, data: dict) -> None:
    with open(path, "w") as fh:
        json.dump(data, fh)


_SIMPLE_SNAPSHOT = {
    "tables": {
        "users": {
            "name": "users",
            "columns": [{"name": "id", "data_type": "int", "nullable": False}],
        }
    }
}

_CHANGED_SNAPSHOT = {
    "tables": {
        "users": {
            "name": "users",
            "columns": [{"name": "id", "data_type": "bigint", "nullable": False}],
        }
    }
}


@pytest.fixture()
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


class FakeArgs:
    def __init__(self, baseline, current, fmt="text", fail_on_breaking=False, no_tag=False, no_score=False):
        self.baseline = baseline
        self.current = current
        self.format = fmt
        self.fail_on_breaking = fail_on_breaking
        self.no_tag = no_tag
        self.no_score = no_score


def test_no_drift_exits_zero(tmp_dir, capsys):
    b = os.path.join(tmp_dir, "base.json")
    c = os.path.join(tmp_dir, "curr.json")
    _write(b, _SIMPLE_SNAPSHOT)
    _write(c, _SIMPLE_SNAPSHOT)
    rc = cmd_comparator(FakeArgs(b, c))
    assert rc == 0


def test_breaking_change_exits_one_with_flag(tmp_dir):
    b = os.path.join(tmp_dir, "base.json")
    c = os.path.join(tmp_dir, "curr.json")
    _write(b, _SIMPLE_SNAPSHOT)
    _write(c, {"tables": {}})
    rc = cmd_comparator(FakeArgs(b, c, fail_on_breaking=True))
    assert rc == 1


def test_breaking_change_exits_zero_without_flag(tmp_dir):
    b = os.path.join(tmp_dir, "base.json")
    c = os.path.join(tmp_dir, "curr.json")
    _write(b, _SIMPLE_SNAPSHOT)
    _write(c, {"tables": {}})
    rc = cmd_comparator(FakeArgs(b, c, fail_on_breaking=False))
    assert rc == 0


def test_json_output_is_valid(tmp_dir, capsys):
    b = os.path.join(tmp_dir, "base.json")
    c = os.path.join(tmp_dir, "curr.json")
    _write(b, _SIMPLE_SNAPSHOT)
    _write(c, _CHANGED_SNAPSHOT)
    cmd_comparator(FakeArgs(b, c, fmt="json"))
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "report" in data
    assert "changes" in data["report"]
