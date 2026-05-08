"""schema-drift: Detects and reports schema changes across database snapshots."""

from .detector import DriftDetector
from .models import (
    ChangeType,
    ColumnDrift,
    ColumnSchema,
    DriftReport,
    SchemaSnapshot,
    TableDrift,
    TableSchema,
)

__all__ = [
    "DriftDetector",
    "ChangeType",
    "ColumnDrift",
    "ColumnSchema",
    "DriftReport",
    "SchemaSnapshot",
    "TableDrift",
    "TableSchema",
]

__version__ = "0.1.0"
