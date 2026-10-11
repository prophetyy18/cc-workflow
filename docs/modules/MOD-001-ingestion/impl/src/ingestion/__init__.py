"""MOD-001 Ingestion public API (Python).

Per DESIGN.md Provided Public Contracts § Event Stream Provider:
- fetch_event_stream(pool_address, start_block, end_block, ...) -> FetchResult
- Exception types: EventStreamFetchError, ValidationError, EventDecodeError
- Data types: FetchStats, FetchResult, StreamEntry, DecodedEvent, PoolState, ...
"""
from .api import fetch_event_stream
from .exceptions import (
    CacheCorruptionRecord,
    EventDecodeError,
    EventStreamFetchError,
    ValidationError,
)
from .types import (
    DecodedEvent,
    FetchResult,
    FetchStats,
    InitializeEvent,
    ModifyLiquidityEvent,
    PoolState,
    StreamEntry,
    SwapEventDecoded,
)

__all__ = [
    "fetch_event_stream",
    "EventStreamFetchError",
    "ValidationError",
    "EventDecodeError",
    "CacheCorruptionRecord",
    "FetchResult",
    "FetchStats",
    "PoolState",
    "DecodedEvent",
    "InitializeEvent",
    "SwapEventDecoded",
    "ModifyLiquidityEvent",
    "StreamEntry",
]
