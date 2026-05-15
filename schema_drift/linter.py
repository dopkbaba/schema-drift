"""Lint schema snapshots for common anti-patterns and risky column definitions."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .models import SchemaSnapshot


@dataclass
class LintWarning:
    table: str
    column: str | None
    code: str
    message: str
    severity: str  # "warning" | "error"

    def to_dict(self) -> dict:
        return {
            "table": self.table,
            "column": self.column,
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
        }


@dataclass
class LintResult:
    warnings: List[LintWarning] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for w in self.warnings if w.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for w in self.warnings if w.severity == "warning")

    @property
    def passed(self) -> bool:
        return self.error_count == 0

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "warnings": [w.to_dict() for w in self.warnings],
        }


def lint_snapshot(snapshot: SchemaSnapshot) -> LintResult:
    """Run all lint checks against a snapshot and return a LintResult."""
    warnings: List[LintWarning] = []

    for table_name, table in snapshot.tables.items():
        if not table.columns:
            warnings.append(LintWarning(
                table=table_name,
                column=None,
                code="E001",
                message="Table has no columns defined.",
                severity="error",
            ))

        for col_name, col in table.columns.items():
            # Warn about generic TEXT/BLOB types without length constraints
            if col.data_type.upper() in ("TEXT", "BLOB", "LONGTEXT"):
                warnings.append(LintWarning(
                    table=table_name,
                    column=col_name,
                    code="W001",
                    message=f"Column uses unbounded type '{col.data_type}'.",
                    severity="warning",
                ))

            # Warn about nullable primary-key-like columns named 'id'
            if col_name.lower() == "id" and col.nullable:
                warnings.append(LintWarning(
                    table=table_name,
                    column=col_name,
                    code="E002",
                    message="Column 'id' should not be nullable.",
                    severity="error",
                ))

            # Warn about columns with no type information
            if not col.data_type or col.data_type.strip() == "":
                warnings.append(LintWarning(
                    table=table_name,
                    column=col_name,
                    code="E003",
                    message="Column has no data type specified.",
                    severity="error",
                ))

    return LintResult(warnings=warnings)
