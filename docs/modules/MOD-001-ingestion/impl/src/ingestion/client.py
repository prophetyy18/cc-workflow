"""RPC client wrapper with pagination policy.

Per DESIGN.md Internal Design (reopen rev 5):
- web3.py: Web3(Web3.HTTPProvider(rpc_url))
- Pagination: respect 10_000 logs per eth_getLogs; 30_000-block per-query ceiling
  observed on Robinhood Chain mainnet (we use 10_000-block sub-windows to stay
  safely under it).
- ABI: V4 PoolManager events (Initialize, Swap, ModifyLiquidity).
- `eth_getLogs` filter pattern: `address=POOL_MANAGER + topics[1]=pool_id` (V4
  is a singleton PoolManager; per-pool filtering uses PoolId in topics[1]).
"""
from __future__ import annotations

import os
from typing import Callable, List, Optional

# Lazy import: web3 + eth-abi are required in production; tests mock at fetch level.
try:
    from web3 import Web3
    from web3.providers.rpc import HTTPProvider
    _WEB3_AVAILABLE = True
except ImportError:
    _WEB3_AVAILABLE = False

# V4 PoolManager on Robinhood Chain (reopen rev 5, empirically verified 2026-10-11
# via `eth_getLogs` topic0 cross-reference against canonical V4 ABIs).
# Source: `docs/verification/MOD-001-v4-contracts.md`. Module-internal constant
# — consumers do NOT pass it; per-pool filtering uses PoolId in topics[1].
# EIP-55 checksum format required by web3.py's address validation.
POOL_MANAGER = "0x8366a39CC670B4001A1121B8F6A443A643e40951"

