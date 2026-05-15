"""Tests for schema_drift.linter."""
import pytest

from schema_drift.linter import lint_snapshot, LintWarning
from schema_drift.models import ColumnSchema, TableSchema, SchemaSnapshot


def make_snapshot(tables: dict) -> SchemaSnapshot:
    return SchemaSnapshot(tables=tables)


def make_table(columns: dict) -> TableSchema:
    return TableSchema(columns=columns)


def make_col(data_type: str = "VARCHAR(255)", nullable: bool = False) -> ColumnSchema:
    return ColumnSchema(data_type=data_type, nullable=nullable)


# ---------------------------------------------------------------------------
# Empty / clean snapshots
# ---------------------------------------------------------------------------

def test_clean_snapshot_passes():
    snap = make_snapshot({
        "users": make_table({"id": make_col("INT"), "name": make_col("VARCHAR(100)")})
    })
    result = lint_snapshot(snap)
    assert result.passed
    assert result.error_count == 0
    assert result.warning_count == 0


def test_empty_snapshot_passes():
    result = lint_snapshot(make_snapshot({}))
    assert result.passed


# ---------------------------------------------------------------------------
# E001 – table with no columns
# ---------------------------------------------------------------------------

def test_table_with_no_columns_is_error():
    snap = make_snapshot({"empty_table": make_table({})})
    result = lint_snapshot(snap)
    assert not result.passed
    codes = [w.code for w in result.warnings]
    assert "E001" in codes


# ---------------------------------------------------------------------------
# W001 – unbounded type
# ---------------------------------------------------------------------------

def test_text_column_raises_warning():
    snap = make_snapshot({
        "posts": make_table({"body": make_col("TEXT")})
    })
    result = lint_snapshot(snap)
    assert result.passed  # warning, not error
    assert result.warning_count == 1
    assert result.warnings[0].code == "W001"
    assert result.warnings[0].column == "body"


def test_blob_column_raises_warning():
    snap = make_snapshot({
        "files": make_table({"data": make_col("BLOB")})
    })
    result = lint_snapshot(snap)
    assert result.warning_count >= 1
    codes = [w.code for w in result.warnings]
    assert "W001" in codes


# ---------------------------------------------------------------------------
# E002 – nullable id column
# ---------------------------------------------------------------------------

def test_nullable_id_is_error():
    snap = make_snapshot({
        "orders": make_table({"id": make_col("INT", nullable=True)})
    })
    result = lint_snapshot(snap)
    assert not result.passed
    codes = [w.code for w in result.warnings]
    assert "E002" in codes


def test_non_nullable_id_is_ok():
    snap = make_snapshot({
        "orders": make_table({"id": make_col("INT", nullable=False)})
    })
    result = lint_snapshot(snap)
    codes = [w.code for w in result.warnings]
    assert "E002" not in codes


# ---------------------------------------------------------------------------
# E003 – missing data type
# ---------------------------------------------------------------------------

def test_missing_data_type_is_error():
    snap = make_snapshot({
        "things": make_table({"value": make_col(data_type="")})
    })
    result = lint_snapshot(snap)
    assert not result.passed
    codes = [w.code for w in result.warnings]
    assert "E003" in codes


# ---------------------------------------------------------------------------
# to_dict
# ---------------------------------------------------------------------------

def test_to_dict_structure():
    snap = make_snapshot({
        "t": make_table({"id": make_col("INT", nullable=True)})
    })
    d = lint_snapshot(snap).to_dict()
    assert "passed" in d
    assert "error_count" in d
    assert "warning_count" in d
    assert isinstance(d["warnings"], list)
    assert d["warnings"][0]["code"] == "E002"
