# schema-drift

Detects and reports schema changes across database snapshots to catch breaking migrations early.

---

## Installation

```bash
pip install schema-drift
```

---

## Usage

Take a snapshot of your current database schema, run your migrations, then compare:

```python
from schema_drift import snapshot, compare

# Capture schema before migration
before = snapshot("postgresql://user:pass@localhost/mydb")

# Run your migrations here...

# Capture schema after migration
after = snapshot("postgresql://user:pass@localhost/mydb")

# Compare and report drift
report = compare(before, after)
report.print_summary()
```

Or use the CLI:

```bash
# Save a baseline snapshot
schema-drift snapshot --db postgresql://user:pass@localhost/mydb --out baseline.json

# Compare against a new snapshot
schema-drift compare --before baseline.json --db postgresql://user:pass@localhost/mydb
```

Example output:

```
[BREAKING] Column 'email' removed from table 'users'
[WARNING]  Column 'created_at' type changed: TIMESTAMP -> DATE
[INFO]     New table 'audit_logs' added
```

---

## Supported Databases

- PostgreSQL
- MySQL / MariaDB
- SQLite

---

## License

This project is licensed under the [MIT License](LICENSE).