# V4 PoolManager event ABIs — canonical Uniswap v4-core IPoolManager.sol primary source
# (https://raw.githubusercontent.com/Uniswap/v4-core/main/src/interfaces/IPoolManager.sol)
#
# Custom V4 types: PoolId = bytes32; Currency = address; IHooks = address.
ABI_INITIALIZE_EVENT = {
    "anonymous": False,
    "inputs": [
        {"indexed": True, "name": "id", "type": "bytes32"},          # PoolId
        {"indexed": True, "name": "currency0", "type": "address"},   # Currency
        {"indexed": True, "name": "currency1", "type": "address"},   # Currency
        {"indexed": False, "name": "fee", "type": "uint24"},
        {"indexed": False, "name": "tickSpacing", "type": "int24"},
        {"indexed": False, "name": "hooks", "type": "address"},       # IHooks
        {"indexed": False, "name": "sqrtPriceX96", "type": "uint160"},
        {"indexed": False, "name": "tick", "type": "int24"},
    ],
    "name": "Initialize",
    "type": "event",
}
ABI_SWAP_EVENT = {
    "anonymous": False,
    "inputs": [
        {"indexed": True, "name": "id", "type": "bytes32"},          # PoolId
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
ABI_MODIFY_LIQUIDITY_EVENT = {
    "anonymous": False,
    "inputs": [
        {"indexed": True, "name": "id", "type": "bytes32"},          # PoolId
        {"indexed": True, "name": "sender", "type": "address"},
        {"indexed": False, "name": "tickLower", "type": "int24"},
        {"indexed": False, "name": "tickUpper", "type": "int24"},
        {"indexed": False, "name": "liquidityDelta", "type": "int256"},
        {"indexed": False, "name": "salt", "type": "bytes32"},
    ],
    "name": "ModifyLiquidity",
    "type": "event",
}

ABI_LIST = [ABI_INITIALIZE_EVENT, ABI_SWAP_EVENT, ABI_MODIFY_LIQUIDITY_EVENT]


def _topic0_matches_init_payload(log: dict) -> bool:
    """Test whether a raw log's first topic matches Initialize's topic0."""
    topics = log.get("topics") or []
    if not topics:
        return False
    return topics[0] == _topic_to_hex(ABI_LIST[0])

# Pagination policy (per SPEC-001 Unknowns empirical verification 2026-10-08 and
# live evidence on Robinhood Chain 2026-10-11).
MAX_LOGS_PER_CALL = 10_000
MAX_BLOCKS_PER_CALL = 10_000  # 30k per-query ceiling observed; 10k is the conservative sub-window.


def _topic_to_hex(event_abi: dict) -> str:
    """Compute keccak topic0 from event ABI; lazy import eth_utils to keep import light.

    Per Ethereum event signature spec, the signature includes ALL inputs
    (indexed + non-indexed). Filtering by `i.get("indexed", False)` only
    produces the WRONG topic0 (this was the bug uncovered by live RPC tests
    2026-10-11 — mock RPC tests passed because they don't actually filter by
    topic0 on the wire; live eth_getLogs with the buggy topic0 returns empty).
    """
    from eth_utils import keccak
    types = ",".join(i["type"] for i in event_abi["inputs"])
    sig = f"{event_abi['name']}({types})"
    return "0x" + keccak(text=sig).hex()


class RpcClient:
    """Thin wrapper around web3.py for the 3 V4 events + eth_getBlockByNumber.

    Injectable for tests: pass `raw_get_logs` / `raw_get_block_by_number` callables
    that return raw JSON-shaped responses (mimicking web3.py).

    Per reopen rev 5: the per-pool eth_getLogs filter is constructed as
    `address=POOL_MANAGER + topics[0]=<event_signature> + topics[1]=<pool_id>`.
    PoolId in topics[1] is what isolates a single pool's events from the
    PoolManager singleton.
    """

    def __init__(
        self,
        rpc_url: Optional[str] = None,
        web3_instance=None,
        raw_get_logs: Optional[Callable[..., list]] = None,
        raw_get_logs_init: Optional[Callable[..., list]] = None,
        raw_get_block_by_number: Optional[Callable[..., dict]] = None,
    ) -> None:
        self._raw_get_logs = raw_get_logs
        self._raw_get_logs_init = raw_get_logs_init
        self._raw_get_block_by_number = raw_get_block_by_number
        self._web3 = web3_instance
        self._rpc_url = rpc_url

    def _ensure_web3(self):
        if self._web3 is not None:
            return
        if not _WEB3_AVAILABLE:
            raise RuntimeError(
                "web3.py not installed; pass web3_instance or raw_get_logs explicitly."
            )
        if self._rpc_url is None:
            raise RuntimeError("rpc_url required when no injected web3_instance.")
        self._web3 = Web3(HTTPProvider(self._rpc_url))

    def get_logs_paginated(
        self,
        pool_id: str,
        start_block: int,
        end_block: int,
    ) -> List[dict]:
        """Paginated eth_getLogs across [start_block, end_block] for one V4 pool.

        Per reopen rev 5: filter is `address=POOL_MANAGER + topics[0]=<event> +
        topics[1]=pool_id`. PoolId is 0x-prefixed 32-byte hex. Splits the block
        range into MAX_BLOCKS_PER_CALL sub-windows. Issues one eth_getLogs call
        per (event, sub-window). Returns list of raw log dicts.
        """
        if self._raw_get_logs is not None:
            return list(self._raw_get_logs(pool_id, start_block, end_block))

        self._ensure_web3()
        results: List[dict] = []
        cursor = start_block
        while cursor <= end_block:
            window_end = min(cursor + MAX_BLOCKS_PER_CALL - 1, end_block)
            for abi in ABI_LIST:
                flt = {
                    "address": POOL_MANAGER,
                    "fromBlock": hex(cursor),
                    "toBlock": hex(window_end),
                    "topics": [_topic_to_hex(abi), pool_id],
                }
                batch = self._web3.eth.get_logs(flt)
                if len(batch) >= MAX_LOGS_PER_CALL:
                    raise RuntimeError(
                        f"eth_getLogs returned {len(batch)} logs at boundary "
                        f"[{cursor}, {window_end}]; exceeds MAX_LOGS_PER_CALL"
                    )
                results.extend(batch)
            cursor = window_end + 1
        return results

    def get_logs_paginated_init(
        self,
        pool_id: str,
        start_block: int,
        end_block: int,
    ) -> List[dict]:
        """Narrow eth_getLogs filtered to Initialize events only (REQ-020(b) pre-check).

        Filter: `address=POOL_MANAGER + topics[0]=Initialize_topic + topics[1]=pool_id`.
        Returns at most one Initialize event per pool — the RPC's Indexed-topic
        filter on topic[1] (the PoolId) isolates this pool's Initialize event.
        """
        if self._raw_get_logs_init is not None:
            results: List[dict] = []
            cursor = start_block
            while cursor <= end_block:
                window_end = min(cursor + MAX_BLOCKS_PER_CALL - 1, end_block)
                results.extend(
                    list(self._raw_get_logs_init(pool_id, cursor, window_end))
                )
                cursor = window_end + 1
            return results
        if self._raw_get_logs is not None:
            results = []
            cursor = start_block
            while cursor <= end_block:
                window_end = min(cursor + MAX_BLOCKS_PER_CALL - 1, end_block)
                full = list(self._raw_get_logs(pool_id, cursor, window_end))
                results.extend(l for l in full if _topic0_matches_init_payload(l))
                cursor = window_end + 1
            return results

        self._ensure_web3()
        init_topic = [_topic_to_hex(ABI_LIST[0])]
        results: List[dict] = []
        cursor = start_block
        while cursor <= end_block:
            window_end = min(cursor + MAX_BLOCKS_PER_CALL - 1, end_block)
            flt = {
                "address": POOL_MANAGER,
                "fromBlock": hex(cursor),
                "toBlock": hex(window_end),
                "topics": [init_topic, pool_id],
            }
            batch = self._web3.eth.get_logs(flt)
            if len(batch) >= MAX_LOGS_PER_CALL:
                raise RuntimeError(
                    f"eth_getLogs (init-only) returned {len(batch)} logs at "
                    f"[{cursor}, {window_end}]; exceeds MAX_LOGS_PER_CALL"
                )
            results.extend(batch)
            cursor = window_end + 1
        return results

    def get_block_by_number(self, block_number: int) -> dict:
        """Return raw block dict with at least {timestamp, hash}."""
        if self._raw_get_block_by_number is not None:
            return self._raw_get_block_by_number(block_number)
        self._ensure_web3()
        block = self._web3.eth.get_block(block_number, full_transactions=False)
        return {
            "timestamp": int(block.get("timestamp", 0)),
            "hash": block.get("hash").hex() if block.get("hash") is not None else "0x",
        }