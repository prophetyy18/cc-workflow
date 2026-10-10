---
module: MOD-003-strategy-engine
status: final
source_spec:
  - SPEC-001
source_architecture:
  - ARCHITECTURE.md §2 (Modules and Responsibilities)
  - ARCHITECTURE.md §4 (Dependency Boundaries)
  - ARCHITECTURE.md §5 (Public Capability: Strategy Result Provider)
  - ARCHITECTURE.md §6 (INV-02 / INV-03 / INV-04 integration / INV-05)
created: 2026-10-10
updated: 2026-10-10
---

# Module Goal and Upstream Basis

Owns the event-driven simulation loop and both strategy modes (passive range LP + CTA signal-driven active LP) over the same canonical event stream produced by MOD-001 Ingestion. Provides the unique Provider contract `Strategy Result Provider` per ARCHITECTURE.md §5. Satisfies SPEC-001 REQ-007..015, REQ-D01, REQ-D02, REQ-N04, and INV-02, INV-03, INV-05; participates in INV-04 (capital conservation, cross-module with MOD-002). Depends on MOD-001 (Event Stream Provider; status: final) and MOD-002 (LP Math Functions; status: final). Consumer: MOD-004 Dashboard.

# Provided Public Contracts

## Strategy Result Provider

Drives the simulation for both strategy modes on the same event stream, producing event-aligned metrics, the CTA action log, and the coverage indicator.

### Input semantics

- `SimulationRequest`
  - `pool_address: str` — V4 pool address (REQ-001 / MOD-001 contract).
  - `start_block: int` — inclusive lower bound (REQ-001).
  - `end_block: int` — inclusive upper bound (REQ-001).
  - `passive: Optional[PassiveSpec]` — if present, run the passive simulation.
  - `cta: Optional[CTASpec]` — if present, run the CTA simulation.
  - At least one of `passive` or `cta` MUST be provided.
- `PassiveSpec`
  - `tick_lower: int`, `tick_upper: int` — position range (REQ-007).
  - `capital_amount: Decimal` — currency0 units (REQ-007).
  - `entry_block: int`, `exit_block: int` — window for the passive run; must satisfy `start_block <= entry_block < exit_block <= end_block` (REQ-007).
- `CTASpec`
  - `capital_amount: Decimal` — fixed total capital, currency0 units (REQ-014).
  - `indicators: List[Indicator]` — plug-in instances (REQ-010); the dispatcher MUST NOT modify itself to accept new indicator types.
  - `thresholds: CTAThresholds` — user-set thresholds (REQ-012).
  - `indicator_to_action_map: Dict[str, Callable[[Signal], CTAAction]]` — required mapping from signal name to action. Behavior (F3 + F-C fix):
    - **Completely missing or empty** AND any indicator emits signals → dispatcher raises `CTASpecError("no_indicator_to_action_map_supplied")` listing the offending signal names.
    - **Partial map** (covers some signal names, misses others) → signals whose names are NOT in the map are silently dropped (no CTA action generated). This is the standard "selective mapping" pattern; not a defect.
  - **There is no silent default mapping** — this avoids silent business defaults.
- `CTAThresholds`
  - `stop_loss_take_profit: Optional[StopLossTakeProfitThreshold]`.
  - `partial_withdraw_fraction: Optional[Decimal]` ∈ (0, 1); default None (disabled). `partial_withdraw_fraction == 1.0` is rejected at CTASpec parse time with `CTASpecError("partial_withdraw_fraction=1.0 is equivalent to quit_liquidity; use quit_liquidity")` (F7 aliasing guard).
  - `rebalance_only` — no threshold; if present in `indicator_to_action_map`, enabled.
- `StopLossTakeProfitThreshold`
  - `threshold_fraction: Decimal` — for `direction='loss'`, negative (e.g., -0.10 = quit when value drops 10% from entry); for `direction='profit'`, positive (e.g., 0.50 = quit when value rises 50% from entry).
  - `direction: Literal['loss', 'profit']` — single action type with direction (REQ-012).
- `Indicator` — Protocol class with method `evaluate(history: Tuple[SwapEvent, ...], current_index: int) -> List[Signal]`; pure function. The dispatcher passes `tuple(swap_events[:current_index+1])` — the indicator sees ONLY events at or before `current_index`, structurally preventing future-event access. The signature's `Tuple` (immutable) plus the dispatcher's slice is the structural enforcement of INV-02 (F2). See Internal Design for the exact shape.
- `Signal = NamedTuple('Signal', name: str, direction: Literal['long','short','neutral'], strength: Decimal)` — emitted by indicators.
- `SwapEvent = NamedTuple('SwapEvent', block_number: int, log_index: int, sqrt_price_x96: int)` — minimal projection of MOD-001 `DecodedEvent` that indicators consume; the simulation MUST NOT expose the full `DecodedEvent` to indicators.

### Output semantics

- `SimulationResult`
  - `event_aligned_metrics: List[MetricRow]` — one row per V4 event in the window; strictly ascending by `event_index`.
  - `cta_action_log: List[CTAAction]` — chronologically ordered CTA action records (REQ-N04).
  - `coverage_indicator: CoverageData` — REQ-019.
  - `failure: Optional[FailureInfo]` — None on success; populated on REQ-020 failure.
- `MetricRow`
  - `event_index: int` — 0-based index into the event stream (join key for REQ-D01 alignment).
  - `block_number: int`, `log_index: int` — original ordering.
  - `event_type: Literal['Swap','ModifyLiquidity','Initialize']` — REQ-001 / REQ-002.
  - `passive: Optional[PassiveMetrics]` — populated iff `passive` spec was provided and `event_index` is within `[entry_block..exit_block]`.
  - `cta: Optional[CTAMetrics]` — populated iff `cta` spec was provided.
- `PassiveMetrics`
  - `principal_value: Decimal` (currency0 units; MOD-002 `position_net_value` output, principal-only).
  - `fees_value_in_c0: Decimal` (cumulative accrued fees, currency0 units; converted from `fees_between` outputs via `Decimal(fees0) + Decimal(fees1) / price` at REQ-N01 precision).
  - `il: Decimal` (fraction vs HODL; REQ-D02 reference).
  - `total_value: Decimal` (= `principal_value + fees_value_in_c0`, currency0 units, includes free cash).
  - `out_of_range: bool` (REQ-009). Formula: `(tick < tick_lower) or (tick >= tick_upper)`.
- `CTAMetrics`
  - `principal_value: Decimal`, `fees_value_in_c0: Decimal`, `il: Decimal`, `total_value: Decimal`, `out_of_range: bool`, `free_cash: Decimal`.
  - `out_of_range` formula (F8): `(tick < tick_lower) or (tick >= tick_upper)`. **CTA out-of-range is informational only — does NOT trigger any state-machine transition. The position continues; fees do not accrue while out-of-range; exit is signal-driven or stop-loss/take-profit only.** This is the asymmetry with passive mode: passive records but continues; CTA also continues, but the asymmetry is explicit (no auto-quit) so downstream consumers do not assume CTA behaves like passive on out-of-range.
  - **Structural requirement (REQ-015 + REQ-D01)**: the fields `principal_value`, `fees_value_in_c0`, `il`, `total_value`, `out_of_range` MUST have identical names and types to `PassiveMetrics`; verified at import time.
