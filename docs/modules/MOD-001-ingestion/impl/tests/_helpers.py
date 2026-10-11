"""Shared test helpers: mock RPC client + canned V4 event log generation.

Per Implementation SKILL Hard Rule §5 (tests independent of bookkeeping):
- Each test calls into fetch_event_stream from outside; none call private helpers.
- Test ABIs match canonical Uniswap v4-core IPoolManager.sol primary source
  (https://raw.githubusercontent.com/Uniswap/v4-core/main/src/interfaces/IPoolManager.sol)
  so the test corpus is mutually consistent with on-chain V4 reality, not
  with a mirror of the implementation's ABIs.
"""
from __future__ import annotations

import json
import os
import sys
from typing import Callable, Dict, List, Optional

# Ensure impl/src is importable.
_IMPL_SRC = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, "src")
)
if _IMPL_SRC not in sys.path:
    sys.path.insert(0, _IMPL_SRC)

import eth_abi
from eth_utils import keccak

# V4 event ABIs — canonical Uniswap v4-core IPoolManager.sol (F1 fix).
# Custom types: PoolId = bytes32; Currency = address; IHooks = address.
ABI_INITIALIZE = {
    "anonymous": False,
    "inputs": [
        {"indexed": True, "name": "id", "type": "bytes32"},
        {"indexed": True, "name": "currency0", "type": "address"},
        {"indexed": True, "name": "currency1", "type": "address"},
        {"indexed": False, "name": "fee", "type": "uint24"},
        {"indexed": False, "name": "tickSpacing", "type": "int24"},
        {"indexed": False, "name": "hooks", "type": "address"},
        {"indexed": False, "name": "sqrtPriceX96", "type": "uint160"},
        {"indexed": False, "name": "tick", "type": "int24"},
    ],
    "name": "Initialize",
    "type": "event",
}
ABI_SWAP = {
    "anonymous": False,
    "inputs": [
        {"indexed": True, "name": "id", "type": "bytes32"},
        {"indexed": True, "name": "sender", "type": "address"},
        {"indexed": False, "name": "amount0", "type": "int128"},
        {"indexed": False, "name": "amount1", "type": "int128"},
        {"indexed": False, "name": "sqrtPriceX96", "type": "uint160"},
        {"indexed": False, "name": "liquidity", "type": "uint128"},
        {"indexed": False, "name": "tick", "type": "int24"},
        {"indexed": False, "name": "fee", "type": "uint24"},
    ],
    "name": "Swap",
    "type": "event",
}
ABI_MODIFY_LIQUIDITY = {
    "anonymous": False,
    "inputs": [
        {"indexed": True, "name": "id", "type": "bytes32"},
        {"indexed": True, "name": "sender", "type": "address"},
        {"indexed": False, "name": "tickLower", "type": "int24"},
        {"indexed": False, "name": "tickUpper", "type": "int24"},
        {"indexed": False, "name": "liquidityDelta", "type": "int256"},
        {"indexed": False, "name": "salt", "type": "bytes32"},
    ],
    "name": "ModifyLiquidity",
    "type": "event",
}

POOL_ID = b"\xcc" * 32  # canonical PoolId (bytes32 — raw bytes for eth_abi bytes32 encoder)
ADDR_SIZE = 20


def topic0(abi: dict) -> str:
    types = ",".join(i["type"] for i in abi["inputs"] if i.get("indexed", False))
    sig = f"{abi['name']}({types})"
    return "0x" + keccak(text=sig).hex()


def hex_addr(addr: str) -> str:
    """Pad/normalize a 0x... hex address to 42 chars (checksum-less)."""
    if not isinstance(addr, str):
        addr = str(addr)
    if not addr.startswith("0x"):
        addr = "0x" + addr
    return addr.lower().rjust(42, "0") if len(addr) < 42 else addr.lower()[:42]


