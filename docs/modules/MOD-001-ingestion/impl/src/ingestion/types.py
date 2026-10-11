"""Public type definitions for MOD-001 Ingestion.

Per DESIGN.md Provided Public Contracts:
- FetchStats (4 fields, non-Optional after F2 fix).
- FetchResult = (event_stream, stats).
- EventStream = List[StreamEntry { event: DecodedEvent, post_state: PoolState }].
- PoolState { sqrt_price_x96, tick, liquidity, fee } — fee None on ModifyLiquidity per REQ-002.
- DecodedEvent carries original block_number / log_index / tx_hash plus decoded fields.
- CacheCorruptionRecord: block_range, cause.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, NamedTuple, Optional, Union

from .exceptions import CacheCorruptionRecord  # re-export


@dataclass(frozen=True)
class PoolState:
    """Per DESIGN: (sqrt_price_x96, tick, liquidity, fee).

    State-propagation rule (REQ-002):
    - Swap event: fee = event.fee
    - ModifyLiquidity event: sqrt_price_x96/tick = most recent prior Swap; liquidity += event.liquidityDelta; fee = None
    - Initialize event: fee = event.fee (initial state)
    """
    block_number: int
    sqrt_price_x96: int
    tick: int
    liquidity: int
    fee: Optional[int]


@dataclass(frozen=True)
class DecodedEvent:
    """Per DESIGN: original block_number / log_index / tx_hash + decoded event-specific fields.

    Fields common to all three event types. Event-specific fields
    (sqrtPriceX96 / liquidityDelta / etc.) live in event-specific
    decoded_* subclasses below.
    """
    block_number: int
    log_index: int
    tx_hash: str
    event_type: str  # 'Initialize' | 'Swap' | 'ModifyLiquidity'


@dataclass(frozen=True)
class InitializeEvent(DecodedEvent):
    """V4 PoolManager Initialize event (canonical IPoolManager.sol ABI, F1 fix).

    ABI:
        event Initialize(
            PoolId indexed id,
            Currency indexed currency0,
            Currency indexed currency1,
            uint24 fee,
            int24 tickSpacing,
            IHooks hooks,
            uint160 sqrtPriceX96,
            int24 tick
        );
    """
    pool_id: str  # PoolId (bytes32)
    currency0: str
    currency1: str
    fee: int
    tick_spacing: int
    hooks: str
    sqrt_price_x96: int
    tick: int
    pool_address: str


@dataclass(frozen=True)
class SwapEventDecoded(DecodedEvent):
    """V4 PoolManager Swap event (canonical IPoolManager.sol ABI, F1 fix).

    ABI:
        event Swap(
            PoolId indexed id,
            address indexed sender,
            int128 amount0,
            int128 amount1,
            uint160 sqrtPriceX96,
            uint128 liquidity,
            int24 tick,
            uint24 fee
        );
    """
    pool_id: str
    sender: str
    amount0: int
    amount1: int
    sqrt_price_x96: int
    liquidity: int
    tick: int
    fee_pips: int  # uint24 in pips (V4 convention, 1 pip = 1/100 bps)


@dataclass(frozen=True)
class ModifyLiquidityEvent(DecodedEvent):
    """V4 PoolManager ModifyLiquidity event (canonical IPoolManager.sol ABI, F1 fix).

    ABI:
        event ModifyLiquidity(
            PoolId indexed id,
            address indexed sender,
            int24 tickLower,
            int24 tickUpper,
            int256 liquidityDelta,
            bytes32 salt
        );
    """
    pool_id: str
    sender: str
    tick_lower: int
    tick_upper: int
    liquidity_delta: int
    salt: str


DecodedEventUnion = Union[InitializeEvent, SwapEventDecoded, ModifyLiquidityEvent]


@dataclass(frozen=True)
class StreamEntry:
    """Per DESIGN: event + post_state (state AFTER this event).
    """
    event: DecodedEventUnion
    post_state: PoolState


@dataclass(frozen=True)
class FetchStats:
    """Per DESIGN Provided Public Contracts (F2 fix: non-Optional).

    - cache_hit_count: sub-ranges served from on-disk cache.
    - cache_corruption_events: empty if no corruption detected.
    - avg_block_time_seconds: ALWAYS populated; failure raises EventStreamFetchError.
    - last_event_block_timestamp: ALWAYS populated (int seconds); failure raises.
    """
    cache_hit_count: int
    cache_corruption_events: List[CacheCorruptionRecord]
    avg_block_time_seconds: float
    last_event_block_timestamp: int


@dataclass(frozen=True)
class FetchResult:
    """Per DESIGN Provided Public Contracts: (event_stream, stats).
    """
    event_stream: List[StreamEntry]
    stats: FetchStats
