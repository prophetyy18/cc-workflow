"""RPC client wrapper with pagination policy.

Per DESIGN.md Internal Design:
- web3.py: Web3(Web3.HTTPProvider(rpc_url))
- Pagination: respect 10_000 logs per eth_getLogs and 10_000_000 blocks per query range
- ABI: V4 PoolManager events (Initialize, Swap, ModifyLiquidity)
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

# V4 PoolManager event ABIs — canonical Uniswap v4-core IPoolManager.sol primary source
# (https://raw.githubusercontent.com/Uniswap/v4-core/main/src/interfaces/IPoolManager.sol)
# Per SPEC-001 § Unknowns and Upstream Feedback acceptance obligation: Implementation MUST verify
# against primary source. Verified 2026-10-11.
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

# Pagination policy (per SPEC-001 Unknowns-and-Upstream-Feedback empirical verification 2026-10-08)
MAX_LOGS_PER_CALL = 10_000
MAX_BLOCKS_PER_CALL = 10_000_000


def _topic_to_hex(event_abi: dict) -> str:
    """Compute keccak topic0 from event ABI; lazy import eth_utils to keep import light."""
    from eth_utils import keccak
    types = ",".join(i["type"] for i in event_abi["inputs"] if i.get("indexed", False))
    sig = f"{event_abi['name']}({types})"
    return "0x" + keccak(text=sig).hex()


class RpcClient:
    """Thin wrapper around web3.py for the 3 V4 events + eth_getBlockByNumber.

    Injectable for tests: pass `raw_get_logs` / `raw_get_block_by_number` callables
    that return raw JSON-shaped responses (mimicking web3.py).
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
        pool_address: str,
        start_block: int,
        end_block: int,
    ) -> List[dict]:
        """Paginated eth_getLogs across [start_block, end_block].

        Returns list of raw log dicts (as JSON-RPC would return).
        Respects 10_000 logs / 10_000_000 blocks per call (split into sub-queries).
        """
        if self._raw_get_logs is not None:
            return list(self._raw_get_logs(pool_address, start_block, end_block))

        self._ensure_web3()
        # Compute topic0 for each event (to filter).
        topics = [[_topic_to_hex(abi)] for abi in ABI_LIST]

        # Pagination: split block range if exceeds MAX_BLOCKS_PER_CALL.
        # For simplicity: split into MAX_BLOCKS_PER_CALL windows.
        results: List[dict] = []
        cursor = start_block
        while cursor <= end_block:
            window_end = min(cursor + MAX_BLOCKS_PER_CALL - 1, end_block)
            for topic in topics:
                flt = {
                    "address": pool_address,
                    "fromBlock": hex(cursor),
                    "toBlock": hex(window_end),
                    "topics": topic,
                }
                batch = self._web3.eth.get_logs(flt)
                if len(batch) >= MAX_LOGS_PER_CALL:
                    # Caller should have used a smaller window — surface as truncation.
                    raise RuntimeError(
                        f"eth_getLogs returned {len(batch)} logs at boundary "
                        f"[{cursor}, {window_end}]; exceeds MAX_LOGS_PER_CALL"
                    )
                results.extend(batch)
            cursor = window_end + 1
        return results

    def get_logs_paginated_init(
        self,
        pool_address: str,
        start_block: int,
        end_block: int,
    ) -> List[dict]:
        """Narrow eth_getLogs filtered to Initialize events only (F2 pre-check).

        Used to verify REQ-020(b) "no Initialize in window" without paying for
        a full pagination.
        """
        if self._raw_get_logs_init is not None:
            # Paginate via the mock — issue per sub-range so the mock can fail
            # per-subrange (matching the real eth_getLogs truncation semantics).
            results: List[dict] = []
            cursor = start_block
            while cursor <= end_block:
                window_end = min(cursor + MAX_BLOCKS_PER_CALL - 1, end_block)
                results.extend(
                    list(self._raw_get_logs_init(pool_address, cursor, window_end))
                )
                cursor = window_end + 1
            return results
        if self._raw_get_logs is not None:
            # No dedicated init-only mock — fall back to full pagination and filter.
            results = []
            cursor = start_block
            while cursor <= end_block:
                window_end = min(cursor + MAX_BLOCKS_PER_CALL - 1, end_block)
                full = list(self._raw_get_logs(pool_address, cursor, window_end))
                results.extend(l for l in full if _topic0_matches_init_payload(l))
                cursor = window_end + 1
            return results

        self._ensure_web3()
        init_topic = [_topic_to_hex(ABI_LIST[0])]  # ABI_LIST[0] = Initialize
        results: List[dict] = []
        cursor = start_block
        while cursor <= end_block:
            window_end = min(cursor + MAX_BLOCKS_PER_CALL - 1, end_block)
            flt = {
                "address": pool_address,
                "fromBlock": hex(cursor),
                "toBlock": hex(window_end),
                "topics": init_topic,
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
        # Normalize to plain dict with hex string fields.
        return {
            "timestamp": int(block.get("timestamp", 0)),
            "hash": block.get("hash").hex() if block.get("hash") is not None else "0x",
        }