def encode_log(
    pool_address: str,
    block_number: int,
    log_index: int,
    abi: dict,
    non_indexed_args: list,
    indexed_args: Optional[list] = None,
    tx_hash: Optional[str] = None,
) -> dict:
    """Build a raw eth_getLogs entry for a V4 event."""
    if indexed_args is None:
        indexed_args = []
    non_indexed_types = [i["type"] for i in abi["inputs"] if not i.get("indexed", False)]
    indexed_types = [i["type"] for i in abi["inputs"] if i.get("indexed", False)]

    data_bytes = eth_abi.encode(non_indexed_types, list(non_indexed_args))
    indexed_topics = [
        topic0(abi),
        *[
            "0x" + eth_abi.encode([t], [v])[2:].hex().rjust(64, "0")
            for t, v in zip(indexed_types, indexed_args)
        ],
    ]
    return {
        "address": hex_addr(pool_address),
        "blockHash": "0x" + ("00" * 32),
        "blockNumber": hex(block_number),
        "data": "0x" + data_bytes.hex(),
        "logIndex": hex(log_index),
        "topics": indexed_topics,
        "transactionHash": tx_hash or ("0x" + ("aa" * 32)),
        "transactionIndex": "0x0",
        "removed": False,
    }


def _init_log_for_window(*, pool_address, start, end):
    """Filter all logs in `mock_rpc_log_data` whose (key_start, key_end) window
    is contained within [start, end], to only those whose topic0 is Initialize.
    """
    from ingestion.client import _topic0_matches_init_payload
    result: list = []
    for (key_start, key_end), logs in mock_rpc_log_data.items():
        if key_start >= start and key_end <= end:
            for l in logs:
                if _topic0_matches_init_payload(l):
                    result.append(l)
    return result


def mock_rpc(
    logs_by_window: Dict[tuple, List[dict]],
    block_timestamps: Optional[Dict[int, int]] = None,
    block_hashes: Optional[Dict[int, str]] = None,
    fail_on_get_logs: Optional[Callable[[int, int], Exception]] = None,
    fail_on_get_block: Optional[Callable[[int], Exception]] = None,
    cap_get_logs: Optional[int] = None,
):
    """Build a mock RpcClient whose get_logs_paginated / get_block_by_number / get_logs_paginated_init
    return canned responses.

    logs_by_window: {(start, end): [raw log dicts], ...}
        If a window is missing from the dict, an empty list is returned.
        If cap_get_logs is set and a window returns more than cap_get_logs entries,
        RuntimeError is raised (simulates truncation).

    block_timestamps: {block_number: timestamp_seconds}; default 1s/block.
    block_hashes: {block_number: "0x..."}; default deterministic.
    """
    from ingestion.client import MAX_BLOCKS_PER_CALL, MAX_LOGS_PER_CALL, RpcClient

    block_timestamps = block_timestamps or {}
    block_hashes = block_hashes or {}

    # Stash the logs_by_window so the init-only filter can read it.
    mock_rpc_log_data.clear()
    mock_rpc_log_data.update(logs_by_window)

    def _get_logs(pool_address: str, start: int, end: int) -> List[dict]:
        if fail_on_get_logs is not None:
            exc = fail_on_get_logs(start, end)
            if exc is not None:
                raise exc
        # Collect logs from all (key_start, key_end) windows whose range is
        # contained within [start, end]. Matches real eth_getLogs semantics
        # when test data is split into multiple sub-ranges.
        results: list = []
        for (key_start, key_end), logs in mock_rpc_log_data.items():
            if key_start >= start and key_end <= end:
                results.extend(logs)
        # Pagination simulation: caller may pass windows of varying sizes.
        # If cap_get_logs set, simulate truncation.
        if cap_get_logs is not None and len(results) >= cap_get_logs:
            raise RuntimeError(
                f"eth_getLogs returned {len(results)} logs at [{start}, {end}]; "
                f"exceeds MAX_LOGS_PER_CALL={MAX_LOGS_PER_CALL}"
            )
        return results

    def _get_logs_init(pool_address: str, start: int, end: int) -> List[dict]:
        return _init_log_for_window(pool_address=pool_address, start=start, end=end)

    def _get_block(block_number: int) -> dict:
        if fail_on_get_block is not None:
            raise fail_on_get_block(block_number)
        ts = block_timestamps.get(block_number, block_number)  # default 1s/block
        bh = block_hashes.get(block_number, "0x" + format(block_number, "x").rjust(64, "0"))
        return {"timestamp": ts, "hash": bh}

    return RpcClient(
        rpc_url=None,
        web3_instance=None,
        raw_get_logs=_get_logs,
        raw_get_logs_init=_get_logs_init,
        raw_get_block_by_number=_get_block,
    )


