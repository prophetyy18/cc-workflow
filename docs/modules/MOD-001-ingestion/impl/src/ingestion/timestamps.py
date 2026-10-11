"""Block-timestamp cache (F1 / F2 / F-D fix per DESIGN.md).

Per DESIGN.md Internal Design (Block-timestamp cache section):
- File-based: ./cache/block_timestamps/<pool_address>/<block_number>.json
- Value: {"timestamp": int, "block_hash": "0x..."}
- REQ-N02 byte-identity: cached payloads byte-identical to raw RPC response
- Reorg detection (F2): every fetch issues eth_getBlockByNumber per unique block,
  compares current vs cached block_hash; mismatch → invalidate + REQ-020(c) recovery
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Optional, Tuple

from .exceptions import CacheCorruptionRecord


CACHE_ROOT = "./cache/block_timestamps"


class BlockTimestampCache:
    """On-disk block-timestamp cache with reorg detection.

    Usage:
        cache = BlockTimestampCache(root="./cache/block_timestamps")
        # On eth_getBlockByNumber success:
        cache.write(pool, block_number, timestamp, block_hash)
        # On fetch (per unique block in window):
        cached = cache.read_with_reorg_check(pool, block_number, current_block_hash)
        if cached is None:
            # reorg or miss — re-fetch
            ...
    """

    def __init__(self, root: str = CACHE_ROOT) -> None:
        self.root = Path(root)

    @staticmethod
    def _path(root: Path, pool_address: str, block_number: int) -> Path:
        return root / pool_address.lower() / f"{block_number}.json"

    def _compute_sha256(self, raw: bytes) -> str:
        return hashlib.sha256(raw).hexdigest()

    def write(
        self,
        pool_address: str,
        block_number: int,
        timestamp: int,
        block_hash: str,
    ) -> None:
        """Persist (timestamp, block_hash)."""
        path = self._path(self.root, pool_address, block_number)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"timestamp": timestamp, "block_hash": block_hash}
        raw = json.dumps(payload, sort_keys=True).encode("utf-8")
        path.write_bytes(raw)

    def read_with_reorg_check(
        self,
        pool_address: str,
        block_number: int,
        current_block_hash: str,
    ) -> Tuple[Optional[int], Optional[CacheCorruptionRecord]]:
        """Return (cached_timestamp, None) on match; (None, CacheCorruptionRecord) on reorg; (None, None) on miss.

        Per F2 explicit mechanism: reorg = current_block_hash differs from cached; treat as corruption.
        """
        path = self._path(self.root, pool_address, block_number)
        if not path.exists():
            return None, None
        try:
            data = path.read_bytes()
        except OSError:
            return None, CacheCorruptionRecord(
                block_range=(block_number, block_number),
                cause="missing_or_unreadable_timestamp_file",
            )
        try:
            payload = json.loads(data.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None, CacheCorruptionRecord(
                block_range=(block_number, block_number),
                cause="malformed_timestamp_file",
            )
        cached_hash = payload.get("block_hash")
        cached_timestamp = payload.get("timestamp")
        if cached_hash != current_block_hash:
            return None, CacheCorruptionRecord(
                block_range=(block_number, block_number),
                cause="reorg_block_hash_mismatch",
            )
        if cached_timestamp is None:
            return None, CacheCorruptionRecord(
                block_range=(block_number, block_number),
                cause="missing_timestamp_in_cache_file",
            )
        return cached_timestamp, None

    def invalidate(self, pool_address: str, block_number: int) -> None:
        """Remove cached entry (after reorg-driven re-fetch)."""
        path = self._path(self.root, pool_address, block_number)
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
