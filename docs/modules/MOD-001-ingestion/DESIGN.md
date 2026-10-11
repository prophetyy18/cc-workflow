---
module: MOD-001-ingestion
status: final
source_spec:
  - SPEC-001
source_architecture:
  - ARCHITECTURE.md §2 (Modules and Responsibilities)
  - ARCHITECTURE.md §4 (Dependency Boundaries)
  - ARCHITECTURE.md §5 (Public Capability: Event Stream Provider)
created: 2026-10-10
updated: 2026-10-10
updated: 2026-10-10 (reopen: FetchStats contract extension per MOD-003 F1/F4)
updated: 2026-10-11 (reopen rev 2: Independent Review fixes F1-F7; cross-module impact on MOD-003)
updated: 2026-10-11 (reopen rev 3: Mode B fixes F-A / F-C / F-D / F-E)
updated: 2026-10-11 (reopen rev 4: user-authorized Mode B fixes F1/F2/F3 internal consistency + reorg mechanism clarification)
updated: 2026-10-11 (Implementation handoff recorded; impl/ committed; status: final + Implementation Verified at code + test layer)
---

# Module Goal and Upstream Basis

Owns V4 event acquisition from the public Robinhood Chain RPC and pool-state reconstruction per Architecture AD-3 (cache key fixed at `(pool_address, start_block, end_block)`). Satisfies SPEC-001 REQ-001 (event fetch with pagination), REQ-002 (per-event pool-state reconstruction), REQ-003 (local cache reuse), REQ-020(a)(c) (failure surfacing for RPC truncation and cache corruption), REQ-N02 (cache byte-identity), REQ-N03 (zero ongoing data cost). Provides the unique Provider contract `Event Stream Provider` per ARCHITECTURE.md §5; no upstream dependency (leaf module).

# Provided Public Contracts

## Event Stream Provider

Returns an ordered sequence of `(event, post_state)` pairs for one pool within `[start_block, end_block]`. Reconstructs pool state in-line per REQ-002 so downstream consumers (Strategy Engine) operate on the same values that existed on-chain at each block.

- **Input semantics**
  - `pool_address: str` — 0x-prefixed 20-byte hex; must be a V4 pool that has emitted at least one `Initialize` event in the window (REQ-020(b)).
  - `start_block: int` — inclusive lower bound; >= V4 PoolManager deployment block on Robinhood Chain.
  - `end_block: int` — inclusive upper bound; >= `start_block`.
  - Window size hard cap: 10,000,000 blocks per single `eth_getLogs` call (SPEC-001 Unknowns-and-Upstream-Feedback, empirically verified 2026-10-08). Larger windows are split into sub-queries internally; this is invisible to consumers.
