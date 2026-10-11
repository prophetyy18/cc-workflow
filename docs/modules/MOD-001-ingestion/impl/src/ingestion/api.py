"""Public API: fetch_event_stream.

Per DESIGN.md Provided Public Contracts § Event Stream Provider.

Fixes applied (post-Reviewer Mode A, 2026-10-11):
- F1: V4 event ABIs match canonical IPoolManager.sol (PoolId/Currency/IHooks/sender/indexed).
- F2: REQ-020(b) "no Initialize in window" pre-check via narrow topic0=Initialize
  eth_getLogs filter BEFORE full pagination; raise ValidationError on miss
  before any pagination or timestamp RPCs.
- F3: malformed-cached-file path records CacheCorruptionRecord with
  cause="malformed_cached_file" and forces re-fetch (previously silently lost data).
- F8: partial_entries on EventStreamFetchError carry real reconstructed
  post_state (run reconstruct_states before any error raise), so downstream
  consumers (MOD-003) can use them.

Flow per fetch_event_stream call:
1. Validate input (address / window ordering).
2. Cache check + narrow Initialize pre-check: if no Initialize in cache OR
   narrow RPC, raise ValidationError("no_initialize_in_window") (F2).
3. Paginated eth_getLogs across window (cache hit on per-subrange; corruption
   re-fetch with cache_corruption_events record; F3 malformed-JSON path).
4. Decode events via V4 ABIs (F1).
5. Reconstruct pool states per REQ-002 (F8 partial path).
6. Per-block timestamp + block_hash with reorg detection (F2).
7. avg_block_time_seconds computation (F6 L2 robustness).
8. Return FetchResult.
"""
from __future__ import annotations

import dataclasses
import json
import logging
from typing import List, Optional

from .cache import EventCache
from .client import ABI_LIST, RpcClient, _topic_to_hex
from .exceptions import (
    CacheCorruptionRecord,
    EventDecodeError,
    EventStreamFetchError,
    ValidationError,
)
from .reconstruct import reconstruct_states
from .timestamps import BlockTimestampCache
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


def _looks_like_hex_address(addr: str) -> bool:
    if not isinstance(addr, str):
        return False
    if not addr.startswith("0x"):
        return False
    if len(addr) != 42:
        return False
    try:
        int(addr, 16)
        return True
    except ValueError:
        return False


