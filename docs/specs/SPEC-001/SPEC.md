---
id: SPEC-001
title: Robinhood Chain UniswapV4 LP Backtest System (Passive + CTA Modes)
status: active
source_intents:
  - INT-001
created: 2026-10-09
updated: 2026-10-09
---

# Scope and Sources

Consumes `INT-001` — build a Robinhood Chain UniswapV4 LP backtester with both passive range LP and CTA signal-driven active LP modes on the same reconstructed event stream, plus a local Robinhood-styled web dashboard.

No related Specs yet (this is the first).

User-locked technology decisions from the Intent (referenced for context, not re-decided here): Python tech stack, Python ecosystem for math/data, dashboard framework as recommended.

# System Capabilities

The Spec defines five tightly-coupled capabilities that share one event-reconstructed price stream:

1. **V4 event ingestion and pool-state reconstruction** — fetch V4 events for a single user-specified pool from the public Robinhood Chain RPC, reconstruct `(block_number, sqrtPriceX96, tick, liquidity, fee)` at every event.
2. **LP math engine** — concentrated-liquidity conversions, fee accumulation, impermanent loss, position value, capital accounting; the only module allowed to interpret pool state numerically.
3. **Passive range LP simulation** — single position, no rebalance; given range + capital, produce fees and IL over the window.
4. **CTA strategy engine** — pluggable indicator framework (Bollinger Bands first), per-swap signal evaluation, action dispatcher covering the six locked actions, single-position state model, fixed-capital allocation.
5. **Local web dashboard (Robinhood-styled)** — input form (pool address, range/capital, CTA settings); visualizations for both modes with comparable metrics.

# Requirements

## Functional

### Capability 1 — V4 Event Ingestion & Pool-State Reconstruction

