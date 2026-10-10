---
module: MOD-002-lp-math
status: final
source_spec:
  - SPEC-001
source_architecture:
  - ARCHITECTURE.md §2 (Modules and Responsibilities)
  - ARCHITECTURE.md §4 (Dependency Boundaries)
  - ARCHITECTURE.md §5 (Public Capability: LP Math Functions)
  - ARCHITECTURE.md §6 (INV-04 Capital conservation)
created: 2026-10-10
updated: 2026-10-10
---

# Module Goal and Upstream Basis

Owns the pure-function math layer for concentrated-liquidity conversions, fee accrual, impermanent-loss computation, and position net-value computation, per Architecture AD-1 and AD-2 (Python tech stack). Satisfies SPEC-001 REQ-004 (CL conversions), REQ-005 (per-event immutability), REQ-006 (fees / IL / value per event), and participates in INV-04 (capital conservation). Provides the unique Provider contract `LP Math Functions` per ARCHITECTURE.md §5. No upstream dependency (leaf module); concretizes the REQ-N01 deterministic-precision constant.

# Provided Public Contracts

## LP Math Functions

A small, stable set of pure functions. No global mutable state. Every function is referentially transparent: same inputs always produce same outputs, regardless of call order, interleaving, or the state of the caller's `decimal.Context`.

### Type definitions (frozen dataclasses)

```python
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class PoolState:
    block_number: int           # uint64
    sqrt_price_x96: int         # uint160, as encoded in V4 Swap event data
    tick: int                   # int24
    liquidity: int              # uint128
    fee: Optional[int]          # uint24 in pips; defined only for Swap events (REQ-002)
```

All fields are immutable (`int`, `Optional[int]`, no mutable containers). The `frozen=True` decorator combined with all-immutable field types is the only configuration that satisfies REQ-005 at the language level. Type definitions are exported as part of the public contract.

### `sqrt_price_x96_to_price(sqrt_price_x96: int) -> Decimal`

- **Input**: `sqrt_price_x96` as encoded in V4 `Swap` event data (uint160).
- **Output**: human-readable price = (sqrtPriceX96 / 2^96)^2, expressed as `Decimal` in REQ-N01 precision (see "Deterministic precision" below).
- **Units**: currency1 per currency0. Matches Uniswap convention.

### `amounts_at_tick(sqrt_price_x96: int, tick_lower: int, tick_upper: int, liquidity: int) -> Tuple[Decimal, Decimal]`

- **Input**: pool state + position range + liquidity.
- **Output**: `(amount0, amount1)` for the position's CL holdings at the current tick, both `Decimal` in REQ-N01 precision.
- **Edge cases**: when current tick <= tick_lower, position holds only `currency0` (return `amount0 > 0, amount1 == 0`); when current tick >= tick_upper, position holds only `currency1`; when tick_lower == tick_upper (zero-width range, REQ-009 degenerate), function MUST return `(0, 0)` and the caller MUST treat the position as out-of-range.

### `fees_between(prev_state: PoolState, curr_state: PoolState, liquidity: int, fee_pips: int) -> Tuple[Decimal, Decimal]`

- **Input**: two consecutive pool states from the event stream, the position's liquidity, and the pool's fee tier **in pips** (V4 convention: 1 pip = 1/100 basis point; e.g., 3000 pips = 0.30%).
- **Output**: `(fee0, fee1)` accrued to the position across the interval, `Decimal` in REQ-N01 precision.
- **Failure**: zero liquidity raises `ValueError("zero_liquidity")`; `curr_state.block_number <= prev_state.block_number` raises `ValueError("non_monotonic_block")`; `fee_pips < 0` or `fee_pips > 2**24 - 1` raises `ValueError("invalid_fee_pips")`.

### `il_against_reference(entry_sqrt_price_x96: int, current_sqrt_price_x96: int, lower_sqrt_price_x96: int, upper_sqrt_price_x96: int) -> Decimal`

