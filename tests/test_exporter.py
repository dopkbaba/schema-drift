"""Tests for schema_drift.exporter."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from schema_drift.exporter import DriftExporter, export_report
from schema_drift.models import ChangeType, DriftReport, SchemaChange


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture()
def empty_report():
    return DriftReport(changes=[])


@pytest.fixture()
def report_with_change():
    change = SchemaChange(
        table="orders",
        column="status",
        change_type=ChangeType.TYPE_CHANGED,
        old_value="varchar",
        new_value="text",
        is_breaking=False,
    )
    return DriftReport(changes=[change])


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestDriftExporter:
    def test_raises_on_unsupported_format(self, empty_report, tmp_dir):
        exporter = DriftExporter()
        with pytest.raises(ValueError, match="Unsupported format"):
            exporter.export(empty_report, str(tmp_dir / "out.xyz"), fmt="xml")

    def test_text_export_creates_file(self, empty_report, tmp_dir):
        dest = tmp_dir / "report.txt"
        result = export_report(empty_report, str(dest), fmt="text")
        assert result == dest
        assert dest.exists()
        assert "No schema drift" in dest.read_text(encoding="utf-8")

    def test_json_export_is_valid_json(self, report_with_change, tmp_dir):
        dest = tmp_dir / "report.json"
        export_report(report_with_change, str(dest), fmt="json")
        data = json.loads(dest.read_text(encoding="utf-8"))
        assert "changes" in data
        assert len(data["changes"]) == 1

    def test_markdown_export_contains_header(self, report_with_change, tmp_dir):
        dest = tmp_dir / "report.md"
        export_report(report_with_change, str(dest), fmt="markdown")
        content = dest.read_text(encoding="utf-8")
        assert "#" in content

    def test_creates_missing_parent_directories(self, empty_report, tmp_dir):
        dest = tmp_dir / "nested" / "deep" / "report.txt"
        export_report(empty_report, str(dest), fmt="text")
        assert dest.exists()

    def test_returns_resolved_path(self, empty_report, tmp_dir):
        dest = tmp_dir / "out.txt"
        result = export_report(empty_report, str(dest))
        assert isinstance(result, Path)
        assert result.suffix == ".txt"
