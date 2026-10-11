"""Exception types for MOD-001 Ingestion.

Per DESIGN.md Provided Public Contracts:
- EventStreamFetchError: REQ-020(a) RPC failure; cache_corruption_events on combined-failure path (F-B/MOD-001 reopen fix).
- ValidationError: REQ-020(b) no Initialize in window.
- EventDecodeError: numerical decode failure.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class CacheCorruptionRecord:
    """Per DESIGN.md Provided Public Contracts: a single recovered-and-re-fetched sub-range."""
    block_range: tuple  # (start_block, end_block)
    cause: str


class EventStreamFetchError(Exception):
    """Raised when RPC fails or the cache corruption recovery itself fails.

    Per DESIGN Failure semantics:
    - cause in {"rpc_truncation", "timestamp_unavailable", "timestamp_no_pairs"} or implementation-specific.
    - cache_corruption_events ALWAYS present (REQ-020(c) surfacing on every exit path).
    - partial_entries ALWAYS present (events successfully fetched before failure).
    - failed_range present on truncation-style causes.
    """

    def __init__(
        self,
        cause: str,
        cache_corruption_events: Optional[List[CacheCorruptionRecord]] = None,
        partial_entries: Optional[list] = None,
        failed_range: Optional[tuple] = None,
        message: str = "",
    ) -> None:
        self.cause = cause
        self.cache_corruption_events: List[CacheCorruptionRecord] = (
            list(cache_corruption_events) if cache_corruption_events is not None else []
        )
        self.partial_entries: list = list(partial_entries) if partial_entries is not None else []
        self.failed_range = failed_range
        full = (
            f"{message}; cause={cause}; "
            f"cache_corruption_events={self.cache_corruption_events}; "
            f"failed_range={failed_range}; "
            f"partial_entries={len(self.partial_entries)} entries"
        )
        super().__init__(full)


class ValidationError(Exception):
    """Raised on REQ-020(b) no Initialize in window.

    Per DESIGN Failure semantics, raised BEFORE any fetch is attempted.
    """

    def __init__(self, reason: str, message: str = "") -> None:
        self.reason = reason
        super().__init__(f"{message}; reason={reason}")


class EventDecodeError(Exception):
    """Numerical decode failure for a single event log."""

    def __init__(self, block_number: int, log_index: int, raw: bytes, message: str = "") -> None:
        self.block_number = block_number
        self.log_index = log_index
        self.raw = raw
        super().__init__(f"{message}; block_number={block_number}; log_index={log_index}")
