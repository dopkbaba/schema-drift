"""Baseline management: save and load reference snapshots for drift comparison."""

import json
import os
from datetime import datetime, timezone
from typing import Optional

from schema_drift.models import DatabaseSnapshot


DEFAULT_BASELINE_DIR = ".schema_drift"
DEFAULT_BASELINE_FILE = "baseline.json"


class BaselineManager:
    """Manages saving and loading of baseline database snapshots."""

    def __init__(self, baseline_dir: str = DEFAULT_BASELINE_DIR):
        self.baseline_dir = baseline_dir
        self._baseline_path = os.path.join(baseline_dir, DEFAULT_BASELINE_FILE)

    def save(self, snapshot: DatabaseSnapshot, label: Optional[str] = None) -> str:
        """Persist a snapshot as the current baseline. Returns the file path."""
        os.makedirs(self.baseline_dir, exist_ok=True)

        payload = {
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "label": label or "",
            "snapshot": snapshot.to_dict(),
        }

        with open(self._baseline_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)

        return self._baseline_path

    def load(self) -> DatabaseSnapshot:
        """Load the stored baseline snapshot. Raises FileNotFoundError if absent."""
        if not os.path.exists(self._baseline_path):
            raise FileNotFoundError(
                f"No baseline found at '{self._baseline_path}'. "
                "Run 'schema-drift baseline save' first."
            )

        with open(self._baseline_path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)

        return DatabaseSnapshot.from_dict(payload["snapshot"])

    def exists(self) -> bool:
        """Return True if a baseline file is present."""
        return os.path.exists(self._baseline_path)

    def metadata(self) -> dict:
        """Return saved_at and label without loading the full snapshot."""
        if not self.exists():
            raise FileNotFoundError(f"No baseline found at '{self._baseline_path}'.")
        with open(self._baseline_path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        return {"saved_at": payload.get("saved_at"), "label": payload.get("label", "")}