- `CTAAction`
  - `event_index: int`, `action_type: Literal['add_liquidity','quit_liquidity','set_range','partial_withdraw','rebalance_only','stop_loss_take_profit']` (REQ-012, INV-05), `params: dict`, `reason: str` — explains why the action fired (signal name, threshold breach, or `no_open_position` / `position_open` / `threshold_not_breached` for INV-03 / state-machine no-op cases).
- `CoverageData` (REQ-019)
  - `window_blocks: int = end_block - start_block + 1`.
  - `window_seconds_estimate: int` — `(end_block - start_block + 1) * avg_block_time_seconds`. **REQUIRED MOD-001 export.** If `avg_block_time_seconds` is not exposed, `run_simulation` raises `CTASpecError("MOD_001_MISSING_FIELD: avg_block_time_seconds")` — NO silent `-1` fallback (F-B fix; unifies with the four-fields-required discipline).
  - `event_count: int`.
  - `age_of_last_event_seconds: int` — `(now - last_event_block_timestamp)`. **REQUIRED MOD-001 export.** If `last_event_block_timestamp` is not exposed, `run_simulation` raises `CTASpecError("MOD_001_MISSING_FIELD: last_event_block_timestamp")` — NO silent `-1` fallback.
  - `cache_hit_count: int` — REQUIRED by REQ-N04; sourced from MOD-001's `fetch_event_stream` return shape. If MOD-001's contract does not export this field, MOD-003's `run_simulation` MUST raise `CTASpecError("MOD_001_MISSING_FIELD: cache_hit_count")`. **Cross-module dependency on MOD-001 (F4) — blocks `status: final` until MOD-001 reopens to add this field.**
  - `cache_corruption_events: List[CacheCorruptionRecord]` — REQUIRED by REQ-020(c) ("the corruption event MUST be surfaced"); sourced from MOD-001 on BOTH paths: (a) success path — from `FetchStats.cache_corruption_events`; (b) failure path — from `EventStreamFetchError.cache_corruption_events` (combined-failure mode where corruption detection co-occurs with RPC error). `CacheCorruptionRecord = NamedTuple('CacheCorruptionRecord', block_range: Tuple[int, int], cause: str)`. Empty list if no corruption occurred on either path. If MOD-001's contract does not export this field on BOTH paths, MOD-003's `run_simulation` MUST raise the same `CTASpecError`. **Cross-module dependency on MOD-001 (F1) — closed by MOD-001 reopen (now `status: final`).**
- `FailureInfo` (REQ-020)
  - `failure_class: Literal['rpc_truncation','no_initialize_in_window','lp_math_invalid_input','simulation_halted']`.
  - `cause: str`.
  - `partial_metrics: Optional[List[MetricRow]]` — events processed before the halt; None if halt occurred at entry (no partial metrics).
  - `cache_corruption_events: Optional[List[CacheCorruptionRecord]] = None` — populated ONLY on the failure path when `EventStreamFetchError.cache_corruption_events` is non-empty (combined-failure mode: corruption detected + RPC re-fetch fails). On the success path, this field is None and `CoverageData.cache_corruption_events` carries the corruption records (the dual-sink pattern: corruption is always surfaced, regardless of whether the run succeeds or halts). REQ-020(c) "MUST be surfaced" obligation is honored end-to-end across both paths.

### State changes

