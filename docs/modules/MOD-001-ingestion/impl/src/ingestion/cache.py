"""Event cache backend (REQ-003 / REQ-N02 / REQ-020(c)).

Per DESIGN Internal Design:
- File-based: ./cache/events/<pool_address>/<start_block>_<end_block>.json
- Index: ./cache/events/_index.json — maps (pool, start, end) to file path + sha256
- REQ-N02 byte-identity: cached payloads byte-identical to raw RPC response
- REQ-020(c): SHA-256 mismatch on read → re-fetch via RPC; append CacheCorruptionRecord
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import List, Optional, Tuple

from .exceptions import CacheCorruptionRecord


CACHE_ROOT = "./cache/events"
INDEX_FILE = "./cache/events/_index.json"


def _window_file_path(pool_address: str, start_block: int, end_block: int) -> str:
    return f"{CACHE_ROOT}/{pool_address}/{start_block}_{end_block}.json"


def _window_index_key(pool_address: str, start_block: int, end_block: int) -> str:
    return f"{pool_address.lower()}:{start_block}-{end_block}"


class EventCache:
    """On-disk event payload cache with REQ-N02 byte-identity + REQ-020(c) corruption detection.

    Usage:
        cache = EventCache(root="./cache/events")
        # On successful fetch:
        cache.write(pool, start, end, raw_rpc_results_json_bytes)
        # On fetch attempt:
        raw_bytes, corruption = cache.read_with_corruption_check(pool, start, end)
    """

    def __init__(self, root: str = CACHE_ROOT) -> None:
        self.root = Path(root)

    def _load_index(self) -> dict:
        idx_path = self.root / "_index.json"
        if not idx_path.exists():
            return {}
        try:
            return json.loads(idx_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_index(self, index: dict) -> None:
        idx_path = self.root / "_index.json"
        idx_path.parent.mkdir(parents=True, exist_ok=True)
        idx_path.write_text(json.dumps(index, sort_keys=True), encoding="utf-8")

    def _compute_sha256(self, raw: bytes) -> str:
        return hashlib.sha256(raw).hexdigest()

    def has(self, pool_address: str, start_block: int, end_block: int) -> bool:
        key = _window_index_key(pool_address, start_block, end_block)
        return key in self._load_index()

    def write(self, pool_address: str, start_block: int, end_block: int, raw: bytes) -> None:
        """Persist raw RPC response bytes (REQ-N02 byte-identity)."""
        path = self.root / pool_address.lower() / f"{start_block}_{end_block}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        key = _window_index_key(pool_address, start_block, end_block)
        index = self._load_index()
        index[key] = {
            "path": str(path),
            "sha256": self._compute_sha256(raw),
        }
        self._save_index(index)

    def read_with_corruption_check(
        self, pool_address: str, start_block: int, end_block: int
    ) -> Tuple[Optional[bytes], Optional[CacheCorruptionRecord]]:
        """Return (raw_bytes, None) on hit-clean; (None, CacheCorruptionRecord) on corruption; (None, None) on miss.

        Per REQ-020(c): SHA-256 mismatch = corruption; caller MUST re-fetch and append the record.
        """
        key = _window_index_key(pool_address, start_block, end_block)
        index = self._load_index()
        entry = index.get(key)
        if entry is None:
            return None, None
        path = Path(entry["path"])
        try:
            data = path.read_bytes()
        except OSError:
            # Treat missing/unreadable file as corruption (silent truncation).
            record = CacheCorruptionRecord(
                block_range=(start_block, end_block),
                cause="missing_or_unreadable_file",
            )
            return None, record
        actual_sha = self._compute_sha256(data)
        if actual_sha != entry["sha256"]:
            record = CacheCorruptionRecord(
                block_range=(start_block, end_block),
                cause="sha256_mismatch",
            )
            return None, record
        return data, None

    def invalidate(self, pool_address: str, start_block: int, end_block: int) -> None:
        """Remove cached entry (e.g., after reorg-driven re-fetch)."""
        key = _window_index_key(pool_address, start_block, end_block)
        index = self._load_index()
        entry = index.pop(key, None)
        if entry is not None:
            try:
                Path(entry["path"]).unlink(missing_ok=True)
            except OSError:
                pass
            self._save_index(index)