- **Input**: REQ-D02 reference prices encoded as `sqrt_price_x96` (caller converts via `sqrt_price_x96_to_price`). LP Math owns the in-range determination internally: `position_in_range = (lower_sqrt_price_x96 <= current_sqrt_price_x96 <= upper_sqrt_price_x96)`.
- **Output**: impermanent loss as a fraction of the HODL value (negative means loss, e.g., `-0.05` = 5% loss vs HODL).
- **Piecewise form** (SPEC-001 Acceptance — passive mode):
  - In-range: `IL = 2*sqrt(p) / (1+p) - 1` where `p = current_price / entry_price`.
  - Out-of-range below (current_sqrt_price_x96 < lower_sqrt_price_x96): LP holds only token0; `LP_value = amount0_at_current_sqrt_price` (via `amounts_at_tick`); `HODL_value = amount0_at_entry + amount1_at_entry * current_price`; `IL = LP_value / HODL_value - 1`.
  - Out-of-range above (current_sqrt_price_x96 > upper_sqrt_price_x96): symmetric (LP holds only token1).
- The caller MUST pass `entry_sqrt_price_x96` consistent with REQ-D02 (entry = reconstructed swap-price at position entry block); `current_sqrt_price_x96` = reconstructed swap-price at each subsequent event; `lower_sqrt_price_x96` / `upper_sqrt_price_x96` = position's `[tickLower, tickUpper]` encoded as `sqrt_price_x96`. LP Math does not silently accept contradictory inputs.

### `position_net_value(amount0: Decimal, amount1: Decimal, price: Decimal) -> Decimal`

- **Input**: current token holdings + the REQ-D02 reference price (currency1 per currency0).
- **Output**: total position value in `currency0` units = `amount0 + amount1 / price`. `Decimal` in REQ-N01 precision.

### Failure semantics (module-wide)

- Numerical exceptions (`Decimal.Inexact` in strict contexts, `Decimal.DivisionByZero`, overflow, NaN) propagate to the caller. No silent fallback to float.
- Invalid inputs (negative liquidity, non-monotonic blocks, tick_lower > tick_upper, `fee_pips < 0`, `fee_pips > 2**24 - 1`) raise `ValueError` with a stable message.
- This module DOES NOT swallow exceptions and DOES NOT log; logging is the caller's responsibility (Architecture §5 Failure Semantics — "numerical exceptions propagate; no silent failure").
- The module's `decimal.Context` is module-private; it does not mutate the global `decimal.getcontext()` and does not depend on the caller's global context. See "Deterministic precision" below.

### Deterministic precision (REQ-N01 concretization)

- Internal arithmetic uses Python `decimal.Decimal` with a module-private `decimal.Context(prec=100, rounding=decimal.ROUND_HALF_EVEN)`, accessed per invocation via `with decimal.localcontext(_CTX):` or via explicit `_CTX.create_decimal(...)` calls. The module NEVER calls `decimal.getcontext().prec = ...`; this guarantees no cross-module interference with other `Decimal` users in the same process (Strategy Engine bookkeeping, Dashboard formatting, stdlib helpers).
- All inputs from `int` (sqrtPriceX96, tick, liquidity) are converted via `Decimal(int_value)` (exact).
- The 100-digit precision is the **deterministic-precision constant for the session** (SPEC-001 REQ-N01). It is exported as `MOD_002_PRECISION_DIGITS = 100` for other modules to read. Changing this constant is a Module-Design decision, not an Implementation decision.
- **Why 100 digits, not 50?** The justification must hold for the actual intermediate magnitudes the CL formulas produce, not just the output magnitudes. Worst-case bound:
  - Inputs: `liquidity` ≤ uint128 (≈ 3.4e38, ~39 digits); `sqrt_price_x96` ∈ [1, 2^160] (≈ 1.46e48).
  - `amounts_at_tick` intermediate: `liquidity * (2^96 / sqrt_price_x96_a - 2^96 / sqrt_price_x96_b)`. The factor `2^96 / sqrt_price_x96` for `sqrt_price_x96 = 1` reaches `2^96 ≈ 7.9e28`. Multiplying by `liquidity` ≈ 3.4e38 yields an intermediate product up to ~2.7e67 (~68 significant digits).
  - Required precision for an intermediate of magnitude ~1e67 to retain <1 atomic-unit error at the output scale (uint256 amounts, ~1e77) is: 67 (intermediate magnitude) + ~7 (cancellation margin) + ~10 (output / atomic-unit margin) ≈ 84 digits minimum.
  - 100 digits leaves a ~16-digit margin that absorbs cumulative rounding across multiple events in the INV-04 property test.
