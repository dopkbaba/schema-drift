"""Tests for schema_drift.commands.notify_cmd."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from schema_drift.commands.notify_cmd import cmd_notify, register_notify_subcommand
from schema_drift.models import ChangeType, DriftReport, SchemaChange


def _report_dict(breaking: int = 0) -> dict:
    changes = [
        {
            "table": f"tbl_{i}",
            "change_type": ChangeType.TABLE_REMOVED.value,
            "breaking": True,
            "detail": "",
        }
        for i in range(breaking)
    ]
    return {"changes": changes}


@pytest.fixture
def report_file(tmp_path):
    def _write(breaking=0):
        p = tmp_path / "report.json"
        p.write_text(json.dumps(_report_dict(breaking)), encoding="utf-8")
        return str(p)
    return _write


class FakeArgs:
    def __init__(self, report, webhook=None, log_file=None, min_severity="low", no_summary=False):
        self.report = report
        self.webhook = webhook
        self.log_file = log_file
        self.min_severity = min_severity
        self.no_summary = no_summary


def test_no_sinks_exits_zero(report_file):
    args = FakeArgs(report=report_file(breaking=0))
    assert cmd_notify(args) == 0


def test_log_file_sink_exits_zero(tmp_path, report_file):
    log = str(tmp_path / "out.log")
    args = FakeArgs(report=report_file(breaking=1), log_file=log)
    rc = cmd_notify(args)
    assert rc == 0
    assert Path(log).exists()


def test_below_threshold_no_output(tmp_path, report_file):
    log = str(tmp_path / "out.log")
    args = FakeArgs(report=report_file(breaking=0), log_file=log, min_severity="critical")
    rc = cmd_notify(args)
    assert rc == 0
    assert not Path(log).exists()


def test_bad_report_path_exits_two():
    args = FakeArgs(report="/nonexistent/report.json")
    assert cmd_notify(args) == 2


def test_webhook_error_exits_one(report_file):
    args = FakeArgs(report=report_file(breaking=1), webhook="http://bad.invalid/")
    with patch("urllib.request.urlopen", side_effect=OSError("fail")):
        rc = cmd_notify(args)
    assert rc == 1


def test_register_adds_notify_subcommand():
    import argparse
    p = argparse.ArgumentParser()
    sub = p.add_subparsers()
    register_notify_subcommand(sub)
    parsed = p.parse_args(["notify", "some_report.json", "--min-severity", "high"])
    assert parsed.min_severity == "high"
    assert parsed.report == "some_report.json"