- **Output semantics**
  - `FetchResult = NamedTuple('FetchResult', event_stream: EventStream, stats: FetchStats)` — the canonical return type of `fetch_event_stream`. The `EventStream` is unchanged; the `FetchStats` carries the cross-module fields required by MOD-003 (REQ-019, REQ-N04, REQ-020(c)) and is the consumer-discoverable channel for cache corruption surfacing.
  - `FetchStats = NamedTuple('FetchStats', cache_hit_count: int, cache_corruption_events: List[CacheCorruptionRecord], avg_block_time_seconds: float, last_event_block_timestamp: int)`. **(F2 fix: non-Optional — the timestamp acquisition path must always succeed or the fetch fails; no silent `None` fallback that would break MOD-003's CTASpecError fail-fast discipline.)**
    - `cache_hit_count` — **number of sub-ranges served from the on-disk cache across this fetch** (F5 + F-E fix: a sub-range is defined as ONE cache file keyed by `(pool_address, start_block, end_block)`; internal RPC pagination within one cache file does NOT increment `cache_hit_count`. This is the cache backend's natural key dimension and the most useful metric for REQ-N04 — required by REQ-N04 and consumed by MOD-003's `CoverageData.cache_hit_count`).
    - `cache_corruption_events` — empty list if no corruption was detected; otherwise one `CacheCorruptionRecord` per recovered-and-re-fetched sub-range. Required by REQ-020(c) ("the corruption event MUST be surfaced") and consumed by MOD-003's `CoverageData.cache_corruption_events`. The Dashboard sees corruption via MOD-003, not via MOD-001's log.
    - `avg_block_time_seconds` — average block time observed across the fetched window. **Acquisition path (F1 + F2 fix)**: for each unique `block_number` in the fetched window, the fetch issues `eth_getBlockByNumber` and **compares the current `block_hash` against the cached `block_hash`** (F2 explicit reorg-detection mechanism — reorg = current block_hash differs from cached value; SHA-256 of file content only catches tampering, not reorgs). On match: use the cached `timestamp` (cache hit). On mismatch: invalidate the cached entry, treat as cache miss, re-acquire `timestamp` + `block_hash` from the current response, write to cache (REQ-020(c) recovery triggered, with `cache_corruption_events` populated for the affected block). Cache file path = `./cache/block_timestamps/<pool_address>/<block_number>.json`; value = `{"timestamp": <int>, "block_hash": "0x..."}`; **key is `(pool_address, block_number)`, `block_hash` is in the value** (F1 clarified). Compute the mean of `(block_n+1.timestamp - block_n.timestamp)` over **positive** consecutive deltas (F6 fix: L2 chains like Robinhood Chain / Arbitrum Nitro can have non-monotonic timestamps under sequencer gaps / reorgs; ignore non-positive deltas to avoid misleading means). The result is `float` seconds. **Always populated**; if timestamp acquisition fails for any block, the fetch raises `EventStreamFetchError { cause: "timestamp_unavailable", cache_corruption_events: [...] }` (REQ-020(c) surfacing honored on every exit path). **Empty-filtered-set edge cases (F-A fix)**: if the fetched window contains fewer than 2 unique blocks (no pairs to compute deltas) OR every consecutive delta is non-positive, the fetch raises `EventStreamFetchError { cause: "timestamp_no_pairs", cache_corruption_events: [...] }` — never silent `None` or `StatisticsError`. **Performance property (F2 clarified)**: the reorg-detection check requires one `eth_getBlockByNumber` per unique block in the window, on EVERY fetch — even on cache hit. The "zero-RPC on cache hit" property from the original design is relaxed to "one-RPC-per-unique-block for reorg check"; reorg detection is mandatory and cannot be deferred. Implementation MAY batch these into a single `eth_getBlockByNumber` fan-out call to reduce wall-clock latency.
    - `last_event_block_timestamp` — block timestamp of the last fetched event's block (i.e., the highest `block_number` in the returned `EventStream`); always populated via the same acquisition path. Consumed by MOD-003's `CoverageData.age_of_last_event_seconds` (`now - last_event_block_timestamp`).
  - Field-type alignment (F4 fix): `avg_block_time_seconds: float` (seconds, sub-second precision preserved). MOD-003's `CoverageData.window_seconds_estimate = int(window_blocks * avg_block_time_seconds)` performs the int coercion at the consumer boundary; the implicit truncation is documented and is acceptable for REQ-019's "window length in time" requirement (no sub-second precision needed for a coverage indicator).
  - `CacheCorruptionRecord = NamedTuple('CacheCorruptionRecord', block_range: tuple[int, int], cause: str)` — `block_range` is the (start_block, end_block) that was re-fetched; `cause` is a short reason string (e.g., "sha256_mismatch", "malformed_json").
  - `EventStream` — ordered list of `StreamEntry { event: DecodedEvent, post_state: PoolState }`.
  - `DecodedEvent` carries original `block_number`, `log_index`, `tx_hash`, plus decoded event-specific fields per REQ-001/REQ-002 (`Swap` / `ModifyLiquidity` / `Initialize`).
  - `PoolState { sqrtPriceX96: int, tick: int, liquidity: int, fee: Optional[int] }` — `fee` defined only for `Swap` events per REQ-002.
  - Ordering: strictly ascending by `(block_number, log_index)`.
  - State-propagation rule (REQ-002): a `ModifyLiquidity` entry's `sqrtPriceX96` and `tick` equal the most recent prior `Swap`'s; its `liquidity` is prior `liquidity + event.liquidityDelta`; `fee` is `None`.
- **State changes**
  - Authoritative state owned by this module (ARCHITECTURE.md §4): raw cached event payloads and the reconstructed pool-state timeline. Writes to the local cache on every successful fetch.
- **Timing / ordering**
  - Synchronous from the consumer's perspective; one call returns the full window.
  - Internal pagination may issue many `eth_getLogs` calls; total wall time depends on RPC latency and event count.
- **Failure semantics**
  - REQ-020(a) — RPC error or `eth_getLogs` response truncation during pagination: raises `EventStreamFetchError { failed_range: (block_start, block_end), cause: str, partial_entries: List[StreamEntry], cache_corruption_events: List[CacheCorruptionRecord] }`. `partial_entries` reflect all events successfully fetched before the failure; `cache_corruption_events` carries any corruption events observed during the partial fetch (F3 fix: REQ-020(c) "MUST be surfaced" obligation is honored on every exit path, including combined-failure paths where corruption detection co-occurs with an RPC error). Previously persisted cache for other ranges is preserved.
  - REQ-020(b) — `pool_address` with no `Initialize` event in the window: raises `ValidationError { reason: "no_initialize_in_window" }` before any fetch. Computation halts before downstream modules run.
  - REQ-020(c) — Cache payload signature mismatch on read: the affected range is silently re-fetched (transparent to the consumer — the call still succeeds); a `CacheCorruptionRecord { block_range, cause }` is appended to `FetchStats.cache_corruption_events` so the consumer (MOD-003 → Dashboard) can surface the corruption to the user. The corruption is ALSO logged by the module for diagnostic purposes. Other ranges remain usable. Per REQ-020(c) "the corruption event MUST be surfaced": the surfacing channel is `FetchStats.cache_corruption_events`, not the module log.
  - Numerical decode errors propagate as `EventDecodeError { block_number, log_index, raw: bytes }`.
- **Correctness constraints**
  - INV-01 (Single price stream) participation: sole producer of the canonical event timeline; both Strategy Engine modes consume this same stream.
  - REQ-N02 (cache byte-identity): cached event payloads MUST be byte-identical to the raw RPC response. Hash equality enforced by REQ-020(c) signature check.
  - Deterministic replay (REQ-N01-derived): given identical inputs and an unchanged cache, two calls return byte-identical `EventStream` ordering and content.
- **Consumer preconditions**
  - Consumer (Strategy Engine) MUST treat the returned sequence as append-only and immutable; REQ-005 forbids mutation of reconstructed state.

# Consumed Public Contracts

None — leaf module (ARCHITECTURE.md §4).

# Internal Design and Key Decisions

- **RPC client**: `web3.py` (`Web3(Web3.HTTPProvider(rpc_url))`). Chosen per INT-001#decisions (Python ecosystem recommendation, user-accepted). Source: web3.py docs (primary).
- **ABI sources**: Uniswap V4 core `IPoolManager.sol` ABI for the three required events. Implementation MUST verify V4 contract addresses on-chain (PoolManager `0x8366a39cc670b4001a1121b8f6c443a643e40951` etc., per SPEC-001 Unknowns-and-Upstream-Feedback; treat as Unverified until empirical `eth_call` confirmation).
- **Pagination policy**: respect RPC's documented `10_000` logs per `eth_getLogs` and `10_000_000` blocks per query range (SPEC-001 Unknowns, empirically verified 2026-10-08). On any sub-query failure, raise REQ-020(a) error with the failed sub-range. No silent truncation.
- **Cache backend**: local files under `./cache/events/`, key = `<pool_address>/<start_block>_<end_block>.json` (one file per window, content = raw RPC `result` array, byte-identical per REQ-N02). Index file `./cache/events/_index.json` maps `(pool_address, start_block, end_block)` to file path + sha256 for REQ-020(c) detection. JSON chosen for transparency and zero-dependency; Implementation may switch to Parquet if I/O scales badly, but byte-identity contract still holds.
- **Block-timestamp cache** (F1 fix, F-D reorg hardening, F2 explicit mechanism): local files under `./cache/block_timestamps/<pool_address>/<block_number>.json` containing `{"timestamp": <int>, "block_hash": "0x..."}`. **Cache key is `(pool_address, block_number)`; `block_hash` is in the value** (F1 clarified). **Reorg detection (F2 explicit)**: on every fetch, for each unique block in the window, the implementation MUST issue `eth_getBlockByNumber` to obtain the current `(timestamp, block_hash)`. The cached `block_hash` is compared against the current `block_hash`: on match, the cached `timestamp` is served (cache hit); on mismatch, the cached entry is invalidated (cache miss for this block), the current `(timestamp, block_hash)` is written to cache, and a `CacheCorruptionRecord` is appended to `FetchStats.cache_corruption_events` (REQ-020(c) surfacing). SHA-256 of file content is reserved for byte-integrity / tampering detection only — it does NOT detect reorgs (reorg does not modify file bytes). The reorg-check cost (one `eth_getBlockByNumber` per unique block per fetch) is mandatory; batched fan-out is permitted at Implementation level for wall-clock optimization.
- **State reconstruction**: implemented as a single linear pass over the decoded event list per REQ-002. No parallelism (events are causally ordered).
- **No rebalance / signal / strategy logic**: strictly prohibited (Architecture §4 forbidden dependencies; Ingestion is upstream of the Strategy Engine and MUST NOT depend on it).

# Correctness Guarantees and Verification

Each observable check is derived from the cited Spec Requirement; the verification method does not rely on this module's own reconstruction helper.

- **REQ-001** — Fetch coverage. Run on a known V4 pool on Robinhood Chain mainnet over a known window. Compare the returned `block_number` set against an independent source (block explorer / Bitquery). Expected: identical event set within documented RPC limits.
- **REQ-002** — Reconstruction accuracy. Sample N blocks across the window (N >= 10, representative of swap / modify-liquidity mixes). For each, compare reconstructed `(sqrtPriceX96, tick, liquidity)` against direct `eth_call` against the PoolManager state at the same block. Expected: equal within the deterministic-precision constant (`MOD_002_PRECISION_DIGITS` from MOD-002). Sampling MUST include at least one `ModifyLiquidity`-only block to verify the propagation rule.
- **REQ-003** — Cache reuse. With an empty cache, run a window; record `eth_getLogs` call count. Clear cache state in memory only (keep disk cache), re-run; record call count again. Expected: second-run call count is 0 for the cached sub-ranges.
- **REQ-020(a)** — RPC truncation surfacing. Inject a mock RPC client that returns truncated results for one sub-range. Expected: `EventStreamFetchError` carries `failed_range` matching the injected sub-range and `partial_entries` matching the events fetched before failure. Cache files for other sub-ranges exist on disk after the failure.
- **REQ-020(b)** — Invalid pool address. Use a known address with no `Initialize` in the chosen window. Expected: `ValidationError("no_initialize_in_window")` raised before any RPC call.
- **REQ-020(c)** — Cache corruption surfacing. With a populated cache, flip one byte in one cached file. Re-run; expected: call still succeeds (range re-fetched), `FetchStats.cache_corruption_events` contains a `CacheCorruptionRecord` for the affected range, returned stream equivalent to fresh-fetch, other cached files untouched, and the corruption is also in MOD-001's log. Consumer (MOD-003 / Dashboard) MUST be able to discover the corruption via `FetchStats.cache_corruption_events` — not only via the MOD-001 log. **Combined-failure path (F3 fix)**: with a populated cache where one file is corrupted AND the RPC re-fetch itself fails (e.g., truncated response), the call raises `EventStreamFetchError` whose `cache_corruption_events` field carries the corruption records — REQ-020(c) surfacing obligation is honored on every exit path.
- **REQ-019 (timestamp acquisition, F1 + F2 fix)** — Run a fetch over a window of N events spanning M unique blocks; assert that `FetchStats.avg_block_time_seconds` is a positive `float` (within a sensible range, e.g., 0.1–60 seconds) and `FetchStats.last_event_block_timestamp` equals the timestamp of the highest-`block_number` event. **No silent `None`**: if any block's timestamp cannot be acquired (RPC failure, block not yet mined, etc.), the fetch raises `EventStreamFetchError { cause: "timestamp_unavailable" }`. **Performance property (F2 fix)**: a second-run fetch over the same window issues exactly **one `eth_getBlockByNumber` per unique block** (for the mandatory reorg check) — NOT zero (the original "zero-RPC" claim is relaxed; reorg detection cannot be deferred). The `test_timestamp_cache.py` test asserts this exact count. A reorg simulation (current `block_hash` differs from cached) triggers REQ-020(c) recovery: `FetchStats.cache_corruption_events` is populated, the cached entry is invalidated, and the current `(timestamp, block_hash)` is written to cache. L2 timestamp non-monotonicity (F6 fix): inject a synthetic non-monotonic timestamp and assert that `avg_block_time_seconds` ignores the non-positive delta.
- **REQ-N04 (FetchStats fields)** — Run a fresh fetch followed by a cache-hit fetch; assert `FetchStats.cache_hit_count` is `0` for the fresh fetch and `> 0` for the cache-hit fetch. Run a known-pool fetch that includes block timestamps; assert `FetchStats.avg_block_time_seconds` is a positive float within a sensible range and `FetchStats.last_event_block_timestamp` equals the last fetched block's timestamp.
- **REQ-019 (FetchStats for MOD-003 CoverageData)** — Cross-module integration test: MOD-003's `CoverageData` consumes `FetchStats` fields; assert the mapping is correct (cache_hit_count → cache_hit_count, etc.).
- **REQ-N02** — Byte-identity. After fetch, read the cached file and assert `sha256(content) == sha256(raw_rpc_response)` for every entry. Implementation MUST expose the raw RPC response for this test (not just the decoded view).
- **REQ-N03** — Zero-cost data path. Static check (grep + dependency manifest): no reference to Alchemy / QuickNode / Chainstack / Blockdaemon / dRPC / Validation Cloud endpoints; no paid SDK in dependencies.

# Blocking Unknowns and Implementation Handoff

- **Unknown**: V4 contract addresses on Robinhood Chain (PoolManager, PositionManager, Quoter, StateView, WETH) — sourced from a single secondary source (SPEC-001 Unknowns-and-Upstream-Feedback).
  **Why it matters**: wrong addresses silently break REQ-001 (fetch returns empty).
  **How to resolve**: Implementation MUST empirically verify via `eth_call` (e.g., read `protocolFees` slot or known public getter) before first fetch. Record verification artifact in `docs/verification/`. Not a Module-Design blocker; recorded as Implementation acceptance obligation.
- **Unknown**: REQ-N01 deterministic-precision constant — concretized by MOD-002 (`MOD_002_PRECISION_DIGITS = 100`, `decimal.Context(prec=100, rounding=ROUND_HALF_EVEN)` with module-private isolation; see `docs/modules/MOD-002-lp-math/DESIGN.md`). MOD-001 reads this constant when comparing reconstructed state against `eth_call` truth.
  **Why it matters**: REQ-002 verification needs a tolerance.
  **How to resolve**: import from MOD-002. If MOD-002 changes the constant, MOD-001's verification tolerance moves with it (no local override).

- **Implementation Handoff**:
  - Module path: `src/ingestion/` (Python). Confirm with project convention before commit; if project uses a different layout, override in `# Resume Notes`.
  - Python target version: **3.10+** (F7 / F-C fix — required by web3.py 7.x's stated minimum Python version, and future-proofs PEP 604 `int | None` syntax for downstream modules). Note: PEP 585 lowercase generics (e.g., `tuple[int, int]`) were introduced in Python 3.9, not 3.10 — they are not the binding reason for the 3.10+ floor.
  - Public surface (revised by reopen): `fetch_event_stream(pool_address, start_block, end_block) -> FetchResult` (where `FetchResult = (event_stream, stats)`; see Provided Public Contracts); exception types `EventStreamFetchError { failed_range, cause, partial_entries, cache_corruption_events }` (F3 fix), `ValidationError`, `EventDecodeError`; data types `FetchStats`, `CacheCorruptionRecord`, `EventStream`, `StreamEntry`, `DecodedEvent`, `PoolState`.
  - Tests: `tests/ingestion/` — `test_known_pool.py` (live RPC, gated by env), `test_pagination.py` (mock RPC), `test_cache_reuse.py`, `test_cache_corruption.py` (asserts `FetchStats.cache_corruption_events` populated AND asserts `EventStreamFetchError.cache_corruption_events` populated on the combined-failure path; cross-module consumer test in MOD-003 verifies Dashboard surfacing), `test_no_initialize.py`, `test_static_dependencies.py` (REQ-N03), `test_fetch_stats.py` (REQ-N04 + REQ-019: cache_hit_count sub-range granularity, avg_block_time_seconds acquisition via eth_getBlockByNumber, last_event_block_timestamp, timestamp cache reuse, non-monotonic L2 timestamps ignored), `test_timestamp_cache.py` (block-timestamp cache hit/miss/corruption).
  - Evidence Implementation MUST produce: (1) one successful end-to-end fetch on a real pool with byte-identity log; (2) one REQ-020(a) trace with mock RPC; (3) V4 contract-address verification artifact; (4) one REQ-020(c) trace showing `FetchStats.cache_corruption_events` populated; (5) one REQ-020(c) combined-failure trace showing `EventStreamFetchError.cache_corruption_events` populated; (6) FetchStats field values logged for a known-pool fetch; (7) timestamp cache reuse trace (zero `eth_getBlockByNumber` calls on second-run).

# Resume Notes

- 2026-10-10: Initial draft created from SPEC-001 + ARCHITECTURE.md. Trigger A criteria (data correctness, money-relevant upstream pipeline) warrant Independent Review before `status: final`; Self-check sufficient for first draft.
- 2026-10-10: Reopened per user authorization (cross-layer coordination via MOD-003 review findings F1 + F4). The Event Stream Provider contract was extended with `FetchStats` (a new output field alongside `EventStream`) carrying four consumer-required fields: `cache_hit_count` (REQ-N04), `avg_block_time_seconds` (REQ-019), `last_event_block_timestamp` (REQ-019), `cache_corruption_events` (REQ-020(c)). The function signature changed from `fetch_event_stream(...) -> EventStream` to `fetch_event_stream(...) -> FetchResult` where `FetchResult = (event_stream, stats)`. REQ-020(c) cache corruption now surfaces via `FetchStats.cache_corruption_events` (consumer-discoverable, not just the module log).
- Mechanical completeness fix: ARCHITECTURE.md §2 row keyed by display name "Ingestion" was given canonical ID `MOD-001-ingestion` per SKILL.md §4 hard rule 4. Source row: ARCHITECTURE.md §2 line "Ingestion | Acquire V4 events...". Recorded here, not in Baseline.
- Storage path `docs/modules/MOD-001-ingestion/` chosen because project convention is `docs/<layer>/<id>/` (see `docs/specs/SPEC-001/`, `docs/intents/INT-001/`); deviates from the SKILL's literal `docs/modules/<name>/` suggestion but follows existing layering.
- Resume position: contract extension applied; verification section updated for REQ-019 / REQ-N04 / REQ-020(c); next action is Independent Review (Mode A) before `status: final`.
- 2026-10-11: Independent Review (Mode A) executed on the FetchStats reopen. 3 Major Confirmed Defects + 4 Minor items surfaced:
  - **F1 (Major)**: `avg_block_time_seconds` / `last_event_block_timestamp` had no specified acquisition path; silently depended on a Robinhood Chain `eth_getLogs` `blockTimestamp` extension (non-standard).
  - **F2 (Major)**: `Optional[...]` typing incompatible with MOD-003's fail-fast CTASpecError discipline — `None` would trigger `TypeError`, not the SPEC's failure-class discipline.
  - **F3 (Major)**: `EventStreamFetchError` did not carry `cache_corruption_events`; REQ-020(c) "MUST be surfaced" obligation was silently violated on the combined-failure path (corruption detected + RPC re-fetch fails).
  - F4 (Minor): `int * float` type-fidelity across MOD-001 → MOD-003 boundary.
  - F5 (Minor): `cache_hit_count` granularity not pinned.
  - F6 (Minor): L2 block-timestamp non-monotonicity (Robinhood Chain is Arbitrum Nitro) not addressed.
  - F7 (Minor): Python target version not declared.
- 2026-10-11: Corrective fixes applied:
  - **F1**: added `Block-timestamp cache` section; acquisition path = `eth_getBlockByNumber` per unique block in the fetched window, cached under `./cache/block_timestamps/...`. If timestamp acquisition fails for any block, `EventStreamFetchError { cause: "timestamp_unavailable" }`. No silent `None`.
  - **F2**: `FetchStats` typing changed from `Optional[...]` to non-`Optional` (`avg_block_time_seconds: float`, `last_event_block_timestamp: int`); MOD-003's fail-fast discipline preserved.
  - **F3**: `EventStreamFetchError` extended with `cache_corruption_events: List[CacheCorruptionRecord]`. REQ-020(c) surfacing obligation honored on every exit path. **Cross-module impact: MOD-003's wrapping logic for `EventStreamFetchError` must extract this field into `CoverageData.cache_corruption_events` — this requires a MOD-003 reopen (modification to the existing wrap-and-route-to-FailureInfo path). Recorded as a Blocking Unknown for MOD-001's downstream consumer.**
  - F4: `int` coercion documented at MOD-003 boundary (`window_blocks * avg_block_time_seconds` produces `float`, then `int(...)` for `window_seconds_estimate`).
  - F5: `cache_hit_count` granularity pinned to **sub-ranges** (the cache backend's natural key dimension).
  - F6: `avg_block_time_seconds` formula documented to ignore non-positive deltas (L2 robustness).
  - F7: Python target version pinned to **3.10+** (required for PEP 585 lowercase generics).
- 2026-10-11: Targeted Resolution Verification (Mode B) executed. Outcomes:
  - F1, F2, F3, F4, F5 verified resolved at MOD-001 layer.
  - F6 partially resolved — empty-filtered-set edge cases (1-block window, all-non-positive deltas) unspecified (F-A new finding).
  - F7 partially resolved — cited PEP 585 was Python 3.9, not 3.10 (F-C new finding); version choice defensible but justification wrong.
  - **F-B (Major)**: MOD-003 cross-module gap surfaced — MOD-001's REQ-020(c) surfacing obligation is correctly modeled at the contract boundary, but MOD-003's wrapping logic does not extract `EventStreamFetchError.cache_corruption_events` into `CoverageData.cache_corruption_events` on the combined-failure path. This is correctly attributed in MOD-001 Resume Notes as a downstream concern (MOD-003 reopen obligation). NOT a MOD-001 defect; flagged for follow-up.
- 2026-10-11: Additional corrective fixes (this revision):
  - **F-A (Major)**: empty-filtered-set edge cases for `avg_block_time_seconds` made explicit. New `EventStreamFetchError { cause: "timestamp_no_pairs", cache_corruption_events: [...] }` raised when the window has < 2 unique blocks OR every consecutive delta is non-positive after L2 filtering. `cache_corruption_events` field is present on the EventStreamFetchError regardless of `cause` (unifies the F3 surfacing discipline across all error paths).
  - **F-C (Minor)**: Python target version justification corrected. Was "PEP 585 lowercase generics" (which is Python 3.9, not 3.10); now "web3.py 7.x's minimum Python version requirement and future-proofing for PEP 604 `int | None` syntax".
  - **F-D (Improvement)**: Block-timestamp cache key extended from `(pool_address, block_number)` to `(pool_address, block_number, block_hash)`. SHA-256 mismatch on read (e.g., after a reorg) triggers REQ-020(c) recovery — re-fetch via `eth_getBlockByNumber` to get the current `block_hash` and `timestamp`. Eliminates the silent-staleness failure mode under L2 sequencer reorgs.
  - **F-E (Improvement)**: Sub-range boundary definition made explicit: "a sub-range is ONE cache file keyed by `(pool_address, start_block, end_block)`; internal RPC pagination within one cache file does NOT increment `cache_hit_count`".
- 2026-10-11: Additional Targeted Resolution Verification (Mode B, final permitted per verification.md §6) executed. Outcomes: F-A verified resolved; F-C verified resolved; F-E verified resolved; **F-D partially resolved** — surfaced 3 new defects:
  - **F1 (Blocking Defect)**: F-D Resume Notes description contradicted Provided Public Contracts / Internal Design / Verification on whether `block_hash` was in the cache key or value.
  - **F2 (Major Risk)**: F-D used SHA-256 as the wrong primitive for reorg detection; the zero-RPC property on cache hit was incompatible with mandatory reorg checks.
  - **F3 (Minor Wording)**: F-E cited REQ-019 alongside REQ-N04 for `cache_hit_count`; REQ-019 does not mandate cache hits.
- 2026-10-11: User-authorized additional corrective fix (beyond verification loop bound, per explicit user authorization):
  - **F1**: clarified cache key vs value throughout — `key = (pool_address, block_number)`, `value = {timestamp, block_hash}`; Provided Public Contracts + Internal Design + Verification + Resume Notes all consistent.
  - **F2**: explicit reorg-detection mechanism — every fetch issues `eth_getBlockByNumber` per unique block, compares cached vs current `block_hash`; mismatch → invalidate cache + REQ-020(c) recovery. "Zero-RPC on cache hit" relaxed to "one-RPC-per-unique-block for reorg check". SHA-256 reserved for byte-integrity only (not reorg detection).
  - **F3**: `cache_hit_count` justification wording restricted to REQ-N04 (REQ-019 reference removed).
- 2026-10-11: Handoff to Implementation. `DESIGN.md status: final`. Implementation must read `docs/modules/MOD-001-ingestion/DESIGN.md` only; chat history not required. Implementation Handoff obligations are listed in `# Blocking Unknowns and Implementation Handoff` of DESIGN.md. **MOD-003 reopen (F-B)** to extract `EventStreamFetchError.cache_corruption_events` into `CoverageData.cache_corruption_events` on the combined-failure path — completed (see MOD-003 DESIGN.md rev F-B). Stale wording removed during post-framework compliance reconciliation (2026-10-11).