- 50 digits is **insufficient** for the worst-case intermediate path on the money-load-bearing contract. The earlier draft's "50 digits comfortably exceeds V4's 18-decimal token precision" reasoning addressed output magnitudes only and is replaced by this intermediate-magnitude derivation.
- This module performs no `float` arithmetic. Float inputs raise `TypeError`.

# Consumed Public Contracts

None — leaf module (ARCHITECTURE.md §4).

# Internal Design and Key Decisions

- **Library**: Python standard library `decimal.Decimal`. No external math dependency (Architecture §9 defers the math library choice to Module Design; rationale for `Decimal` over `mpmath` / `gmpy2`: zero install footprint, REQ-N01's "deterministic-precision constant for the session" maps cleanly to a single `decimal.Context`, and 100 digits comfortably exceeds V4's worst-case intermediate magnitude with margin for cumulative rounding).
- **Context isolation**: the module owns a private `_CTX = decimal.Context(prec=100, rounding=decimal.ROUND_HALF_EVEN)` and uses `with decimal.localcontext(_CTX):` per public function. NEVER mutate `decimal.getcontext()`. This eliminates cross-module `Decimal` pollution (Strategy Engine, Dashboard, stdlib) and preserves the no-mutable-state contract.
- **File layout**: `src/lp_math/` with sub-modules `conversions.py`, `fees.py`, `il.py`, `value.py`, and `precision.py` (exports the context + constant + frozen dataclass). One file per concern; cross-imports only via the public surface listed above.
- **No mutable state**: every function is pure. The module-private `_CTX` is constructed once at import and never mutated.
- **V4 formulas**: derived from the Uniswap V4 whitepaper and `IPoolManager.sol` source (primary source). Implementation MUST cite the formula source for each function in its docstring. Verification strategy below includes cross-checks against an external reference V4 SDK.
- **REQ-005 enforcement**: encoded at the type level via `@dataclass(frozen=True)` with only immutable field types. See "Type definitions" above.
- **REQ-006(b) IL in-range determination**: owned by LP Math internally. The public contract accepts `sqrt_price_x96` bounds; the function computes `position_in_range` itself. Callers no longer pass a boolean flag, eliminating the silent-failure mode where a wrong flag is accepted without notice.

# Correctness Guarantees and Verification

Each observable check is derived from the cited Spec Requirement and does not rely on the module's own bookkeeping.

- **REQ-004** — CL conversions. Golden tests:
  - In-range case (current tick = midpoint of [tickLower, tickUpper]): compare against an external V4 SDK (`uv4-sdk` or the Python `web3` + manual decode) on three reference positions.
  - Below-range case (current tick < tickLower): assert `amount1 == 0` and `amount0` matches the analytic single-sided formula `liquidity * (1/sqrt(p_a) - 1/sqrt(p_b))`.
  - Above-range case (current tick > tickUpper): symmetric.
  - Zero-width range (tickLower == tickUpper): assert `(0, 0)` per REQ-009 degenerate case.
- **REQ-005** — Immutability. Type-level: `PoolState` is `@dataclass(frozen=True)` with only immutable field types; the type definition is exported as part of the contract. Runtime tests:
  - `__setattr__` on a `PoolState` instance raises `dataclasses.FrozenInstanceError`.
  - Hash of a `PoolState` before and after passing through `fees_between` matches.
  - Construct a `PoolState` and pass it through `fees_between`; assert the function output reflects the **pre-mutation** state under `object.__setattr__` bypass (defensive-copy contract for nested mutation; if implementation does not defensively copy, this is documented as a known limitation).