- Authoritative state owned (ARCHITECTURE.md §4): per-position state during simulation (INV-03 single-position CTA state machine; INV-04 capital conservation tracked via MOD-003's independent cash ledger).
- State is created at the start of `run_simulation` and released on completion (or on halt); NO persistent storage between calls.

### Timing / ordering

- Synchronous from the consumer's perspective; one call returns the full `SimulationResult`.
- Per-event processing is strictly sequential (no parallelism); events are causally ordered.
- INV-02 (no future-data leakage) is structurally guaranteed by:
  - The single-pass loop iterating in event_index order.
  - The `Indicator.evaluate(history, current_index)` interface where the dispatcher passes `tuple(swap_events[:current_index+1])` — an immutable `Tuple` containing exactly the events at or before `current_index`. An indicator conforming to the interface cannot access future events even by accident (F2).

### Failure semantics

- REQ-020: `FailureInfo` surfaces failure class + cause; computation halts on unrecoverable boundary; `partial_metrics` carries what was processed before the halt.
- Specific failure classes:
  - `"rpc_truncation"` — propagated from MOD-001's `EventStreamFetchError`; halt immediately; partial metrics reflect all events successfully fetched and processed.
  - `"no_initialize_in_window"` — propagated from MOD-001's `ValidationError`; halt before processing any event; partial_metrics = None.
  - `"lp_math_invalid_input"` — wrapped from MOD-002's `ValueError`; halt at the offending event; partial metrics reflect events processed before the offending one.
  - `"simulation_halted"` — MOD-003-internal halt for an unrecoverable boundary (e.g., persistent indicator bug); cause carries the reason.
- Recoverable MOD-001 issues (REQ-020(c) cache corruption) are surfaced via TWO sinks depending on the exit path:
  - **Success path**: `CoverageData.cache_corruption_events` (the run continues; corruption is visible via the Dashboard's coverage indicator).
  - **Failure path (combined-failure)**: `CoverageData.cache_corruption_events` AND `FailureInfo.cache_corruption_events` (the run halts due to RPC error; corruption is visible via both the FailureInfo and the CoverageData, ensuring the Dashboard can surface it through either surface).
  REQ-020(c) "the corruption event MUST be surfaced" is honored on every exit path. (F-B fix: cross-module impact from MOD-001 reopen — EventStreamFetchError now carries `cache_corruption_events`; MOD-003 extracts it on the failure path.)
- `CTASpecError` raised at validation time (e.g., missing `indicator_to_action_map`, `partial_withdraw_fraction == 1.0`, MOD-001 contract field missing) — fails fast before any computation begins.

### Correctness constraints

- INV-02 (no future-data leakage): simulation step for `event_index = N` MUST see only events with `event_index <= N`. Structurally enforced by (a) the single-pass loop and (b) the `Indicator` Protocol's `history: Tuple[SwapEvent, ...]` parameter, where the dispatcher passes only events at or before `current_index`.
- INV-03 (single-position CTA + 6-action dispatch): the CTA state machine enforces at most one open range; per-action × {open, closed} state semantics are fixed (see Internal Design).
- INV-04 (capital conservation, principal at entry; F1 + F-A refinement; F5 reclassification per WebFetch primary-source verification): MOD-003 maintains an independent cash ledger with two cash sub-fields — `free_cash = free_cash_principal + free_cash_earnings` (user-facing `free_cash` is the sum). The invariant is on the **principal** component: `free_cash_principal + position_value_at_entry_price == initial_capital` at every event_index after position open, within MOD-002's REQ-N01 precision (100-digit Decimal). Equivalently using the user-facing field: `(free_cash - total_fees_realized) + position_value_at_entry_price == initial_capital`. **`position_value_at_entry_price` is computed once at `add_liquidity` via MOD-002's `position_net_value(amounts_at_open, entry_sqrt_price_x96_snapshot)` — uses the entry event's `sqrt_price_x96`, NOT current price. This value is constant for the position's life** (token amounts unchanged under passive / partial_withdraw / set_range-equal-amounts; valuation price unchanged). Mark-to-market (`principal_value` in CTAMetrics / PassiveMetrics) is the user-facing P&L view; the INV-04 invariant uses a separate internal quantity.
  - **Fees accounting as a Design Choice (F5 reclassification, post-WebFetch primary-source verification 2026-10-11)**: V4 Position.sol `update()` returns `feesOwed0`/`feesOwed1` but does NOT transfer tokens on liquidity-decrease; a separate V4 `collect()` function handles the actual token transfer. MOD-003's ledger treats fees as **realized at quit/partial_withdraw for backtest economic accounting** — independent of V4's actual on-chain `collect()` flow. Rationale: backtest models the LP's economic P&L, and the LP would in practice call `collect()` on exit; modeling fees as realized at the simulator's liquidity-decreasing action is the simplest faithful accounting for the backtest's economic claim. This is a Design Choice, NOT a replication of V4's exact on-chain flow. Implementation MUST NOT change this without reopening this DESIGN.
  - The split (`free_cash_principal` + `free_cash_earnings`) is necessary because once fees are realized into free cash, the principal-only invariant must still hold; lumping them would break the invariant. This means:
  - Initial state (no position): `free_cash_principal = capital_amount`, `free_cash_earnings = 0`, `position_value_at_entry_price = 0`, `fees_value_in_c0 = 0`, `total_fees_realized = 0`. INV-04 holds.
  - At every event after position open: `free_cash_principal + position_value_at_entry_price == capital_amount` (the invariant holds — `free_cash_principal` only changes on actions; `position_value_at_entry_price` is constant under passive / partial_withdraw / set_range-equal-amounts, and is updated explicitly on set_range per F6 with the differential absorbed by `free_cash_principal` to preserve the invariant).
  - On `quit_liquidity`: `free_cash_principal += position_value_at_entry_price` (principal returned to principal-cash); `free_cash_earnings += fees_value_in_c0` (fees realized to earnings-cash per Design Choice — LP's economic outcome at exit); `total_fees_realized += fees_value_in_c0`; `position_value_at_entry_price = 0`; `fees_value_in_c0 = 0`. INV-04 holds.
  - On `partial_withdraw` with fraction `f`: `withdrawn_principal = position_value_at_entry_price * f`; `withdrawn_fees = fees_value_in_c0 * f`; `free_cash_principal += withdrawn_principal`; `free_cash_earnings += withdrawn_fees`; `total_fees_realized += withdrawn_fees`; `position_value_at_entry_price -= withdrawn_principal`; `fees_value_in_c0 -= withdrawn_fees`. INV-04 holds post-action.
- INV-05 (closed action vocabulary): action set is exactly the six listed; no other action types permitted in v1.
- REQ-N01 (deterministic precision): inherited from MOD-002 (100-digit Decimal, isolated context). MOD-003 MUST NOT mutate the global `decimal.getcontext()`; float inputs are forbidden at every numeric interface.
- REQ-D02 (IL reference):
  - **Passive**: `entry_sqrt_price_x96` = `sqrt_price_x96` of the first event in the window at or after `PassiveSpec.entry_block`. If no such event exists (entry_block outside the event stream), raise `ValidationError("entry_block_out_of_window")` (F9).
  - **CTA**: `entry_sqrt_price_x96` = reconstructed swap-price at the CTA position's `add_liquidity` event.

### Consumer preconditions

- Consumer (MOD-004 Dashboard) MUST treat `event_aligned_metrics` as append-only and read-only.
- Consumer MUST handle `failure != None` (graceful display of failure_class + cause; halt rendering of partial metrics per Dashboard's UX choice).
- Consumer MUST treat `cta_action_log` as a complete record (every CTA-fired signal that produced a state-machine event is logged, including no-ops per INV-03).

# Consumed Public Contracts

## Event Stream Provider (Provider: MOD-001 Ingestion)

- Contract location: `docs/modules/MOD-001-ingestion/DESIGN.md` (status: final; this DESIGN aligns with the contract content as specified there; any contract change requires MOD-003 reopen via Cross-layer Coordination).
- Used for: obtaining the canonical event timeline; the simulation MUST NOT fetch events directly.
- Per-event contract: receives `StreamEntry { event: DecodedEvent, post_state: PoolState }` ordered by `(block_number, log_index)`.
- MOD-001's exception types (`EventStreamFetchError`, `ValidationError`, `EventDecodeError`) propagate as-is and are wrapped into `FailureInfo`.
- **Required exports (now satisfied by MOD-001 reopen rev 4; status: final):**
  - `cache_hit_count: int` — required by REQ-N04 and `CoverageData.cache_hit_count` (F4).
  - `avg_block_time_seconds: Optional[float]` — required by `CoverageData.window_seconds_estimate` (F4; -1 fallback acceptable).
  - `last_event_block_timestamp: Optional[int]` — required by `CoverageData.age_of_last_event_seconds` (F4; -1 fallback acceptable).
  - `cache_corruption_events: List[CacheCorruptionRecord]` — required by REQ-020(c) and `CoverageData.cache_corruption_events` (F1).
- All four fields plus `EventStreamFetchError.cache_corruption_events` are exposed by MOD-001 (status: final, rev 4). MOD-003's `run_simulation` consumes them directly.

## LP Math Functions (Provider: MOD-002 LP Math)

- Contract location: `docs/modules/MOD-002-lp-math/DESIGN.md` (status: final).
- Used for: `sqrt_price_x96_to_price`, `amounts_at_tick`, `fees_between`, `il_against_reference`, `position_net_value`.
- MOD-003 reads `MOD_002_PRECISION_DIGITS = 100`; does NOT mutate the global `decimal.getcontext()`; float inputs are forbidden.
- MOD-003's independent cash ledger does NOT call any "accounting helper" from MOD-002 (none exists); ledger is maintained by MOD-003 against `position_net_value(...)` outputs only.

# Internal Design and Key Decisions

## Event-driven simulation loop

Single linear iteration over MOD-001's `EventStream` in `(block_number, log_index)` order. For each event:

1. Extract `sqrt_price_x96` and `tick` from the per-event `post_state`.
2. If a passive spec was provided and the event is within `[entry_block..exit_block]`: compute passive metrics via MOD-002; record row.
3. If a CTA spec was provided:
   a. On `Swap` events: invoke each `Indicator.evaluate(tuple(swap_events_so_far), current_index)` (REQ-011 per-Swap evaluation; structural INV-02 enforcement via the sliced `Tuple`); consume the resulting `List[Signal]` per `indicator_to_action_map` to produce zero or more proposed CTA actions; apply each via the state machine; check `stop_loss_take_profit` threshold against the post-state position value; record actions to `cta_action_log` and `MetricRow.cta`.
   b. On `ModifyLiquidity` events: do NOT invoke indicators (REQ-011 per-Swap evaluation); update MOD-001's per-event `liquidity` field in the cached state for downstream use.
   c. On `Initialize` events: passive-only event; CTA does nothing.
4. Advance `event_index` and continue.

INV-02 is structurally guaranteed: the loop body has no access to future events, AND the indicator interface cannot see future events (F2).

## Passive strategy (REQ-007..009)

- At `entry_block`: position `[tickLower, tickUpper]` with `capital_amount`; `entry_sqrt_price_x96 = sqrt_price_x96 of the first event in the window at or after entry_block` (F9); no rebalance ever (REQ-008).
- At each event within `[entry_block..exit_block]`:
  - `out_of_range = (tick < tick_lower) or (tick >= tick_upper)`.
  - `principal_value = position_net_value(amounts_at_tick(...), price)` via MOD-002 (principal only).
  - `fees_value_in_c0` = cumulative sum since entry, converted from `fees_between` outputs; zero while `out_of_range` (REQ-009).
  - `il` = `il_against_reference(entry_sqrt_price_x96, current_sqrt_price_x96, lower_sqrt_price_x96, upper_sqrt_price_x96)` (REQ-D02, F9).
  - `total_value = principal_value + fees_value_in_c0` (passive has no separate free_cash; capital is fully deployed at entry).
- Exit at `exit_block`: position value at exit = final `passive_total_value`; simulation continues to record CTA rows (if CTA active) but passive rows beyond `exit_block` have `passive = None`.
- **No** rebalance, signal evaluation, or position mutation (REQ-008). REQ-009 out-of-range regime is recorded but does NOT halt.

## CTA strategy (REQ-010..015, INV-03)

CTA state machine:

```python
class CTAPositionState:
    status: Literal['no_position', 'open']
    tick_lower: int                # when status == 'open'
    tick_upper: int                # when status == 'open'
    liquidity: int                 # uint128, when status == 'open'
    entry_sqrt_price_x96: int      # sqrt_price_x96 at the add_liquidity event (REQ-D02)
    entry_event_index: int         # for logging
    entry_position_value_at_entry_price: Decimal  # snapshot at add_liquidity; constant for the position's life; used for INV-04 invariant (F-A fix)
    entry_principal_value_at_current: Decimal     # mark-to-market at entry; for stop_loss_take_profit comparison (current mark-to-market vs entry mark-to-market)
    entry_fees_value_in_c0: Decimal # fees accrued since entry; for proportional withdraw / stop-loss comparison
```

Per-action × {open, closed} semantics (REQ-013 + INV-03):

| Action | Open | Closed |
|---|---|---|
| `add_liquidity` | **Rejected**, log `reason="position_open"` (per INV-03: rejected is one of the two permitted choices; `quit+add` is the other; MOD-003 commits to **rejected** for v1) | Opens new range from `free_cash`, allocates 100% of available cash per REQ-014 default |
| `quit_liquidity` | Closes; `free_cash += principal_value + fees_value_in_c0`; `principal_value = 0`; `fees_value_in_c0 = 0` (realized per Design Choice for backtest accounting — see F5 reclassification) | No-op; log `reason="no_open_position"` |
| `set_range` | Updates `[tick_lower, tick_upper]`; rebalances tokens at current price using `new_amounts_at_tick(current_sqrt_price_x96, new_lower, new_upper, liquidity)`; `new_position_value_at_entry_price = position_net_value(new_amounts, entry_sqrt_price_x96_snapshot)`; differential `d = new_position_value_at_entry_price - position_value_at_entry_price` absorbed into `free_cash_principal` (negative d → `free_cash_principal += |d|`; positive d → `free_cash_principal -= d`, `CTASpecError("set_range_differential_requires_cash")` if insufficient); preserves INV-04 by construction (F3 fix) | No-op; log `reason="no_open_position"` |
| `partial_withdraw` | `f = partial_withdraw_fraction`; `withdrawn_principal = principal_value * f`; `withdrawn_fees = fees_value_in_c0 * f`; `free_cash += withdrawn_principal + withdrawn_fees`; `principal_value -= withdrawn_principal`; `fees_value_in_c0 -= withdrawn_fees`. (`partial_withdraw_fraction == 1.0` rejected at CTASpec parse — F7.) | No-op; log `reason="no_open_position"` |
| `rebalance_only` | `quit_liquidity` then `add_liquidity` at the same event boundary (single log entry with both sub-actions) | No-op; log `reason="no_open_position"` |
| `stop_loss_take_profit` | If `(current_value - entry_value) / entry_value` crosses `threshold_fraction` (per direction), force `quit_liquidity`; otherwise no-op (still log `reason="threshold_not_breached"`) | No-op; log `reason="no_open_position"` |

**`set_range` formula (F6 + F3 fix)**: When changing `[tick_lower, tick_upper]` with the same `liquidity`:
- `new_amount0, new_amount1 = amounts_at_tick(current_sqrt_price_x96, new_lower, new_upper, liquidity)`
- `new_position_value_at_entry_price = position_net_value(new_amounts, entry_sqrt_price_x96_snapshot)` — uses the entry event's `sqrt_price_x96` snapshot (NOT current price), consistent with the F-A split-formulation.
- `differential = new_position_value_at_entry_price - position_value_at_entry_price`
- If `differential > 0`: `free_cash_principal -= differential` (the LP's principal cash is consumed to absorb the additional tokens required by the new range; `CTASpecError("set_range_differential_requires_cash")` if insufficient).
- If `differential < 0`: `free_cash_principal += |differential|` (the LP receives principal cash from the surplus tokens released by the new range).
- `position_value_at_entry_price = new_position_value_at_entry_price`. INV-04 preserved by construction.

**Open commitment**: `add_liquidity` while open is **rejected**, not auto-expressed as `quit+add`. INV-03 permits either choice; MOD-003 commits to **rejected** for v1.

## Indicator framework (Architecture §9 deferred → resolved here; F2 fix)

Interface:

```python
from typing import Protocol, List, Literal, Tuple
from decimal import Decimal
from typing import NamedTuple

class SwapEvent(NamedTuple):
    """Minimal projection of MOD-001's Swap event that indicators consume."""
    block_number: int
    log_index: int
    sqrt_price_x96: int

class Signal(NamedTuple):
    name: str                              # e.g., "bollinger_upper_break"
    direction: Literal['long', 'short', 'neutral']
    strength: Decimal                      # in [0, 1]

class Indicator(Protocol):
    """Pure function: same (history, current_index) → same List[Signal].
    The dispatcher passes an immutable Tuple containing ONLY events at or
    before current_index — structural INV-02 enforcement."""
    def evaluate(self, history: Tuple[SwapEvent, ...], current_index: int) -> List[Signal]: ...
```

- The dispatcher calls `evaluate(tuple(swap_events[:current_index+1]), current_index)` ONCE per Swap event (REQ-011).
- The `Tuple` parameter is immutable; the slice contains exactly `current_index + 1` events; an indicator cannot access events past `current_index` even by accident.
- Dispatcher's `indicator_to_action_map` translates each `Signal` to a CTA action via a user-supplied callable. There is **no default mapping** — if indicators emit signals but the map is missing/empty, the dispatcher raises `CTASpecError("no_indicator_to_action_map_supplied")` (F3).
- Adding a new indicator MUST NOT modify the dispatcher (REQ-010); verified by structural test (see Verification).

## Action threshold representation (Architecture §10 deferred → resolved here; F7 fix)

```python
class StopLossTakeProfitThreshold(NamedTuple):
    threshold_fraction: Decimal            # negative for loss, positive for profit
    direction: Literal['loss', 'profit']

class CTAThresholds(NamedTuple):
    stop_loss_take_profit: Optional[StopLossTakeProfitThreshold]
    partial_withdraw_fraction: Optional[Decimal]   # (0, 1); None = disabled; 1.0 rejected at parse time
    # rebalance_only has no threshold; presence in indicator_to_action_map enables it.
```

- Trigger evaluation per event for an open position (F-D fix): `breach = (current_total_value - entry_total_value) / entry_total_value` where `entry_total_value = entry_principal_value_at_current + entry_fees_value_in_c0` (= position's entry mark-to-market + fees accrued since entry). Rationale: the user's strategy P&L includes fees; a stop-loss/take-profit threshold compares against the position's realized entry value (capital + accumulated fees). At `add_liquidity` time, `entry_fees_value_in_c0 = 0`, so `entry_total_value == entry_principal_value_at_current` and the formula is symmetric with the principal-only formulation at the entry instant. For `direction='loss'`: `breach <= threshold_fraction`. For `direction='profit'`: `breach >= threshold_fraction`. On breach, force `quit_liquidity` at that event.
- `partial_withdraw_fraction` is consumed at the moment `partial_withdraw` action fires; the formula `withdrawn_principal = principal_value * f` (proportional to mark-to-market) is the committed choice (F7).
- `rebalance_only` is fire-on-signal only.

## Capital ledger (REQ-014, INV-04; F5 reword + F-A refinement)

MOD-003 maintains an INDEPENDENT cash ledger, separate from MOD-002's `position_net_value` outputs:

```python
# Internal ledger (not directly user-facing; user sees only `free_cash`)
free_cash_principal: Decimal           # principal portion of free cash
free_cash_earnings: Decimal            # realized fees (running sum)
position_value_at_entry_price: Decimal # constant for an open position's life; computed once at add_liquidity
fees_value_in_c0: Decimal              # unclaimed fees since last realization
total_fees_realized: Decimal           # running sum of realized fees (= free_cash_earnings; kept for INV-04 cross-check)

# User-facing field (exposed via CTAMetrics.free_cash)
@property
def free_cash(self) -> Decimal:
    return free_cash_principal + free_cash_earnings
```

**INV-04 (principal conservation, principal at entry; F-A refinement)**: `free_cash_principal + position_value_at_entry_price == initial_capital` at every event_index after position open, within MOD-002's REQ-N01 precision (100-digit Decimal). Equivalently, using the user-facing `free_cash` field: `(free_cash - total_fees_realized) + position_value_at_entry_price == initial_capital`. `position_value_at_entry_price` is computed once at `add_liquidity` via MOD-002's `position_net_value(amounts_at_open, entry_sqrt_price_x96_snapshot)` using the entry event's `sqrt_price_x96` (NOT current price) — constant for the position's life (token amounts unchanged under passive / partial_withdraw / set_range-equal-amounts; valuation price unchanged).

Fees are external income tracked separately via `fees_value_in_c0`; credited to `free_cash_earnings` on liquidity-decreasing actions **as a Design Choice for backtest economic accounting** (F5 reclassified post-WebFetch primary-source verification — V4 `Position.update()` does NOT auto-credit on decrease; a separate `collect()` function handles token transfer. See Correctness Constraints INV-04 paragraph for full rationale.) The split is necessary because once fees are realized to free_cash, the principal-only invariant must still hold (sum without fees).

Initial state (no position):
- `free_cash_principal = capital_amount; free_cash_earnings = 0; position_value_at_entry_price = 0; fees_value_in_c0 = 0; total_fees_realized = 0`.
- INV-04: `capital + 0 == capital` ✓

Updates per CTA action:
- `add_liquidity`:
  - `free_cash_principal -= position_value_at_entry_price_at_open` (= MOD-002's `position_net_value(amounts_at_open, sqrt_price_x96_at_open)`)
  - `position_value_at_entry_price = position_value_at_entry_price_at_open`
  - `fees_value_in_c0 = 0` (reset on new position)
  - INV-04: `(capital - deployed) + deployed == capital` ✓
- `quit_liquidity`:
  - `principal_to_return = position_value_at_entry_price`
  - `fees_to_realize = fees_value_in_c0`
  - `free_cash_principal += principal_to_return`
  - `free_cash_earnings += fees_to_realize`
  - `total_fees_realized += fees_to_realize`
  - `position_value_at_entry_price = 0`
  - `fees_value_in_c0 = 0`
  - INV-04: `(free_cash_principal + principal_to_return) + 0 == capital` ✓ (free_cash_principal returns to its pre-add_liquidity value; free_cash_earnings now contains realized fees, separately)
- `set_range` (F6): see formula above. `position_value_at_entry_price` recomputed — for a CL position the entry-price valuation depends on token amounts which DO change under `set_range` (the differential is absorbed by `free_cash_principal`). `position_value_at_entry_price` after `set_range` = MOD-002's `position_net_value(new_amounts, entry_sqrt_price_x96_snapshot)`. Ledger absorbs the differential to preserve INV-04 (see F6 formula for details).
- `partial_withdraw` with fraction `f`:
  - `principal_to_return = position_value_at_entry_price * f`
  - `fees_to_realize = fees_value_in_c0 * f`
  - `free_cash_principal += principal_to_return`
  - `free_cash_earnings += fees_to_realize`
  - `total_fees_realized += fees_to_realize`
  - `position_value_at_entry_price -= principal_to_return`
  - `fees_value_in_c0 -= fees_to_realize`
  - INV-04: holds by construction.
- `rebalance_only`: `quit_liquidity` + `add_liquidity` at the same event boundary.

The ledger is owned by MOD-003 (no MOD-002 helper exists); per MOD-002's "Out-of-Module Verification" section, INV-04 property test lives here and uses an INDEPENDENT ledger.

**Implementation MUST verify V4 Position.sol primary source before treating this reword as authoritative** (SPEC-001 Unknowns-and-Upstream-Feedback discipline).

## Metrics aggregator

- One `MetricRow` per `event_index`; `passive` and `cta` columns populated independently if their respective specs were provided.
- REQ-D01 alignment: `event_index` is the join key; passive and CTA rows for the same `event_index` come from the same underlying pool event.
- REQ-015 (CTA same shape): structural type check at import time asserts `PassiveMetrics` and `CTAMetrics` share the field names and types for `principal_value`, `fees_value_in_c0`, `il`, `total_value`, `out_of_range`.

## Coverage indicator (REQ-019)

- `window_blocks = end_block - start_block + 1` (always computable).
- `window_seconds_estimate = window_blocks * avg_block_time_seconds` (from MOD-001).
- `event_count = len(event_aligned_metrics)`.
- `age_of_last_event_seconds = now - last_event_block_timestamp` (from MOD-001).
- `cache_hit_count` (from MOD-001) — REQUIRED by REQ-N04; failure mode: raise `CTASpecError` rather than silently -1.
- `cache_corruption_events` (from MOD-001) — REQUIRED by REQ-020(c); failure mode: raise `CTASpecError`.

## Logger (REQ-N04; F10 fix)

At the end of each `run_simulation` call, log a structured record containing:
- `pool_address`, `start_block`, `end_block`, `event_count`, `cache_hits` (from MOD-001).
- `cta_action_counts: Dict[action_type, int]` — count of `cta_action_log` entries per `action_type` (INCLUSIVE of no-ops; matches the consumer-precondition that `cta_action_log` is the complete record).
- `cta_realized_action_counts: Dict[action_type, int]` — same but EXCLUDING entries with `reason in {"position_open", "no_open_position", "threshold_not_breached"}` (state-changing actions only).
- `final_position_state`: CTA position state at end of window (open / no_position + ranges / cash).

## Failure surfacer (REQ-020)

- Wraps MOD-001 exceptions (`EventStreamFetchError`, `ValidationError`, `EventDecodeError`) into `FailureInfo` with mapped failure_class + cause.
- **Combined-failure path (F-B fix)**: when wrapping `EventStreamFetchError`, the failure surfacer extracts `e.cache_corruption_events` and populates BOTH `CoverageData.cache_corruption_events` AND `FailureInfo.cache_corruption_events` (the dual-sink pattern described above). The Dashboard sees the corruption through either surface.
- Wraps MOD-002 numerical exceptions (`ValueError` from `fees_between` etc.) as `lp_math_invalid_input`.
- Halt on unrecoverable boundary; populate `partial_metrics` with what was processed.
- `cache_corruption_events` from MOD-001 surface via `CoverageData` (success path; F1) AND via both `CoverageData` and `FailureInfo` (failure path; F-B fix). Per REQ-020(c) "other ranges MUST be usable" — on the success path the run continues; on the failure path the corruption history is preserved alongside the failure record.

# Correctness Guarantees and Verification

For each assigned Spec Requirement and Invariant:

- **REQ-007 (passive metric series)** — Golden fixture: replay a fixed event sequence over a known pool state; assert every `MetricRow.passive` matches an external reference (hand-computed or reference V4 SDK). Expected values written down before Implementation.
- **REQ-008 (no rebalance)** — Count `passive` state mutations across a run; assert 0; assert `passive.principal_value` changes only via fee accrual (not via range change).
- **REQ-009 (out-of-range recording)** — Replay a window where tick exits `[tick_lower, tick_upper]`; assert `MetricRow.passive.out_of_range == True` from exit to re-entry; assert `fees_value_in_c0` is constant (zero delta) during out-of-range; assert simulation does NOT halt.
- **REQ-010 (indicator plug-in)** — Instantiate a third-party indicator (stub `Indicator` defined in the test file, NOT in MOD-003 source); run a fixed event sequence; assert the simulation completes and `cta_action_log` reflects the stub's signals; assert MOD-003 dispatcher source files are unchanged from before the test (no added branches for the stub).
- **REQ-011 (per-swap signal eval)** — Count `Indicator.evaluate(...)` invocations during a fixed-event run; assert equal to the count of `Swap` events (NOT `ModifyLiquidity`).
- **REQ-012 (action vocab)** — Static check: `grep` MOD-003 source for action-type string literals; assert exactly 6 distinct values; assert no other action names appear in the `Literal[...]` type.
- **REQ-013 (single-position semantics)** — Table-driven test: 6 actions × 2 states (open, closed) = 12 cases; for each, assert the documented outcome (mutation + ledger update OR no-op + log entry with `reason="no_open_position"` / `"position_open"`).
- **REQ-014 (capital sizing)** — Replay a fixed event sequence with N `add_liquidity` actions; assert `free_cash` after each `add_liquidity` equals `expected_remaining_cash` per the 100% rule; assert INV-04 (principal) invariant holds after each action.
- **REQ-015 (CTA same metric shape)** — Structural type check at import time: `CTAMetrics` and `PassiveMetrics` share field names and types for `principal_value`, `fees_value_in_c0`, `il`, `total_value`, `out_of_range`; assert by introspection (`dataclasses.fields`).
- **REQ-D01 (metric alignment)** — Replay the same event stream with both `passive` and `cta` specs; assert `event_index → MetricRow` mapping is 1:1; assert no `event_index` appears in one mode and not the other.
- **REQ-D02 (IL reference, F9 fix)** — Replay a known price walk; assert CTA `il` values correspond to MOD-002's `il_against_reference` called with `entry_sqrt_price_x96` = sqrt_price_x96 at the CTA's `add_liquidity` event. For passive: assert `entry_sqrt_price_x96` = sqrt_price_x96 of the first event at or after `PassiveSpec.entry_block`. Cross-verify by calling MOD-002 directly on the same inputs. Additionally: an `entry_block` outside the event stream window MUST raise `ValidationError("entry_block_out_of_window")`.
- **REQ-N04 (logging)** — Capture log output; assert required fields present per run; assert `cta_action_counts` includes no-ops; assert `cta_realized_action_counts` excludes them.
- **REQ-N01 (deterministic precision)** — Cross-module pollution regression guard: set `decimal.getcontext().prec = 28` BEFORE importing MOD-003; assert preservation after every MOD-003 call (same guard as MOD-002's).
- **INV-02 (no future-data)** — Controlled fixture: construct an `EventStream` with a deliberate future event placed at index 5; instrument the indicator harness to record the maximum `current_index` ever passed to `evaluate(...)`; assert it equals the run's final event_index. Additionally: assert no indicator in the test corpus accesses `history[current_index+1]` (F2 structural enforcement).
- **INV-03 (single-position + dispatch)** — Combined with REQ-013 table test.
- **INV-04 (capital conservation, principal at entry; F-A refinement)** — Property test: 1000 random event walks (Hypothesis); at every event_index after position open, assert `free_cash_principal + position_value_at_entry_price == initial_capital` within MOD-002's 100-digit Decimal precision. Equivalently, assert `(free_cash - total_fees_realized) + position_value_at_entry_price == initial_capital` using the user-facing `free_cash` field. `position_value_at_entry_price` is computed once at `add_liquidity` via MOD-002's `position_net_value(amounts_at_open, entry_sqrt_price_x96_snapshot)` — uses the position's `add_liquidity` event's `sqrt_price_x96` snapshot (NOT current price), and is constant for the position's life. Ledger is MOD-003-owned (independent of MOD-002's helpers). After `quit_liquidity`: assert `free_cash_principal == initial_capital` (principal fully returned), and `free_cash_earnings == total_fees_realized == cumulative_fees_value_in_c0_at_quit` (fees realized). This is the externally observable invariant the V4 protocol guarantees for a passive LP; CTA-mode invariants are subsumed.
- **INV-05 (closed action vocabulary)** — Static check combined with REQ-012; additionally assert the `Literal[...]` type cannot be extended by importers (`typing.get_args` runtime check).
- **REQ-019 (coverage indicator)** — Replay a fixed window; assert `CoverageData.window_blocks = end_block - start_block + 1`; `event_count = len(event_aligned_metrics)`; `age_of_last_event_seconds` consistency check.
- **REQ-020 (failure surfacing, F1 + F-B fix)** — Inject each failure class (mock MOD-001 to raise `EventStreamFetchError`, `ValidationError`; mock MOD-002 to raise `ValueError`); assert `SimulationResult.failure` is populated with the expected `failure_class` and `cause`; assert `event_aligned_metrics` reflects what was processed before the halt; assert halts at the correct boundary. For cache corruption: assert `CoverageData.cache_corruption_events` is populated; assert `FailureInfo is None` (run continues); assert `event_aligned_metrics` reflects the recovered stream. **Combined-failure test (F-B fix)**: mock MOD-001 to raise `EventStreamFetchError` whose `cache_corruption_events` field is non-empty (e.g., `[CacheCorruptionRecord(block_range=(100, 200), cause="sha256_mismatch")]`); assert that the wrapped `FailureInfo` carries the same `cache_corruption_events` list AND that `CoverageData.cache_corruption_events` carries the same list (dual-sink); assert `failure_class == "rpc_truncation"`; assert `event_aligned_metrics` reflects the partial fetch. This validates REQ-020(c) "MUST be surfaced" on the combined-failure path end-to-end.

# Blocking Unknowns and Implementation Handoff

- **Unknown (Blocking, cross-module)**: MOD-001 Event Stream Provider contract was previously draft and did not export the four fields required by this DESIGN: `cache_hit_count`, `avg_block_time_seconds`, `last_event_block_timestamp`, `cache_corruption_events`. MOD-003's `status: final` was previously BLOCKED on MOD-001 reopen to add these fields (F1 + F4). **CLOSED** — see Resolution status.
  **Why it matters**: REQ-N04, REQ-019, REQ-020(c) cannot be satisfied without these fields; `CoverageData` schema depends on them.
  **How to resolve**: reopen MOD-001 (via cross-layer coordination); add the four fields to MOD-001's `fetch_event_stream` return shape (a `Stats` parameter or a separate `get_window_stats(...)` accessor); MOD-003's `run_simulation` then consumes them. This requires user authorization.
  **Resolution status**: CLOSED — MOD-001 reopened (rev 4), all four fields exported, plus `EventStreamFetchError.cache_corruption_events` field added. MOD-001 status: final.

- **Unknown (F5, CLOSED via primary-source verification 2026-10-11)**: V4 Position.sol fee-on-decrease semantics — WebFetch on `https://raw.githubusercontent.com/Uniswap/v4-core/main/src/libraries/Position.sol` revealed that `Position.update()` returns `feesOwed0`/`feesOwed1` but does **NOT** transfer tokens on liquidity-decrease; a separate V4 `collect()` function handles the actual transfer. The original F5 design assumption (V4 auto-credits on decrease) is **incorrect as a description of V4 on-chain behavior**. The ledger's treatment of fees as realized at quit/partial_withdraw is therefore **reclassified as a Design Choice for backtest economic accounting** (independent of V4's actual on-chain `collect()` flow); see Correctness Constraints INV-04 paragraph. Implementation MUST NOT change this Design Choice without reopening this DESIGN.

- **Unknown (MOD-001 contract change, blocking)**: any contract change in MOD-001's DESIGN beyond the four added fields will trigger a MOD-003 reopen at Implementation handoff.

- **Unknown (Architecture §9 deferred, resolved here)**: CTA indicator interface shape (`Protocol` with `Tuple`-sliced history). If the user prefers a different interface shape, MOD-003 must be reopened.

- **Unknown (Architecture §10 deferred, resolved here)**: CTA action threshold representation. MOD-004 Dashboard input form MUST match these field names and types.

- **Implementation Handoff**:
  - Module path: `src/strategy_engine/`. Confirm against project convention before commit.
  - Public surface: `run_simulation(request: SimulationRequest) -> SimulationResult`, plus all the type definitions listed under Provided Public Contracts (Protocol included).
  - Tests: `tests/strategy_engine/` — `test_passive.py`, `test_cta_state_machine.py` (REQ-013 + INV-03 table test, 12 cases), `test_indicators.py` (REQ-010 plug-in), `test_capital_conservation.py` (INV-04 property test, Hypothesis, ≥1000 random events), `test_failure_surfacing.py` (REQ-020 + F1 + F4), `test_metric_alignment.py` (REQ-D01), `test_no_future_data.py` (INV-02 controlled fixture), `test_action_vocab.py` (REQ-012 + INV-05 static check), `test_deterministic_precision.py` (REQ-N01 cross-module pollution guard), `test_coverage.py` (REQ-019), `test_v4_fee_design_choice.py` (F5 — Implementation verifies the DESIGN's "Design Choice for backtest accounting" assumption by running a sanity fixture where fees_earned=0 produces zero principal/earnings movement; not a V4 on-chain verification, which was completed at module-design layer).
  - Evidence Implementation MUST produce: (1) capital-conservation property test pass log (≥1000 random events, INV-04 holds at every step); (2) cross-module pollution test pass log (REQ-N01); (3) CTA state-machine table test pass log (REQ-013 + INV-03, 12/12 cases); (4) indicator plug-in integration test pass log (REQ-010); (5) failure-surfacing trace log (REQ-020, all four failure classes + cache corruption surfacing via CoverageData); (6) V4 Position.sol primary-source verification artifact.
  - Trigger A applies (money / capital conservation / public contract / cross-module invariants): Implementation must pass Independent Reviewer (Mode A) before `status: final`.

# Resume Notes

- 2026-10-10: Initial draft created from SPEC-001 + ARCHITECTURE.md. Trigger A applies — Independent Review (Mode A) will be delegated before `status: final`.
- 2026-10-10: Independent Review (Mode A) executed. 10 findings received: F1 (Major, REQ-020(c) cache-corruption surfacing gap), F2 (Major, Indicator Protocol structural slicing), F3 (Major, default indicator_to_action_map unspecified), F4 (Major, MOD-001 contract gap for cache_hits / avg_block_time / last_event_timestamp / cache_corruption_events), F5 (Major, V4 fee-on-decrease accounting gap), F6 (Minor, set_range token-rebalance formula), F7 (Minor, partial_withdraw withdrawn_value formula + 1.0 aliasing), F8 (Minor, CTA out_of_range formula + asymmetry statement), F9 (Minor, passive entry_sqrt_price_x96 definition), F10 (Improvement, cta_action_counts no-op scope). All 10 fixes applied in this revision (see below).
- 2026-10-10: Fixes applied:
  - **F1**: `CoverageData.cache_corruption_events: List[CacheCorruptionRecord]` field added; cache corruption surfaces via `CoverageData` (not `FailureInfo`), preserving REQ-020(c) "other ranges MUST be usable". MOD-001 reopen required to populate this field (Blocking Unknown).
  - **F2**: `Indicator` Protocol signature changed to `evaluate(history: Tuple[SwapEvent, ...], current_index: int) -> List[Signal]`; dispatcher passes `tuple(swap_events[:current_index+1])` — immutable `Tuple` containing exactly the events at or before `current_index`, structurally preventing future-event access. INV-02 verification extended to assert no indicator accesses `history[current_index+1]`.
  - **F3**: Default `indicator_to_action_map` declared as empty (`Dict`); if indicators emit signals but no map supplied, dispatcher raises `CTASpecError("no_indicator_to_action_map_supplied")` — no silent business default.
  - **F4**: `CoverageData.cache_hit_count` field added; required MOD-001 exports enumerated (cache_hit_count, avg_block_time_seconds, last_event_block_timestamp, cache_corruption_events). MOD-001 reopen required (Blocking Unknown).
  - **F5**: INV-04 reworded as **principal conservation**: `free_cash + principal_value == initial_capital` at every event; fees tracked separately via `fees_value_in_c0` and credited to `free_cash` on liquidity-decreasing actions per V4 Position.sol `update()` semantics. Implementation must verify primary source (`Uniswap/v4-core/src/libraries/Position.sol`); Blocking Unknown until verified.
  - **F6**: `set_range` formula specified explicitly — rebalances tokens at current price via `amounts_at_tick`; ledger absorbs differential to preserve INV-04.
  - **F7**: `partial_withdraw` formula specified: `withdrawn_principal = principal_value * f`; `partial_withdraw_fraction == 1.0` rejected at CTASpec parse with `CTASpecError` (aliasing guard).
  - **F8**: CTA `out_of_range` formula explicit: `(tick < tick_lower) or (tick >= tick_upper)`; informational only — no auto-quit; CTA asymmetry with passive stated explicitly.
  - **F9**: Passive `entry_sqrt_price_x96` defined: `sqrt_price_x96` of the first event in the window at or after `PassiveSpec.entry_block`; `entry_block_out_of_window` raises `ValidationError`.
  - **F10**: `cta_action_counts` scope declared INCLUSIVE of no-ops; added separate `cta_realized_action_counts` (excluding `reason in {"position_open", "no_open_position", "threshold_not_breached"}`) for state-changing actions only.
- Architecture deferred items resolved here:
  - §9 CTA indicator plug-in interface shape (REQ-010): Python `Protocol` class with `evaluate(history: Tuple[SwapEvent, ...], current_index: int) -> List[Signal]`; `Signal = NamedTuple(name, direction, strength)`; `SwapEvent` projection with `(block_number, log_index, sqrt_price_x96)` only.
  - §10 CTA action threshold representation (REQ-012): typed `StopLossTakeProfitThreshold { threshold_fraction, direction }`, `partial_withdraw_fraction: Optional[Decimal]` ∈ (0, 1), `rebalance_only` has no threshold.
- INV-03 open commitment: `add_liquidity` while open is **rejected** (not `quit+add`). INV-03 permits either; MOD-003 commits to rejected for v1.
- **Blocking dependencies for `status: final`**:
  - MOD-001 reopen (F1 + F4): must add `cache_hit_count`, `avg_block_time_seconds`, `last_event_block_timestamp`, `cache_corruption_events` to its contract.
  - V4 Position.sol primary-source verification (F5): must confirm fee-on-decrease semantics.
- Mechanical completeness fix: ARCHITECTURE.md §2 row keyed by display name "Strategy Engine" was given canonical ID `MOD-003-strategy-engine` per SKILL.md §4 hard rule 4 (already applied during MOD-001 handoff; recorded here for traceability). Source row: ARCHITECTURE.md §2 line "Strategy Engine | Event-driven simulation loop...".
- Storage path: `docs/modules/MOD-003-strategy-engine/` (follows project convention `docs/<layer>/<id>/`, matches MOD-001 and MOD-002).
- 2026-10-10: Targeted Resolution Verification (Mode B) executed. 8 of 10 fixes verified resolved (F1, F2, F3, F6, F7, F8, F9, F10). F4 partially resolved (silent -1 fallback remained for `window_seconds_estimate` and `age_of_last_event_seconds`, diverging from the four-fields-required discipline). F5 partially resolved: literal Required Outcome met, but the invariant reword `free_cash + principal_value == initial_capital` is internally inconsistent (Major F-A) — `principal_value` is mark-to-market and changes at every event via IL, so the invariant cannot hold as written.
- 2026-10-10: Corrective fix for F-A + F-B + Improvements F-C/F-D/F-E/F-F:
  - **F-A (Major, INV-04 internal consistency)**: rewrote INV-04 to use `position_value_at_entry_price` (computed via MOD-002's `position_net_value(amounts, entry_sqrt_price_x96_snapshot)` — constant for the position's life) instead of mark-to-market `principal_value`. Mark-to-market remains the user-facing CTAMetrics / PassiveMetrics field; INV-04 verifies against the entry-price valuation. CTAPositionState extended with `entry_position_value_at_entry_price` (invariant field) + `entry_principal_value_at_current` (for stop_loss_take_profit comparison). Capital ledger updates for `add_liquidity` / `quit_liquidity` / `set_range` rewritten against `position_value_at_entry_price`. INV-04 property test rewritten against the entry-price invariant. Algebraic check: for an open position, both `free_cash` (after action) and `position_value_at_entry_price` (constant) change in inverse directions such that their sum remains `initial_capital`.
  - **F-B (Minor, F4 silent -1)**: removed silent -1 fallback for `window_seconds_estimate` and `age_of_last_event_seconds`; both now `CTASpecError("MOD_001_MISSING_FIELD: ...")` if MOD-001 does not export. Unifies with the four-fields-required discipline (F4).
  - **F-C (Improvement, partial map)**: clarified that `indicator_to_action_map` MAY be partial — signals whose names are not in the map are silently dropped (standard selective-mapping pattern). `CTASpecError` fires only on completely missing/empty map AND any indicator emits signals.
  - **F-D (Improvement, stop_loss_take_profit threshold formula)**: added explicit rationale for using `entry_total_value = entry_principal_value_at_current + entry_fees_value_in_c0` as the denominator (user's strategy P&L includes fees; threshold compares against realized entry value).
  - **F-E (Improvement, CTA out_of_range wording)**: clarified "The position remains open until a signal-driven or threshold-driven action fires."
  - **F-F (Improvement, F9 SPEC ambiguity)**: SPEC-001 REQ-D02 prose says "at the position's entry block" but is silent on the edge case where `entry_block` has no Swap event (e.g., block has only ModifyLiquidity). The DESIGN's fallback to "first event at-or-after entry_block" is a Module-Design interpretation; recorded for future Spec clarification (the current prose supports either reading).
- 2026-10-10: Additional Targeted Resolution Verification (Mode B, final permitted pass) executed. Algebra for F-A / F-B / F-C / F-D / F-E / F-F verified resolved (algebra preserved across all five CTA actions; F-A split-formulation `free_cash_principal + position_value_at_entry_price == initial_capital` algebraically correct). Two documentation-consistency issues surfaced:
  - **F1 (Major)**: Correctness constraints section (INV-04 paragraph) was NOT updated alongside the Capital ledger section in the prior corrective fix; the two sections contradicted each other (pre-F-A wording in the constraints section vs F-A split-formulation in the ledger section).
  - **F3 (Minor)**: F6 table formula (set_range row + formula block) used pre-F-A variables (`principal_value`, `price`); ambiguous after F-A split.
  - Per verification.md §6 loop bound, surfaced to user for authorization.
- 2026-10-10: User-authorized additional corrective fix (beyond verification loop bound, per explicit user authorization):
  - **F1**: Correctness constraints section rewritten to use the F-A split-formulation (`free_cash_principal + free_cash_earnings` split; `free_cash_principal + position_value_at_entry_price == initial_capital`); ledger update rules for `quit_liquidity` / `partial_withdraw` rewritten to credit `free_cash_principal` for principal returns and `free_cash_earnings` for realized fees; initial-state / per-event / post-action invariant claims corrected.
  - **F3**: `set_range` table row + formula block rewritten to use `position_value_at_entry_price` and `entry_sqrt_price_x96_snapshot` (NOT `price` / current price); `free_cash_principal` absorbs the differential; insufficient-cash guard retained.
  - Algebraic verification (post-fix): walk through each action symbolically; invariant holds. Algebra was already correct; documentation now matches the algebra.
- 2026-10-10: Handoff to Implementation. `DESIGN.md status: final`. Implementation must read `docs/modules/MOD-003-strategy-engine/DESIGN.md` only; chat history not required. Implementation Handoff obligations are listed in `# Blocking Unknowns and Implementation Handoff` of DESIGN.md (MOD-001 reopen for F1/F4 fields; V4 Position.sol primary-source verification for F5).
- 2026-10-11: Reopened per user authorization to absorb MOD-001 contract changes (F-B fix). MOD-001 reopen added the `FetchStats` field group AND extended `EventStreamFetchError` with `cache_corruption_events: List[CacheCorruptionRecord]`. MOD-003 updates applied (this revision):
  - **CoverageData.cache_corruption_events source expanded** to include both paths: success path (from `FetchStats.cache_corruption_events`) AND failure path (from `EventStreamFetchError.cache_corruption_events`).
  - **FailureInfo.cache_corruption_events optional field added** — populated only on the failure path (combined-failure mode).
  - **Failure surfacer extracts `e.cache_corruption_events`** from `EventStreamFetchError` and populates both sinks (`CoverageData.cache_corruption_events` and `FailureInfo.cache_corruption_events`) — the dual-sink pattern ensures REQ-020(c) "MUST be surfaced" obligation is honored end-to-end.
  - **Verification REQ-020 extended** with a combined-failure test: mock `EventStreamFetchError` with non-empty `cache_corruption_events`; assert both sinks carry the list.
  - **Blocking Unknown for MOD-001 dependency CLOSED** — MOD-001 status: final, all four required fields plus `EventStreamFetchError.cache_corruption_events` exported.
- Targeted Resolution Verification (Mode B) will be delegated next to confirm the F-B fix restores the cross-module REQ-020(c) end-to-end surfacing obligation without introducing new material defects.