def _decode_log_to_event(log: dict) -> DecodedEvent:
    """Decode a raw eth_getLogs entry using canonical V4 ABI (F1).

    Topics layout:
    - Initialize: [topic0, id, currency0, currency1]
    - Swap: [topic0, id, sender]
    - ModifyLiquidity: [topic0, id, sender]
    """
    import eth_abi  # noqa: lazy import
    from eth_utils import to_checksum_address

    topics = log.get("topics") or []
    data = log.get("data") or "0x"
    block_number = int(log.get("blockNumber", "0x0"), 16)
    log_index = int(log.get("logIndex", "0x0"), 16)
    tx_hash = log.get("transactionHash", "0x")
    pool_address = log.get("address", "0x")

    if not topics:
        raise EventDecodeError(block_number, log_index, str(log).encode("utf-8"))

    data_bytes = bytes.fromhex(data[2:] if data.startswith("0x") else data)
    topic0 = topics[0]

    base_kwargs = dict(
        block_number=block_number,
        log_index=log_index,
        tx_hash=tx_hash if isinstance(tx_hash, str) else "0x",
        event_type=None,
    )

    for abi in ABI_LIST:
        if topic0 != _topic_to_hex(abi):
            continue
        base_kwargs["event_type"] = abi["name"]

        non_indexed_types = [inp["type"] for inp in abi["inputs"] if not inp.get("indexed", False)]
        non_indexed_names = [inp["name"] for inp in abi["inputs"] if not inp.get("indexed", False)]
        indexed_types = [inp["type"] for inp in abi["inputs"] if inp.get("indexed", False)]

        decoded = eth_abi.decode(non_indexed_types, data_bytes)
        idx_vals = []
        for i, t in enumerate(indexed_types):
            topic_bytes = bytes.fromhex(topics[1 + i][2:])
            val = eth_abi.decode([t], topic_bytes)
            idx_vals.append(val[0] if isinstance(val, (list, tuple)) else val)

        # id is always topics[1] for V4 canonical ABIs.
        pool_id_hex = topics[1]

        if abi["name"] == "Initialize":
            # ABI: id, currency0, currency1, fee, tickSpacing, hooks, sqrtPriceX96, tick
            # indexed: id (bytes32), currency0 (address), currency1 (address)
            # data:    fee, tickSpacing, hooks, sqrtPriceX96, tick
            kwargs = dict(zip(non_indexed_names, decoded))
            return InitializeEvent(
                pool_id=pool_id_hex,
                currency0=to_checksum_address(idx_vals[1]) if isinstance(idx_vals[1], (bytes, bytearray)) else idx_vals[1],
                currency1=to_checksum_address(idx_vals[2]) if isinstance(idx_vals[2], (bytes, bytearray)) else idx_vals[2],
                fee=int(kwargs["fee"]),
                tick_spacing=int(kwargs["tickSpacing"]),
                hooks=to_checksum_address(kwargs["hooks"]) if isinstance(kwargs["hooks"], (bytes, bytearray)) else kwargs["hooks"],
                sqrt_price_x96=int(kwargs["sqrtPriceX96"]),
                tick=int(kwargs["tick"]),
                pool_address=pool_address,
                **base_kwargs,
            )
        elif abi["name"] == "Swap":
            # ABI: id, sender, amount0, amount1, sqrtPriceX96, liquidity, tick, fee
            # indexed: id, sender
            # data:    amount0, amount1, sqrtPriceX96, liquidity, tick, fee
            kwargs = dict(zip(non_indexed_names, decoded))
            return SwapEventDecoded(
                pool_id=pool_id_hex,
                sender=to_checksum_address(idx_vals[1]) if isinstance(idx_vals[1], (bytes, bytearray)) else idx_vals[1],
                amount0=int(kwargs["amount0"]),
                amount1=int(kwargs["amount1"]),
                sqrt_price_x96=int(kwargs["sqrtPriceX96"]),
                liquidity=int(kwargs["liquidity"]),
                tick=int(kwargs["tick"]),
                fee_pips=int(kwargs["fee"]),
                **base_kwargs,
            )
        elif abi["name"] == "ModifyLiquidity":
            # ABI: id, sender, tickLower, tickUpper, liquidityDelta, salt
            # indexed: id, sender
            # data:    tickLower, tickUpper, liquidityDelta, salt
            kwargs = dict(zip(non_indexed_names, decoded))
            return ModifyLiquidityEvent(
                pool_id=pool_id_hex,
                sender=to_checksum_address(idx_vals[1]) if isinstance(idx_vals[1], (bytes, bytearray)) else idx_vals[1],
                tick_lower=int(kwargs["tickLower"]),
                tick_upper=int(kwargs["tickUpper"]),
                liquidity_delta=int(kwargs["liquidityDelta"]),
                salt=kwargs["salt"].hex() if isinstance(kwargs["salt"], (bytes, bytearray)) else str(kwargs["salt"]),
                **base_kwargs,
            )

    raise EventDecodeError(block_number, log_index, str(log).encode("utf-8"))


