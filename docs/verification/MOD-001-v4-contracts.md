# MOD-001 Live-RPC Verification

**Date**: 2026-10-11
**Status**: ✅ All 19 tests pass, including the live RPC test against Robinhood Chain mainnet.

## Live Test Outcome

`tests/test_known_pool.py::TestKnownPoolLive::test_live_fetch_returns_non_empty_event_stream`
**PASS** in ~72 sec (one fetch, then cached for subsequent runs). Verified that:

- `fetch_event_stream` actually fetches V4 events from the real RPC.
- Event decode succeeds end-to-end (raw logs → typed `DecodedEvent` records).
- Reconstruction runs without errors.
- `FetchStats.avg_block_time_seconds` and `last_event_block_timestamp` populate correctly.

## Bugs Found and Fixed (Live-RPC-Driven)

Running the live test uncovered **6 real defects** that the mock-RPC test suite
had been silently passing over. This is exactly the §11.5 risk-driven reason real
tests matter — mocks can't catch wrong-assumption propagation.

| # | Defect | Where | Fix |
|---|---|---|---|
| 1 | `_topic_to_hex` filtered event inputs by `indexed=True` only, producing a **wrong topic0**. Per the Ethereum event signature spec, the signature must include ALL inputs (indexed + non-indexed). | `src/ingestion/client.py`, `tests/_helpers.py` | Use full input types (no `indexed` filter). |
| 2 | `raw_logs[-len(batch):] = normalized` with empty batch silently clears the whole list — every empty sub-window wiped accumulated events. | `src/ingestion/api.py` STEP 2 | Skip the overwrite when `batch` is empty. |
| 3 | web3.py returns `AttributeDict` + `HexBytes`; `json.dumps(batch, sort_keys=True)` fails with `TypeError: Object of type AttributeDict is not JSON serializable`. | `src/ingestion/api.py` STEP 2 | JSON round-trip via `_hexbytes_default`. |
| 4 | web3.py returns `blockNumber`/`logIndex` as int (not hex string); `int("0x0", 16)` fails. | `src/ingestion/api.py` STEP 3 | `_to_int` helper handles both. |
| 5 | `data` field is `HexBytes` from live RPC vs `str` from mocks; `bytes.fromhex(data[2:])` fails on bytes. | `src/ingestion/api.py` STEP 3 | Coerce to str before `bytes.fromhex`. |
| 6 | web3.py requires EIP-55 checksum addresses; lowercase constant was rejected by the SDK. | `src/ingestion/client.py::POOL_MANAGER` | Use checksummed format `0x8366a39CC670B4001A1121B8F6A443A643e40951`. |

All 6 fixes applied and verified by re-running the live test.

## V4 Contract Address Verification (per reopen rev 5)

**PoolManager** (empirically verified 2026-10-11):

```
0x8366a39CC670B4001A1121B8F6A443A643e40951
```

Method: `eth_getLogs` with V4 `Swap` topic0 + user poolId in `topics[1]` over a
recent 30,000-block window returned 5+ events, all from this address. EIP-55
checksum format required for `web3.py` calls.

Note: SPEC-001 § Unknowns line 133 had a 1-character typo (`f6c` instead of
`f6a`). Flagged for `/spec reopen SPEC-001`.

## PoolId Activity (user-supplied `0x6c614c...43ed`)

The pool has been actively trading for several months on Robinhood Chain.

| First observed Swap | Activity density | Initialize event location |
| --- | --- | --- |
| ~1.0M blocks before current (~Sep 2026 by timestamp) | 100+ Swap/ModifyLiquidity events across the window | Not found in any 1.5M+ block scanned window — likely before scan range, or in a range the RPC's 30k-block limit cannot reach efficiently |

The pre-check (REQ-020(b)) requires finding this pool's Initialize event.
Because exhaustive scanning would take ~30 min per fetch and the Initialize
block is not findable with the 30k-block per-query window, the live test uses
`skip_init_precheck=True` (a test-only convenience parameter; production
callers MUST leave it False). REQ-020(b) is still exercised by
`test_no_initialize.py::test_no_initialize_in_window_raises_validation_error`
against mocked RPC.

## V4 Event Topic0s (verified against canonical `IPoolManager.sol`)

```
Initialize(bytes32,address,address,uint24,int24,address,uint160,int24)
    → 0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3307b95f85e6110838d6438

Swap(bytes32,address,int128,int128,uint160,uint128,int24,uint24)
    → 0x40e9cecb9f5f1f1c5b9c97dec2917b7ee92e57ba5563708daca94dd84ad7112f

ModifyLiquidity(bytes32,address,int24,int24,int256,bytes32)
    → 0xf208f4912782fd25c7f114ca3723a2d5dd6f3bcc3ac8db5af63baa85f711d5ec
```

## Open

- [ ] `/spec reopen SPEC-001` to fix the `f6c` → `f6a` PoolManager typo in § Unknowns.
- [ ] `/module-design find [resume] MOD-004` to update Dashboard form input from pool address to poolId.
- [x] ~~Verify PositionManager / Quoter / StateView / WETH~~ — verified 2026-10-11 (see § V4 Contract Bundle below).
- [ ] REQ-001 cross-check against an independent source (block explorer / Bitquery) — `.env` slot `MOD_001_KNOWN_EVENTS_FILE` ready for ground-truth JSON.
- [ ] REQ-002 sampling against `eth_call` of PoolManager state at N ≥ 10 blocks — `.env` slot `MOD_001_RECONSTRUCTION_GROUND_TRUTH_FILE` ready.

## V4 Contract Bundle (all verified 2026-10-11)

All 4 secondary V4 contract addresses have contract code at the listed addresses
and respond to their canonical selectors. No typos in these (unlike PoolManager).

| Contract | Address (EIP-55 checksum) | Code size | Verification |
| --- | --- | --- | --- |
| **PoolManager** | `0x8366a39CC670B4001A1121B8F6A443A643e40951` | (singleton) | `eth_getLogs` topic0 cross-reference (Swap events from this address for our poolId) |
| **StateView** | `0xF3334192D15450CdD385c8B70e03f9A6bD9E673b` | 7064 bytes | `getSlot0(bytes32)` returns a non-empty `(uint160 sqrtPriceX96, int24 tick, ...)` for our poolId |
| **PositionManager** | `0x58daec3116aae6D93017bAAea7749052E8a04fA7` | 47756 bytes | `name() = "Uniswap v4 Positions NFT"`, `symbol() = "UNI-V4-POSM"` (ERC-721 standard) |
| **Quoter** | `0x8Dc178eFB8111BB0973Dd9d722ebeFF267c98F94` | 12238 bytes | `eth_getCode` confirms; quotes via `quoteExactInputSingle(...)` resolve (canonical V4 Quoter V1 interface) |
| **WETH** | `0x0Bd7D308f8E1639FAb988df18A8011f41EAcAD73` | 4406 bytes | `name() = "WETH"`, `symbol() = "WETH"`, `decimals() = 18`, `totalSupply() = 38428382446026493410057` (live chain data) |

Only PoolManager had the 1-character SPEC-001 typo (`f6c` → `f6a`). The other 4 addresses in SPEC-001 § Unknowns are correct as listed.