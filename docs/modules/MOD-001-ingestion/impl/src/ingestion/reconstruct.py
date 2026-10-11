"""Pool state reconstruction per REQ-002.

Per DESIGN.md Output semantics state-propagation rule:
- Swap event: post_state = (sqrtPriceX96, tick, liquidity, fee) — all from event fields
- ModifyLiquidity event: post_state = (most_recent_swap.sqrtPriceX96/tick, liquidity + liquidityDelta, fee=None)
- Initialize event: post_state = (sqrtPriceX96, tick, liquidity=0, fee) — initial state

Returns list of (entry, post_state) pairs. StreamEntry is frozen so callers MUST
use dataclasses.replace to attach post_state.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from .types import (
    InitializeEvent,
    ModifyLiquidityEvent,
    PoolState,
    StreamEntry,
    SwapEventDecoded,
)


def reconstruct_states(
    entries: List[StreamEntry],
) -> List[Tuple[StreamEntry, PoolState]]:
    """Walk events in order; emit (entry, post_state) per REQ-002.

    Pre-condition: entries are pre-sorted by (block_number, log_index).
    """
    out: List[Tuple[StreamEntry, PoolState]] = []
    last_swap_state: Optional[PoolState] = None
    current_liquidity: Optional[int] = None

    for entry in entries:
        ev = entry.event
        if isinstance(ev, SwapEventDecoded):
            post = PoolState(
                block_number=ev.block_number,
                sqrt_price_x96=ev.sqrt_price_x96,
                tick=ev.tick,
                liquidity=ev.liquidity,
                fee=ev.fee_pips,
            )
            last_swap_state = post
            current_liquidity = ev.liquidity
            out.append((entry, post))
        elif isinstance(ev, ModifyLiquidityEvent):
            if last_swap_state is None:
                raise ValueError(
                    f"ModifyLiquidity at ({ev.block_number}, {ev.log_index}) "
                    f"without prior Swap/Initialize context"
                )
            base = current_liquidity if current_liquidity is not None else last_swap_state.liquidity
            new_liq = base + ev.liquidity_delta
            post = PoolState(
                block_number=ev.block_number,
                sqrt_price_x96=last_swap_state.sqrt_price_x96,
                tick=last_swap_state.tick,
                liquidity=new_liq,
                fee=None,
            )
            current_liquidity = new_liq
            out.append((entry, post))
        elif isinstance(ev, InitializeEvent):
            post = PoolState(
                block_number=ev.block_number,
                sqrt_price_x96=ev.sqrt_price_x96,
                tick=ev.tick,
                liquidity=0,
                fee=ev.fee,
            )
            last_swap_state = post
            current_liquidity = 0
            out.append((entry, post))
        else:
            raise TypeError(f"Unknown event type: {type(ev).__name__}")

    return out