def fetch_event_stream(
    pool_address: str,
    start_block: int,
    end_block: int,
    rpc_client: Optional[RpcClient] = None,
    event_cache: Optional[EventCache] = None,
    timestamp_cache: Optional[BlockTimestampCache] = None,
    cache_root: str = "./cache",
) -> FetchResult:
    """Public entry per DESIGN.md Provided Public Contracts § Event Stream Provider."""
    # ---- STEP 0: Input validation.
    if not _looks_like_hex_address(pool_address):
        raise ValidationError(reason="invalid_pool_address", message=pool_address)
    if start_block > end_block:
        raise ValidationError(
            reason="start_block_after_end_block",
            message=f"start={start_block} > end={end_block}",
        )
    if start_block < 0 or end_block < 0:
        raise ValidationError(reason="negative_block", message=f"start={start_block} end={end_block}")

    if rpc_client is None:
        import os as _os
        rpc_url = _os.environ.get("MOD_001_RPC_URL")
        if rpc_url is None:
            raise ValidationError(
                reason="no_rpc_configured",
                message="Pass rpc_client or set MOD_001_RPC_URL env var.",
            )
        rpc_client = RpcClient(rpc_url=rpc_url)
    if event_cache is None:
        event_cache = EventCache(root=f"{cache_root}/events")
    if timestamp_cache is None:
        timestamp_cache = BlockTimestampCache(root=f"{cache_root}/block_timestamps")

    # ---- STEP 1 (F2): REQ-020(b) pre-check — Initialize must exist before any
    # pagination / timestamp RPCs. We use a narrow eth_getLogs with topic0=Initialize
    # so we know whether to raise ValidationError BEFORE any subsequent fetch.
    cache_corruption_events: List[CacheCorruptionRecord] = []
    cache_hit_count = 0
    corruption_recorded_for: set = set()  # block_range tuples — dedupe across pre-check + main loop.

    # Cache-first pre-check: any cached sub-range with an Initialize event?
    has_init_in_cache = False
    from .client import MAX_BLOCKS_PER_CALL
    cursor = start_block
    while cursor <= end_block:
        window_end = min(cursor + MAX_BLOCKS_PER_CALL - 1, end_block)
        cached_bytes, corruption = event_cache.read_with_corruption_check(
            pool_address, cursor, window_end
        )
        if corruption is not None and (cursor, window_end) not in corruption_recorded_for:
            cache_corruption_events.append(corruption)
            corruption_recorded_for.add((cursor, window_end))
        if cached_bytes is not None:
            try:
                decoded = json.loads(cached_bytes.decode("utf-8"))
                if any(_topic0_matches_init(t.get("topics")) for t in decoded):
                    has_init_in_cache = True
                    break
            except (json.JSONDecodeError, UnicodeDecodeError):
                if (cursor, window_end) not in corruption_recorded_for:
                    cache_corruption_events.append(CacheCorruptionRecord(
                        block_range=(cursor, window_end),
                        cause="malformed_cached_file",
                    ))
                    corruption_recorded_for.add((cursor, window_end))
                # malformed → not usable for pre-check
        cursor = window_end + 1

    if not has_init_in_cache:
        # Narrow RPC pre-check: any Initialize in window?
        try:
            init_logs = rpc_client.get_logs_paginated_init(pool_address, start_block, end_block)
        except RuntimeError as e:
            raise EventStreamFetchError(
                cause="rpc_truncation",
                cache_corruption_events=cache_corruption_events,
                partial_entries=[],
                failed_range=(start_block, end_block),
                message=f"Initialize pre-check failed: {e}",
            )
        if not init_logs:
            raise ValidationError(
                reason="no_initialize_in_window",
                message=pool_address,
            )

    # ---- STEP 2: Pagination + decode (F3 malformed-JSON path fixed).
    raw_logs: List[dict] = []
    entries_before_recon: List[StreamEntry] = []
    cursor = start_block
    while cursor <= end_block:
        window_end = min(cursor + MAX_BLOCKS_PER_CALL - 1, end_block)
        cached_bytes, corruption = event_cache.read_with_corruption_check(
            pool_address, cursor, window_end
        )
        if corruption is not None and (cursor, window_end) not in corruption_recorded_for:
            cache_corruption_events.append(corruption)
            corruption_recorded_for.add((cursor, window_end))

        used_cache = False
        if cached_bytes is not None:
            try:
                decoded_logs = json.loads(cached_bytes.decode("utf-8"))
                raw_logs.extend(decoded_logs)
                cache_hit_count += 1
                used_cache = True
            except (json.JSONDecodeError, UnicodeDecodeError):
                # F3: malformed cached file — record corruption, force re-fetch.
                if (cursor, window_end) not in corruption_recorded_for:
                    cache_corruption_events.append(CacheCorruptionRecord(
                        block_range=(cursor, window_end),
                        cause="malformed_cached_file",
                    ))
                    corruption_recorded_for.add((cursor, window_end))
                cached_bytes = None  # force re-fetch path

        if not used_cache and cached_bytes is None:
            try:
                batch = rpc_client.get_logs_paginated(pool_address, cursor, window_end)
            except RuntimeError as e:
                # Truncation — build partial_entries with REAL reconstructed post_state (F8).
                partial_pairs = _safe_reconstruct(entries_before_recon + [
                    StreamEntry(event=_safe_decode(l), post_state=PoolState(
                        block_number=int(l.get("blockNumber", "0x0"), 16),
                        sqrt_price_x96=0, tick=0, liquidity=0, fee=None,
                    ))
                    for l in raw_logs
                ])
                raise EventStreamFetchError(
                    cause="rpc_truncation",
                    cache_corruption_events=cache_corruption_events,
                    partial_entries=[dataclasses.replace(e, post_state=ps)
                                    for e, ps in partial_pairs],
                    failed_range=(cursor, window_end),
                    message=str(e),
                )
            raw_logs.extend(batch)
            event_cache.write(
                pool_address, cursor, window_end,
                json.dumps(batch, sort_keys=True).encode("utf-8"),
            )
        cursor = window_end + 1

    # ---- STEP 3: Decode events.
    for log in raw_logs:
        try:
            ev = _decode_log_to_event(log)
        except EventDecodeError:
            raise
        entries_before_recon.append(
            StreamEntry(
                event=ev,
                post_state=PoolState(block_number=ev.block_number, sqrt_price_x96=0,
                                    tick=0, liquidity=0, fee=None),
            )
        )

    entries_before_recon.sort(key=lambda e: (e.event.block_number, e.event.log_index))

    # ---- STEP 4: REQ-002 reconstruction (F8 partial-path side benefit).
    paired = reconstruct_states(entries_before_recon)
    entries: List[StreamEntry] = [
        dataclasses.replace(e, post_state=ps) for e, ps in paired
    ]

    # ---- STEP 5: Per-block timestamp + block_hash (with F2 reorg detection).
    unique_blocks = sorted({e.event.block_number for e in entries})
    block_timestamps: dict = {}
    for block_number in unique_blocks:
        try:
            block = rpc_client.get_block_by_number(block_number)
        except Exception as e:
            # F8: partial_entries carry reconstructed post_state.
            raise EventStreamFetchError(
                cause="timestamp_unavailable",
                cache_corruption_events=cache_corruption_events,
                partial_entries=entries,
                failed_range=(start_block, end_block),
                message=f"eth_getBlockByNumber({block_number}) failed: {e}",
            )
        current_block_hash = block["hash"]
        cached_timestamp, corruption = timestamp_cache.read_with_reorg_check(
            pool_address, block_number, current_block_hash
        )
        if corruption is not None:
            cache_corruption_events.append(corruption)
        if cached_timestamp is None:
            timestamp = block["timestamp"]
            timestamp_cache.write(
                pool_address, block_number, timestamp, current_block_hash
            )
            block_timestamps[block_number] = timestamp
        else:
            block_timestamps[block_number] = cached_timestamp

    # ---- STEP 6: avg_block_time_seconds (F6 ignore non-positive).
    sorted_blocks = sorted(unique_blocks)
    deltas: List[int] = []
    for i in range(1, len(sorted_blocks)):
        b_prev, b_curr = sorted_blocks[i - 1], sorted_blocks[i]
        d = block_timestamps[b_curr] - block_timestamps[b_prev]
        if d > 0:
            deltas.append(d)
    if not deltas:
        raise EventStreamFetchError(
            cause="timestamp_no_pairs",
            cache_corruption_events=cache_corruption_events,
            partial_entries=entries,
            failed_range=(start_block, end_block),
            message=f"unique_blocks={sorted_blocks} yielded no positive deltas",
        )
    avg_block_time = sum(deltas) / len(deltas)

    last_event_block_timestamp = block_timestamps[entries[-1].event.block_number]

    return FetchResult(
        event_stream=entries,
        stats=FetchStats(
            cache_hit_count=cache_hit_count,
            cache_corruption_events=cache_corruption_events,
            avg_block_time_seconds=avg_block_time,
            last_event_block_timestamp=last_event_block_timestamp,
        ),
    )


def _topic0_matches_init(topics: list) -> bool:
    if not topics:
        return False
    return topics[0] == _topic_to_hex(ABI_LIST[0])


def _safe_decode(log):
    """Best-effort decode for partial_entries reporting on truncation."""
    try:
        return _decode_log_to_event(log)
    except Exception:
        from .types import DecodedEvent as _DE
        return _DE(
            block_number=int(log.get("blockNumber", "0x0"), 16),
            log_index=int(log.get("logIndex", "0x0"), 16),
            tx_hash=log.get("transactionHash", "0x"),
            event_type="Unknown",
        )


def _safe_reconstruct(entries: List[StreamEntry]) -> list:
    """Best-effort reconstruct for partial_entries reporting."""
    try:
        return reconstruct_states(entries)
    except Exception:
        return [(e, e.post_state) for e in entries]