def fresh_caches(tmp_path: str):
    from ingestion.cache import EventCache
    from ingestion.timestamps import BlockTimestampCache

    return (
        EventCache(root=os.path.join(tmp_path, "events")),
        BlockTimestampCache(root=os.path.join(tmp_path, "block_timestamps")),
        tmp_path,
    )


POOL = "0x1234567890abcdef1234567890abcdef12345678"
CURRENCY0 = "0x" + "11" * 20
CURRENCY1 = "0x" + "22" * 20
SENDER = "0x" + "ab" * 20
HOOKS = "0x" + "00" * 20  # zero address (no hooks)
FEE_PIPS = 3000  # 0.30%
TICK_SPACING = 60  # standard 1% pool tick spacing


def make_init_log(block_number: int, log_index: int, **overrides) -> dict:
    """Build a V4 Initialize log per canonical IPoolManager.sol.

    Indexed args: pool_id (bytes32), currency0 (address), currency1 (address).
    Non-indexed (data): fee, tickSpacing, hooks, sqrtPriceX96, tick.
    """
    return encode_log(
        pool_address=POOL,
        block_number=block_number,
        log_index=log_index,
        abi=ABI_INITIALIZE,
        indexed_args=[
            overrides.get("pool_id", POOL_ID),
            hex_addr(overrides.get("currency0", CURRENCY0)),
            hex_addr(overrides.get("currency1", CURRENCY1)),
        ],
        non_indexed_args=[
            overrides.get("fee", FEE_PIPS),
            overrides.get("tick_spacing", TICK_SPACING),
            hex_addr(overrides.get("hooks", HOOKS)),
            overrides.get("sqrt_price_x96", 2 ** 96),  # P=1.0
            overrides.get("tick", 0),
        ],
    )


def make_swap_log(block_number: int, log_index: int, **overrides) -> dict:
    """Build a V4 Swap log per canonical IPoolManager.sol.

    Indexed args: pool_id (bytes32), sender (address).
    Non-indexed (data): amount0 (int128), amount1 (int128), sqrtPriceX96 (uint160),
                       liquidity (uint128), tick (int24), fee (uint24).
    """
    return encode_log(
        pool_address=POOL,
        block_number=block_number,
        log_index=log_index,
        abi=ABI_SWAP,
        indexed_args=[
            overrides.get("pool_id", POOL_ID),
            hex_addr(overrides.get("sender", SENDER)),
        ],
        non_indexed_args=[
            overrides.get("amount0", 0),
            overrides.get("amount1", 0),
            overrides.get("sqrt_price_x96", 2 ** 96),
            overrides.get("liquidity", 10 ** 18),
            overrides.get("tick", 0),
            overrides.get("fee", FEE_PIPS),
        ],
    )


def make_modify_log(block_number: int, log_index: int, **overrides) -> dict:
    """Build a V4 ModifyLiquidity log per canonical IPoolManager.sol.

    Indexed args: pool_id (bytes32), sender (address).
    Non-indexed (data): tickLower, tickUpper, liquidityDelta (int256), salt (bytes32).
    """
    return encode_log(
        pool_address=POOL,
        block_number=block_number,
        log_index=log_index,
        abi=ABI_MODIFY_LIQUIDITY,
        indexed_args=[
            overrides.get("pool_id", POOL_ID),
            hex_addr(overrides.get("sender", SENDER)),
        ],
        non_indexed_args=[
            overrides.get("tick_lower", -TICK_SPACING * 10),
            overrides.get("tick_upper", TICK_SPACING * 10),
            overrides.get("liquidity_delta", 10 ** 18),
            overrides.get("salt", b"\x00" * 32),
        ],
    )


# Module-level stash so get_logs_paginated_init can read the same logs_by_window
# that the caller passed to mock_rpc(...).
mock_rpc_log_data: Dict[tuple, List[dict]] = {}