- **REQ-006(a)** — Fee accrual. Replay a fixed event sequence over a known position; assert `fees_between` deltas sum to a hand-rolled reference value within REQ-N01 precision.
- **REQ-006(b)** — IL. Closed-form reference for both branches:
  - In-range: `IL(p) = 2*sqrt(p)/(1+p) - 1` where `p = current_price / entry_price`. At `p=1`, `IL=0`. Monotonicity: `dIL/dp < 0` for `p > 1` (IL becomes more negative as price diverges).
  - Out-of-range below (current_sqrt_price_x96 < lower_sqrt_price_x96): LP holds only token0. `LP_value = amount0_at_current_sqrt_price` (constant; equals the in-range formula evaluated at `P = P_lower`: `L * (1/sqrt(P_lower) - 1/sqrt(P_upper))`). `HODL_value_at_current_price = amount0_at_entry + amount1_at_entry * current_price`. `IL = LP_value / HODL_value - 1`.
  - Out-of-range above (current_sqrt_price_x96 > upper_sqrt_price_x96): LP holds only token1. `LP_value = amount1_at_current_sqrt_price * current_price` (constant; equals `L * (sqrt(P_upper) - sqrt(P_lower)) * current_price`). `HODL_value_at_current_price = amount0_at_entry + amount1_at_entry * current_price`. `IL = LP_value / HODL_value - 1`.
  - Test fixtures (hand-computed below; written down BEFORE Implementation writes the function so a wrong expected value is caught immediately):
    - Fixt 1 (in-range, p = 1.1): encode `price` as `sqrt_price_x96 = isqrt(price * 2**192)` per V4 convention (NOT `2**96 * isqrt(price * 2**192)` — that overflows uint160).
      - `entry_sqrt_price_x96 = isqrt(1.0 * 2**192) = 2**96`
      - `lower_sqrt_price_x96 = isqrt(0.8 * 2**192)`
      - `upper_sqrt_price_x96 = isqrt(1.25 * 2**192)`
      - `current_sqrt_price_x96 = isqrt(1.1 * 2**192)`
      - Expected `IL = 2*sqrt(1.1)/(1+1.1) - 1 ≈ -0.001134430...` (Implementation computes the exact `Decimal` value to 100 digits).
    - Fixt 2 (out-of-range below, current_price = 0.5): use Fixt 1's entry state, L = 1 (units cancel in IL).
      - `amount0_at_entry = 1 * (1 - 1/sqrt(1.25)) ≈ 0.1055728090000841`
      - `amount1_at_entry = 1 * (1 - sqrt(0.8)) ≈ 0.1055728090000841`
      - LP at `current_sqrt_price_x96 = isqrt(0.5 * 2**192)`: holds only token0, `amount0 = 1 * (1/sqrt(0.8) - 1/sqrt(1.25)) ≈ 0.2236067977499791`, `amount1 = 0`
      - `LP_value (in c0) ≈ 0.2236067977499791`
      - `HODL_value (in c0) = 0.1055728090000841 + 0.1055728090000841 * 0.5 ≈ 0.158359213500126`
      - Expected `IL = (√5 - 1) / 3 ≈ 0.412022659...` (LP outperforms HODL when fully concentrated in the appreciated asset).
    - Fixt 3 (out-of-range above, current_price = 1.5): symmetric setup.
      - `amount0_at_entry ≈ 0.1055728090000841`, `amount1_at_entry ≈ 0.1055728090000841`
      - LP at `current_sqrt_price_x96 = isqrt(1.5 * 2**192)`: holds only token1, `amount1 = 1 * (sqrt(1.25) - sqrt(0.8)) ≈ 0.2236067977499791`, `amount0 = 0`
      - `LP_value (in c0) = 0 + 0.2236067977499791 * 1.5 ≈ 0.335410196624969`
      - `HODL_value (in c0) = 0.1055728090000841 + 0.1055728090000841 * 1.5 ≈ 0.263932022500210`
      - Expected `IL = (3√5 - 4) / 10 ≈ 0.270820393...`
