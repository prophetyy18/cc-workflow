"""Per-pool Initialize block index.

Per reopen rev 5 followup (REQ-020(b) usability): for pools whose
Initialize event is older than the easily-scannable RPC windows
(Robinhood Chain's 30k-block per-query ceiling × many windows ≈ minutes
per fetch), the Initialize event must be located once and remembered
across fetches. This module persists a `pool_id → initialize_block`
mapping under `./cache/pool_init/<pool_id>.json` so subsequent pre-checks
are O(1) instead of O(window_size / 30_000) RPC round-trips.

REPL-1 (Revision log): created 2026-10-12 to address user feedback
that `skip_init_precheck=True` is dishonest testing — the default public
entry must work, and for old pools the only way to make it work in O(1)
is to remember the Initialize block once found.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Optional


CACHE_ROOT = "./cache/pool_init"


class PoolInitIndex:
    """Persistent `pool_id → initialize_block` map.

    On-disk layout: one JSON file per pool at
    `./cache/pool_init/<pool_id>.json` containing `{"initialize_block": N}`.
    Per-pool files (vs single global index) avoid concurrent-write races
    when fetches for distinct pools run in parallel.
    """

    def __init__(self, root: str = CACHE_ROOT) -> None:
        self.root = Path(root)

    def _path(self, pool_id: str) -> Path:
        return self.root / pool_id.lower() / "init.json"

    def get(self, pool_id: str) -> Optional[int]:
        """Return cached initialize_block for this pool_id, or None."""
        path = self._path(pool_id)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            block = data.get("initialize_block")
            return int(block) if isinstance(block, int) else None
        except (json.JSONDecodeError, OSError, TypeError, ValueError):
            return None

    def put(self, pool_id: str, initialize_block: int) -> None:
        """Persist initialize_block for this pool_id."""
        path = self._path(pool_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"initialize_block": int(initialize_block)}, sort_keys=True),
            encoding="utf-8",
        )

    def invalidate(self, pool_id: str) -> None:
        """Remove cached entry (e.g., if the user reports the cache is stale)."""
        path = self._path(pool_id)
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass