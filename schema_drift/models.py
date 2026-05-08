"""Core data models for representing database schema snapshots and drift results."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class ChangeType(str, Enum):
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"


@dataclass
class ColumnSchema:
    name: str
    data_type: str
    nullable: bool = True
    default: Optional[str] = None
    primary_key: bool = False

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "data_type": self.data_type,
            "nullable": self.nullable,
            "default": self.default,
            "primary_key": self.primary_key,
        }


@dataclass
class TableSchema:
    name: str
    columns: Dict[str, ColumnSchema] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "columns": {k: v.to_dict() for k, v in self.columns.items()},
        }


@dataclass
class SchemaSnapshot:
    captured_at: datetime
    tables: Dict[str, TableSchema] = field(default_factory=dict)
    source: str = "unknown"

    def to_dict(self) -> dict:
        return {
            "captured_at": self.captured_at.isoformat(),
            "source": self.source,
            "tables": {k: v.to_dict() for k, v in self.tables.items()},
        }


@dataclass
class ColumnDrift:
    table: str
    column: str
    change_type: ChangeType
    before: Optional[dict] = None
    after: Optional[dict] = None


@dataclass
class TableDrift:
    table: str
    change_type: ChangeType
    column_drifts: List[ColumnDrift] = field(default_factory=list)


@dataclass
class DriftReport:
    generated_at: datetime
    baseline_snapshot: str
    current_snapshot: str
    table_drifts: List[TableDrift] = field(default_factory=list)

    @property
    def has_breaking_changes(self) -> bool:
        for td in self.table_drifts:
            if td.change_type == ChangeType.REMOVED:
                return True
            for cd in td.column_drifts:
                if cd.change_type in (ChangeType.REMOVED, ChangeType.MODIFIED):
                    return True
        return False

    @property
    def total_changes(self) -> int:
        return sum(1 + len(td.column_drifts) for td in self.table_drifts)