- **REQ-006(c)** — Net value. Round-trip: `position_net_value(amounts_at_tick(...), price)` MUST equal the sum of `amount0 + amount1 / price` for several non-degenerate states (algebraic identity, exact within `Decimal`).
- **REQ-N01 deterministic precision**.
  - Cross-platform determinism: assert `Decimal` outputs are byte-identical across two runs on identical inputs.
  - **Cross-module pollution test** (regression guard for context-isolation): set `decimal.getcontext().prec = 28` BEFORE importing MOD-002; assert that calling every public function preserves the global context (`assert decimal.getcontext().prec == 28` after each call). This catches any future regression that switches back to `getcontext().prec = ...`.
  - **Float rejection** (behavior, not grep): for each public function, call with `float` inputs and assert `TypeError`. Replaces the source-text grep check.
  - **Precision-stress test**: random grid with `liquidity ∈ [1, 2**128 - 1]` and `sqrt_price_x96 ∈ [1, 2**160 - 1]`; compare `amounts_at_tick` output against an `mpmath` reference implementation at `mp.dps = 200`; assert relative error < 1e-50 across the grid. Catches F3's worst-case intermediate issue.

# Out-of-Module Verification (INV-04 cross-module)

INV-04 (capital conservation) is an integration invariant whose owner is "LP Math + Strategy Engine" per ARCHITECTURE.md §6. The property test belongs at the integration layer (MOD-003 Strategy Engine DESIGN or a dedicated integration test suite), not within MOD-002 alone. The test runner MUST:

- Use MOD-002's `position_net_value` and `fees_between` as a deterministic oracle for position value.
- Maintain its own independent cash ledger, NOT calling into any helper from MOD-002 for cash tracking.
- Verify the independent ledger's correctness separately (e.g., by cross-checking against a brute-force replay with an alternative cash tracker).

MOD-002's DESIGN supports this test by guaranteeing:

- Deterministic-precision `position_net_value` and `fees_between` outputs (REQ-N01).
- Pure-function semantics (no hidden state).
- Reproducible byte-identical outputs across runs.

The actual INV-04 property test is owned by the MOD-003 DESIGN (`docs/modules/MOD-003-strategy-engine/DESIGN.md`, status: final) and is **out of scope** for this DESIGN.md.

# Blocking Unknowns and Implementation Handoff

- **None blocking.** The deferred Architecture decision (REQ-N01 math library) is resolved here as `Decimal` with 100-digit context, isolated from the global default. This resolution is binding for Implementation; any change to the precision constant requires reopening this DESIGN.md, not a local code edit.

- **Implementation Handoff**:
  - Module path: `src/lp_math/`. Confirm against project convention before commit.
  - Public surface: the six functions listed under "Provided Public Contracts" plus the `PoolState` frozen dataclass, the `MOD_002_PRECISION_DIGITS = 100` constant, and the module-private `_CTX` setup helper.
  - Tests: `tests/lp_math/` — `test_conversions.py`, `test_fees.py`, `test_il.py` (with hand-computed fixtures), `test_value.py`, `test_precision.py` (determinism + cross-module pollution + float rejection + precision-stress), `test_fee_units.py` (F2 guard), `test_immutability.py` (frozen dataclass + nested-mutation contract).
  - Evidence Implementation MUST produce: (1) cross-module pollution test pass log; (2) precision-stress test pass log; (3) hand-computed IL fixture pass log; (4) float-rejection behavior test pass log; (5) fee-unit guard pass log.
  - Trigger A applies (money / capital conservation / public contract math): Implementation must pass the Independent Reviewer's Mode A check before `status: final`.

# Resume Notes

- 2026-10-10: Initial draft. Trigger A applies (assets, capital conservation, public contract math) — Independent Review (Mode A) will be delegated before `status: final`.
- 2026-10-10: Independent Review (Mode A) executed. 8 findings received: F1 (Major, Confirmed), F2 (Major, Confirmed), F3 (Major, Probable), F4 (Major, Probable), F5 (Minor, Probable), F6 (Minor, Confirmed), F7 (Improvement), F8 (Improvement). All 8 fixes applied in this revision:
  - **F1**: replaced `decimal.getcontext().prec = 50` with module-private `_CTX` + `localcontext` per call; added cross-module pollution test (regression guard for context-isolation).
  - **F2**: renamed parameter `fee_bps` → `fee_pips` with explicit "1 pip = 1/100 basis point" annotation; added fee-unit guard test.
  - **F3**: raised `MOD_002_PRECISION_DIGITS` from 50 to 100; added worst-case intermediate-magnitude derivation; added precision-stress test against `mpmath` reference.
  - **F4**: changed `il_against_reference` signature to receive `sqrt_price_x96` bounds instead of `position_in_range` flag; in-range determination now internal to LP Math.
  - **F5**: added closed-form IL formulas for both out-of-range branches (below / above) with hand-computed fixtures written down before implementation.
  - **F6**: exported `PoolState` as `@dataclass(frozen=True)` with all-immutable fields; added nested-mutation contract test.
  - **F7**: moved INV-04 property test out of MOD-002's correctness section into a dedicated "Out-of-Module Verification" section; explicitly assigned to MOD-003 / integration layer.
  - **F8**: replaced `grep "float("` static check with behavior test (`TypeError` on `float` inputs) per public function.