- **REQ-001** (source INT-001#constraints-and-success-criteria, INT-001#decisions): Given a single user-supplied V4 pool address on Robinhood Chain, the system MUST fetch all `Swap`, `ModifyLiquidity`, and `Initialize` events for that pool from the public Robinhood Chain RPC within the user-supplied block window `[start_block, end_block]`, paginating via the RPC's documented per-`eth_getLogs` limits.
- **REQ-002** (source INT-001#facts-and-research): For every `Swap` event fetched, the system MUST reconstruct pool state `(sqrtPriceX96, tick, liquidity, fee)` from the post-event fields carried in that event's data, so downstream simulation operates on the same state values that existed on-chain at that block. For `ModifyLiquidity` events, the price-state fields `(sqrtPriceX96, tick)` inherit from the most recent prior `Swap` event on the same pool; the `liquidity` state MUST be updated by applying the event's `liquidityDelta` to the most recent `liquidity`. `fee` is only defined for `Swap` events.
- **REQ-003** (source INT-001#decisions): The system MUST persist fetched events to a local cache keyed by `(pool_address, start_block, end_block)` and MUST reuse the cache on subsequent runs with identical inputs, falling back to RPC only for missing ranges.

### Capability 2 — LP Math Engine

- **REQ-004** (source INT-001#clarified-intent, derived — see Derived section): The LP math engine MUST compute concentrated-liquidity conversions between `(sqrtPriceX96, tick, liquidity)` and per-position `(amount0, amount1)` for any tick in `[tickLower, tickUpper]`, with consistent rounding rules across all callers.
- **REQ-005** (derived — see Derived section): The math engine MUST treat all per-event state as immutable historical inputs; no path may write back into the reconstructed event stream or otherwise mutate previously-recorded state.
- **REQ-006** (source INT-001#decisions): For every event in the window during which a position is active, the engine MUST compute (a) fees accrued since the previous event, (b) impermanent loss vs the reference price series resolved in REQ-D02, and (c) the position's net value in `currency0` + `currency1`.

### Capability 3 — Passive Range LP Simulation

- **REQ-007** (source INT-001#decisions, INT-001#cta-strategy-mode): Given a position spec (pool address, capital amount, tick range `[tickLower, tickUpper]`, entry block, exit block), the passive simulation MUST emit a time series of position value, fee earnings, IL, and total asset change over the window, with one row per V4 event in the window.
- **REQ-008** (source INT-001#decisions): The passive simulation MUST NOT execute any rebalance, signal-driven action, or position mutation. Capital remains in the original range from entry to exit.
- **REQ-009** (source INT-001#clarified-intent, INT-001#evaluation): When the current tick leaves the position's `[tickLower, tickUpper]` during the window, the simulation MUST record that the position is out-of-range and accrues no further fees until the tick re-enters, without halting the simulation.

### Capability 4 — CTA Strategy Engine

- **REQ-010** (source INT-001#cta-strategy-mode): The system MUST provide a general technical-indicator + signal framework with a plug-in interface such that an indicator consumes the reconstructed price series and emits zero or more signals per swap event. Bollinger Bands MUST ship as the first concrete implementation; the interface MUST be stable enough that additional indicators (e.g., RSI, MACD) can be added without modifying the dispatcher.
- **REQ-011** (source INT-001#cta-strategy-mode): Signal evaluation MUST occur once per `Swap` event in the window. No bar resampling in v1.
- **REQ-012** (source INT-001#cta-strategy-mode): The CTA engine MUST support the action vocabulary `{add_liquidity, quit_liquidity, set_range, partial_withdraw, rebalance_only, stop_loss_take_profit}`. `stop_loss_take_profit` MUST trigger a forced `quit_liquidity` when the position's current value crosses a user-set threshold (one action type with direction).
- **REQ-013** (source INT-001#cta-strategy-mode): The CTA position-state model MUST enforce **exactly one open range at a time**. `add_liquidity` opens a new range after the prior one is fully quit.
- **REQ-014** (source INT-001#cta-strategy-mode): The CTA engine MUST allocate capital per `add_liquidity` from a user-set fixed total capital field; the default rule MUST allocate 100% of available cash to each new open.
- **REQ-015** (source INT-001#cta-strategy-mode, INT-001#decisions): The CTA simulation MUST emit the same metric series as the passive mode (per REQ-007) over the same event boundaries, so the two are directly comparable.

### Capability 5 — Local Web Dashboard

- **REQ-016** (source INT-001#decisions): The system MUST expose a local web dashboard styled in a Robinhood-style visual language (color palette, typography, layout density).
- **REQ-017** (source INT-001#decisions): The dashboard MUST expose, at minimum, the input fields: pool address, block window, passive-mode tick range + capital, CTA-mode capital + indicator params + action thresholds. Field values MUST be persisted per session.
- **REQ-018** (source INT-001#decisions): The dashboard MUST visualize, in a single comparable view, the metrics from REQ-007 / REQ-015 for both the passive and CTA modes over the chosen window, including fee income, APR, IL, and total asset change.
- **REQ-019** (source INT-001#evaluation): The dashboard MUST surface a data-coverage indicator (window length in blocks and time, number of events covered, age of last event) so users can judge the statistical adequacy of the backtest.

## Non-Functional

- **REQ-N01** (derived — reproducibility, see Derived section): Given identical inputs (pool address, block window, strategy params), two runs of the system MUST produce identical numeric outputs, up to the chosen output precision. (Justification: required for backtest validity; the user is a market maker evaluating strategies before deploying capital.)
- **REQ-N02** (derived — data integrity, see Derived section): The system MUST NOT silently mutate cached event data; cached event payloads MUST be byte-identical to what the RPC returned.
- **REQ-N03** (source INT-001#decisions, INT-001#clarified-intent): Ongoing operational data-acquisition cost MUST be zero — no paid archive provider, no third-party paid API. Local compute + storage only.
- **REQ-N04** (derived — observability, see Derived section): On every run, the system MUST log at minimum: pool address, block window, number of events fetched, number of cache hits, CTA action counts (per action type), and final position state.
- **REQ-N05** (source INT-001#clarified-intent): The dashboard MUST run locally — no cloud deployment, no hosted backend.

## Derived

- **REQ-D01** (derived from REQ-007 + REQ-015 comparability — justification: the user's intent requires "comparable P&L view" between passive and CTA modes, which only holds if both emit metrics in identical shape over identical event boundaries): The two strategy modes MUST emit their metric series over the same set of V4 events (event-aligned), not on independent time grids.
- **REQ-D02** (derived from REQ-006 — justification: V4 pool state at historical blocks is the cleanest available price source without adding new external dependencies; using the pool's own reconstructed swap-price series keeps the math self-consistent. This resolves the Unknown flagged in the source Intent): Impermanent loss MUST be computed relative to the pool's own reconstructed swap-price series, with entry price = reconstructed price at the position's entry block and comparison price = reconstructed price at each subsequent event in the window. If a downstream stage requires a different reference (e.g., a CEX oracle for cross-market IL), open a Spec change rather than overriding this locally.

# System Invariants and Dependencies

- **INV-01 (Single price stream)**: Both strategy modes MUST operate on the same reconstructed event stream. The data pipeline produces one canonical pool-state timeline; both modes consume it.
- **INV-02 (No future-data leakage)**: At every simulation step for a given block, neither the passive nor the CTA mode may observe events, state, or prices from blocks greater than the current block.
- **INV-03 (Single-position constraint, CTA mode)**: The CTA position-state model MUST hold at most one open range. The behavior for each CTA action when dispatched against an empty or illegal state is fixed as follows:
  - `add_liquidity` while a position is open MUST either be rejected or be expressed as a `quit_liquidity` followed by `add_liquidity`.
  - `quit_liquidity`, `partial_withdraw`, `set_range`, `rebalance_only`, and `stop_loss_take_profit` while no position is open MUST be no-ops and MUST be recorded as such in the strategy log.
  No other action ordering is permitted under the single-position model.
- **INV-04 (Capital conservation)**: For both modes, total capital in the system (free cash + position value, valued at the reconstructed swap price) MUST be conserved across all simulation steps up to the precision of the LP math engine; no value may appear or disappear.
- **INV-05 (Closed action vocabulary in v1)**: In v1, the CTA action set is exactly the six listed in REQ-012. Adding a new action is a Spec change, not a code-only change.

# Acceptance and Verification

**Capability Verification (per-Spec)**:

- *Passive mode*: Given a fixed position spec on a known pool + window, the metric series MUST match a reference calculation within a stated precision. Fees MUST be reconcilable to `amount0 + amount1 * price` within rounding tolerance. IL MUST match a piecewise analytical reference against the REQ-D02 reference price series: when the current tick is within `[tickLower, tickUpper]`, IL follows the symmetric-pool formula `2*sqrt(p)/(1+p) - 1` where `p = price_ratio`; when the current tick is outside the position's range, IL equals the value difference between the single-token LP position and the HODL split at the REQ-D02 reference price series.
- *CTA mode*: For a fixed indicator param set + action thresholds, replaying over a known event window MUST produce an identical action sequence to a reference oracle (e.g., a hand-rolled Bollinger Bands + threshold rule on the same price series).
- *Cross-mode comparison*: For identical pool + window + capital, the dashboard MUST show both modes' metric series aligned by event index.

**Contract Verification**:

- *Data pipeline emits canonical events*: Every event consumed by either strategy mode MUST be retrievable from the local cache by `(pool_address, block_number, log_index)`.
- *CTA indicator plug-in contract*: A new indicator implementation that conforms to the indicator interface MUST work without modifying the action dispatcher or simulation loop.

**System Verification**:

- *End-to-end dashboard run*: Starting from an empty cache, a fresh dashboard run on a known pool + window + both modes populated MUST complete (data fetch + simulation + render) within bounded local time, and the rendered metrics MUST match the per-mode reference outputs above.

# Architecture Handoff

Architecture must decide:

- **Module ownership** for each of the five capabilities — which module owns event ingestion, which owns the math engine, which owns the simulation loop, which owns the strategy engines, which owns the dashboard.
- **Public contracts** between (a) event ingestion and (b) LP math engine, (c) LP math engine and (d) strategy engines, (e) strategy engines and (f) dashboard.
- **Indicator interface** — exact method shape that indicator plug-ins must implement; must remain stable as new indicators are added (REQ-010).
- **Cache key format and storage backend** for REQ-003.
- **Dashboard framework choice** — the user-locked Python tech stack constrains the candidate set; the specific framework is Architecture's call.
- **CTA action threshold representation** — how user-set thresholds for `stop_loss_take_profit` (and any future threshold-driven actions) are expressed in the strategy config (units, sign convention, evaluation trigger).

# Unknowns and Upstream Feedback

- **Unknown** (runtime input, not blocking): Specific pool address, fee tier, and tick spacing per run. Resolved at runtime via the dashboard form.
- **Unknown** (runtime input, not blocking): Passive-mode tick range and capital per run; CTA-mode indicator params and action thresholds. Resolved at runtime via the dashboard form.
- **Unknown** (resolved in this Spec, see REQ-D02): External price reference for IL — resolved as **the pool's own reconstructed swap-price series**. Reason: smallest surface, internally consistent, no new external dependency. If a downstream stage requires a different reference, open a Spec change.
- **Feedback to Implementation / Architecture** (acceptance obligation): V4 contract addresses on Robinhood Chain (PoolManager `0x8366a39cc670b4001a1121b8f6c443a643e40951`, PositionManager `0x58daec3116aae6d93017baaea7749052e8a04fa7`, Quoter `0x8dc178efb8111bb0973dd9d722ebeff267c98f94`, StateView `0xf3334192d15450cdd385c8b70e03f9a6bd9e673b`, WETH `0x0Bd7D308f8E1639FAb988df18A8011f41EAcAD73`) are cited from a single secondary source (theagenttimes.com + Bitquery docs). Per the source Intent, Architecture/Implementation MUST re-verify these by direct on-chain `eth_call` before consuming them (e.g., read `protocolFees` slot or a known public getter on the PoolManager). Until verified, treat as **Unverified**.
- **Feedback to Implementation / Architecture** (acceptance obligation): Public RPC limits (10k logs per `eth_getLogs`, 10M blocks per query range) were empirically verified on 2026-10-08 against the V4 PoolManager. Implementation MUST honor these limits in pagination; if a query exceeds them, surface the limitation to the user rather than silently truncating.
- **Feedback to Implementation / Architecture** (acceptance obligation): Reconstruction accuracy — that the reconstructed state `(sqrtPriceX96, tick, liquidity, fee)` at block N matches the on-chain state at block N — MUST be empirically checked by sampling reconstructed values against direct RPC `eth_call` reads of the PoolManager's state at the same block, on at least a representative sample of blocks. This is an empirical verification, not a documentation check.
- **Feedback to Implementation / Architecture** (acceptance obligation): Statistical caveat — V4 on Robinhood Chain launched ~July 2026 (~3 months of history). Backtest results from this window may not be statistically robust. The dashboard's data-coverage indicator (REQ-019) is the user-facing mitigation; the existence of the indicator is required, but a quantitative confidence bound is not required in v1.

# Resume Notes

2026-10-09: Spec v1 drafted from INT-001. Risk review complete — no blocking unknowns. Spec-level decision recorded: IL reference price = pool's own reconstructed swap-price series (REQ-D02). Single Spec chosen because passive and CTA modes are tightly coupled by shared event pipeline, comparable metrics, and shared dashboard; splitting would create artificial boundaries. Architecture handoff lists open module-ownership / contract decisions. Acceptance obligations recorded for V4 contract-address verification, RPC pagination limits, reconstruction-accuracy sampling, and the statistical-coverage caveat. Ready for user review.

2026-10-09: Review Executed (Mode: Independent Review, full scope) by `independent-reviewer` subagent. 8 findings returned: 1 Confirmed Defect (Major, F1), 1 Probable Risk (Major, F2), 3 Probable Risk (Minor, F3 / F6 / F8), 3 Improvement Suggestion (Informational, F4 / F5 / F7). User authorized fixes for F1 / F2 / F3 / F8 only; F4 / F5 / F6 / F7 remain Unverified (deferred). Fixes applied: REQ-002 narrowed to `Swap` events with `ModifyLiquidity` propagation rule (F1); passive-mode IL acceptance changed to piecewise form (F2); REQ-006 "every block" → "every event" (F3); INV-03 expanded to cover all six CTA actions' empty-state dispatch semantics (F8). Trigger B criteria fire (acceptance language change / invariant expansion / granularity change); Targeted Resolution Verification will be delegated next. Authority Resolved: pending verification.

2026-10-09: Targeted Verification Executed (Mode B, scope F1 / F2 / F3 / F8) by `independent-reviewer` subagent using primary V4 ABI source (`Uniswap/v4-core IPoolManager.sol`). All four fixes Verified Fix; Necessary Conditions restored; no new material defects in scope. Two Minor / Informational ripple observations recorded (F1: REQ-002 silent on `Initialize` events — relevant only when window begins at pool launch, current default window does; F2: `p = price_ratio` shorthand — operative definition recoverable from REQ-D02). Neither blocks the four fixes. **Authority Resolved** for F1 / F2 / F3 / F8. F4 / F5 / F6 / F7 remain Unverified and are available for future authorization. Implementation Verified not claimed (no empirical observation; reconstruction accuracy and V4 address provenance remain Implementation / Architecture acceptance obligations per `# Unknowns and Upstream Feedback`).