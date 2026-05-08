"""Schema drift detection logic — compares two SchemaSnapshot objects."""

from datetime import datetime

from .models import (
    ChangeType,
    ColumnDrift,
    DriftReport,
    SchemaSnapshot,
    TableDrift,
)


class DriftDetector:
    """Compares a baseline snapshot against a current snapshot and produces a DriftReport."""

    def detect(self, baseline: SchemaSnapshot, current: SchemaSnapshot) -> DriftReport:
        report = DriftReport(
            generated_at=datetime.utcnow(),
            baseline_snapshot=baseline.source,
            current_snapshot=current.source,
        )

        all_tables = set(baseline.tables) | set(current.tables)

        for table_name in sorted(all_tables):
            in_baseline = table_name in baseline.tables
            in_current = table_name in current.tables

            if in_baseline and not in_current:
                report.table_drifts.append(
                    TableDrift(table=table_name, change_type=ChangeType.REMOVED)
                )
            elif not in_baseline and in_current:
                report.table_drifts.append(
                    TableDrift(table=table_name, change_type=ChangeType.ADDED)
                )
            else:
                column_drifts = self._compare_columns(
                    table_name,
                    baseline.tables[table_name].columns,
                    current.tables[table_name].columns,
                )
                if column_drifts:
                    report.table_drifts.append(
                        TableDrift(
                            table=table_name,
                            change_type=ChangeType.MODIFIED,
                            column_drifts=column_drifts,
                        )
                    )

        return report

    def _compare_columns(self, table: str, baseline_cols: dict, current_cols: dict) -> list:
        drifts = []
        all_columns = set(baseline_cols) | set(current_cols)

        for col_name in sorted(all_columns):
            in_baseline = col_name in baseline_cols
            in_current = col_name in current_cols

            if in_baseline and not in_current:
                drifts.append(
                    ColumnDrift(
                        table=table,
                        column=col_name,
                        change_type=ChangeType.REMOVED,
                        before=baseline_cols[col_name].to_dict(),
                    )
                )
            elif not in_baseline and in_current:
                drifts.append(
                    ColumnDrift(
                        table=table,
                        column=col_name,
                        change_type=ChangeType.ADDED,
                        after=current_cols[col_name].to_dict(),
                    )
                )
            else:
                b = baseline_cols[col_name].to_dict()
                c = current_cols[col_name].to_dict()
                if b != c:
                    drifts.append(
                        ColumnDrift(
                            table=table,
                            column=col_name,
                            change_type=ChangeType.MODIFIED,
                            before=b,
                            after=c,
                        )
                    )
        return drifts