- 2026-10-10: Targeted Resolution Verification (Mode B) executed. 7 of 8 fixes verified resolved (F1, F2, F3, F4, F6, F7, F8). F5 partially resolved: closed-form IL formulas were correct, but Fixt 1 had a `sqrt_price_x96` encoding typo (`2**96 * isqrt(...)` overflows uint160 by `2**96`; correct encoding is `isqrt(price * 2**192)`) and a wrong expected IL value (`-0.002353` vs the correct `≈ -0.001134` for p=1.1); Fixt 2/3 lacked concrete numerical values.
- 2026-10-10: Corrective fix for F5 (defects 5a/5b/5c):
  - **5a**: Fixt 1 `sqrt_price_x96` encoding rewritten to `isqrt(price * 2**192)` (no spurious `2**96 *` prefix); out-of-range formulas clarified (below / above).
  - **5b**: Fixt 1 expected IL rewritten to `2*sqrt(1.1)/(1+1.1) - 1 ≈ -0.001134430...` (independent recomputation confirmed).
  - **5c**: Fixt 2 (out-of-range below, current_price=0.5) and Fixt 3 (out-of-range above, current_price=1.5) given full hand-computed numerical values for `amount0_at_entry`, `amount1_at_entry`, `LP_value`, `HODL_value`, and expected IL (`+0.412173913...` and `+0.270753512...` respectively). The positive IL is correct: LP outperforms HODL when fully concentrated in the appreciated asset after price exits range.
- 2026-10-10: Additional Targeted Resolution Verification (Mode B, scope = F5 corrective fix only) executed. Confirmed 5a (sqrt_price_x96 encoding) + 5b (Fixt 1 expected IL) resolved; Fixt 2 (`≈ 0.412173913`) and Fixt 3 (`≈ 0.270753512`) expected IL values flagged as arithmetic slips. Reviewer recommended stop per `verification.md` §6 loop bound; surfaced to user.
- 2026-10-10: Final F5 fix applied (user-authorized beyond the verification loop bound). Fixt 2 expected IL replaced with closed-form `(√5 - 1) / 3 ≈ 0.412022659...`; Fixt 3 expected IL replaced with closed-form `(3√5 - 4) / 10 ≈ 0.270820393...`. Self-verified algebraically from stated intermediates using `√1.25 = √5/2`, `√0.8 = 2/√5`. No additional Targeted Resolution Verification per loop bound. Module Design complete.
- 2026-10-10: Handoff to Implementation. `DESIGN.md status: final`. Implementation must read `docs/modules/MOD-002-lp-math/DESIGN.md` only; chat history not required. Implementation Handoff obligations are listed in `# Blocking Unknowns and Implementation Handoff` of DESIGN.md.
- Architectural deferred item closed here: REQ-N01 concrete math library / precision constant (Architecture §9). Resolution: `decimal.Decimal` with 100-digit context, isolated from global default, exported as `MOD_002_PRECISION_DIGITS = 100`. Implementation MUST NOT change without reopening this DESIGN.
- Mechanical completeness fix: ARCHITECTURE.md §2 row keyed by display name "LP Math" was given canonical ID `MOD-002-lp-math` per SKILL.md §4 hard rule 4. Source row: ARCHITECTURE.md §2 line "LP Math | Pure functions...".
- Storage path `docs/modules/MOD-002-lp-math/` follows project convention `docs/<layer>/<id>/` (matches `docs/specs/SPEC-001/`, `docs/intents/INT-001/`).
