"""Exports drift reports to various file formats (JSON, Markdown, text)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from schema_drift.models import DriftReport
from schema_drift.reporter import DriftReporter


class DriftExporter:
    """Writes drift reports to disk in a chosen format."""

    SUPPORTED_FORMATS = ("text", "json", "markdown")

    def __init__(self, reporter: Optional[DriftReporter] = None) -> None:
        self._reporter = reporter or DriftReporter()

    def export(self, report: DriftReport, output_path: str, fmt: str = "text") -> Path:
        """Render *report* in *fmt* and write it to *output_path*.

        Returns the resolved :class:`pathlib.Path` that was written.

        Raises
        ------
        ValueError
            If *fmt* is not one of the supported formats.
        """
        if fmt not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported format {fmt!r}. Choose from: {', '.join(self.SUPPORTED_FORMATS)}"
            )

        content = self._render(report, fmt)
        dest = Path(output_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
        return dest

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _render(self, report: DriftReport, fmt: str) -> str:
        if fmt == "json":
            return self._reporter.as_json(report)
        if fmt == "markdown":
            return self._reporter.as_markdown(report)
        return self._reporter.as_text(report)


def export_report(
    report: DriftReport,
    output_path: str,
    fmt: str = "text",
    reporter: Optional[DriftReporter] = None,
) -> Path:
    """Convenience wrapper around :class:`DriftExporter`."""
    return DriftExporter(reporter).export(report, output_path, fmt)
