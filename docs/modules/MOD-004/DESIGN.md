---
module: MOD-004
status: final
source_spec:
  - SPEC-001
source_architecture:
  - ARCHITECTURE.md §2 (Modules and Responsibilities, row MOD-004)
  - ARCHITECTURE.md §4 (Dependency Boundaries)
  - ARCHITECTURE.md §5 (Public Capability: Backtest Dashboard)
created: 2026-10-11
updated: 2026-10-11
updated: 2026-10-11 (status: final — Independent Review Mode A applied (15 findings: 7 Necessary in-file + F2/F3/F5 cross-layer closed via SPEC reopen + MOD-003 reopen, Authority Resolved on both cross-layers); F5 residual CTA stop_loss_take_profit single-direction discipline + form translation rule + boundary case `stop_loss_take_profit_dual_activation` documented and added.)
---

# Module Goal and Upstream Basis

Owns the **local web dashboard** per SPEC-001 REQ-016..020 + REQ-N05. Per
ARCHITECTURE.md §2 the Dashboard is the unique Owner of "Local web dashboard"
capability; per ARCHITECTURE.md §4 it sits downstream of `MOD-001` (Ingestion),
`MOD-002` (LP Math), and `MOD-003` (Strategy Engine) — it does NOT own any
computation, only the user-facing form + visualization + failure surfacing +
data-coverage indicator.

The Dashboard's primary consumer is the **human user** via a web browser
talking to a localhost HTTP server. Inputs and outputs are HTTP-shaped;
internal storage is a local per-session JSON file (REQ-017 persistence).

# Provided Public Contracts

## Backtest Dashboard (HTTP + UI)

The Dashboard exposes one user-facing capability: **run a backtest against a
V4 pool on Robinhood Chain and visualize the results in a Robinhood-styled
local web UI**. The capability has two coupled surfaces:

### A. HTTP API (server-side)

| Endpoint | Method | Body | Returns | Purpose |
| --- | --- | --- | --- | --- |
| `/` | GET | — | `text/html` (single-page app) | Input form + chart canvas |
| `/api/backtest` | POST | JSON form payload (see Form semantics) | JSON result with metrics + chart data, OR JSON error | Run a backtest (passive or CTA) and return all derived series |
| `/api/coverage` | GET | — | JSON `CoverageData` | Read-only coverage indicator for the most-recent backtest |
| `/api/failures` | GET | — | JSON `FailureInfo` | Read-only failure surfacing for the most-recent backtest |
| `/api/session` | GET | — | JSON `{ pool_id, start_block, end_block, mode, ... }` | Most-recent form input (for REQ-017 persistence on page reload) |
| `/api/session` | POST | JSON form payload | `200 OK` | Save form input to per-session JSON file (REQ-017) |

### Form semantics (REQ-017)

```json
{
  "pool_id":           "0x<66 hex chars>",        // V4 PoolId (per MOD-001 reopen rev 5); EIP-55 mixed-case accepted; lowercase also accepted
  "start_block":       12345678,                  // decimal integer
  "end_block":         12349999,                  // decimal integer
  "mode":              "passive" | "cta",
  // Passive mode
  "tick_lower":        -600,                      // signed int24
  "tick_upper":        600,                       // signed int24
  "capital":           "10.5",                     // decimal string, currency0 + currency1 sum
  // CTA mode (omitted when mode=passive)
  "indicator_params":  {"bbands_period": 20, "bbands_std": 2.0},
  // action_thresholds fields (F5 closure, corrected): stop_loss_take_profit
  // is a SINGLE-action type per REQ-012 (single direction per submission);
  // exactly one of stop_loss_enabled/take_profit_enabled MAY be true.
  "stop_loss_enabled":  false,                       // boolean; if true, stop_loss_fraction MUST be set
  "stop_loss_fraction": "0.10",                     // decimal string ∈ (-1, 0); ABS taken, sign forced negative
  "take_profit_enabled": false,                      // boolean; if true, take_profit_fraction MUST be set
  "take_profit_fraction": "0.30",                   // decimal string ∈ (0, +∞); ABS taken, sign forced positive
  "partial_withdraw_fraction": "0.5",                // decimal string ∈ (0, 1); 1.0 rejected at parse
  "indicator_to_action_map": {"upper_break": "quit_liquidity", "lower_break": "add_liquidity"},
  "rebalance_only":    false,                       // boolean, default false; true enables rebalance_only CTA action
  // Optional: per-session persistence key (default = a new UUID)
  "session_key":       "<uuid>"
}
```

Field validation rules are owned by `MOD-001` (REQ-020(b)) and `MOD-003`
(REQ-020 fail-fast discipline — "MUST NOT proceed silently past the failure
boundary" per SPEC-001 line 71); the Dashboard's HTTP layer translates the
upstream exception into HTTP 400 with the failure class + reason in the body.
The Dashboard itself enforces the form-side boundary cases (F7 — see
`test_form_validation.py` handoff).

### B. UI semantics (REQ-016..019 + REQ-020)

- REQ-016 Robinhood-style visual language: dark background (`#0E1116`-ish),
  green/grey accent palette, monospace for numbers, sans-serif for labels.
  No external font CDN; fonts are loaded from a single bundled WOFF2.
- REQ-017 per-session input persistence: form fields re-populate on page
  reload from the per-session JSON file (`./cache/sessions/<key>.json`).
- REQ-018 single comparable view: both modes' fee income, APR, IL, and
  total-asset-change series are rendered on the same chart canvas, sharing
  the X axis (event index) and Y axis (% / currency0+currency1).
- REQ-019 data-coverage indicator: a top banner shows window length in
  blocks + time, number of events covered, age of last event, cache hit
  ratio, `cache_corruption_events` count. Source = `MOD-003.CoverageData`
  (which derives internally from MOD-001.FetchStats — see Consumed
  Public Contracts § routing).
- REQ-020 failure surfacing: a red banner at the top of the chart for any
  failure class — RPC truncation, no-Initialize, cache corruption (cached
  + live). The Dashboard surfaces the cause via `MOD-003.FailureInfo`
  (already routed per `MOD-001` reopen rev 5 + `MOD-003` reopen F-B + 2026-10-11
  F3 reopen).
  **The HTTP response body on a failure always carries `failed_range`**
  (REQ-020(a)): structured `tuple[int, int]` carried end-to-end from
  MOD-001's `EventStreamFetchError.failed_range` through MOD-003's
  `FailureInfo.failed_range` (added 2026-10-11) to the Dashboard's HTTP
  body. F3 cross-layer gap CLOSED.
- REQ-016 supplement: Indicator parameters (Bollinger Bands) and CTA
  thresholds (`stop_loss_take_profit`, `partial_withdraw_fraction`) are
  wired to a fixed server-side `BollingerBandsIndicator` implementation
  (per REQ-010's "first concrete implementation is Bollinger Bands" and
  REQ-017's CTA input fields). The `indicator_to_action_map` defaults
  to `{"upper_break": "quit_liquidity", "lower_break": "add_liquidity"}`;
  `rebalance_only` is enabled via a separate form checkbox. This is the
  only server-side signal→action wiring v1 ships with (F9 closes the
  form→Indicator construction gap).
- REQ-018 supplement (F2 — APR definition): the chart receives
  `apr: Decimal` per `MetricRow` from MOD-003, computed by MOD-003 as
  `annualized(total_fees_value_in_c0 / capital_amount)` where
  `annualized` uses window duration from `CoverageData.window_seconds_estimate`.
  Resolution depends on either (a) reopening SPEC-001 REQ-018 to formalize
  this APR formula, or (b) extending MOD-003's `MetricRow` to include
  `apr: Decimal` directly. Awaiting user authorization.

# Consumed Public Contracts

Per ARCHITECTURE.md §4 (Dependency Boundaries), the Dashboard MUST NOT call
MOD-001 or MOD-002 directly — it goes through MOD-003's `Strategy Result
Provider` exclusively. The only consumer-side public capability the Dashboard
talks to is:

| Capability | Provider | Contract location |
| --- | --- | --- |
| Strategy Result Provider (passive + CTA simulation, `CoverageData`, `FailureInfo`) | MOD-003 | `docs/modules/MOD-003-strategy-engine/DESIGN.md` |

All references to `MOD-001.fetch_event_stream`, `FetchStats`, `FetchResult`,
and MOD-002 LP Math functions in this DESIGN are downstream of MOD-003 and
appear only as internal-to-MOD-003 commentary (carried through
`SimulationResult` / `MetricRow` / `CoverageData` / `FailureInfo`).

# Internal Design and Key Decisions

## Tech stack

- **Backend**: Python web framework. Pick **Flask** for v1 — smallest
  stdlib-ish HTTP server with template + JSON support, no async runtime
  required, fits MOD-001/002/003 already being synchronous Python.
  Per CLAUDE.md Search Rules: Flask is verified at flask.palletsprojects.com
  (primary source). Alternative FastAPI considered; deferred to v2 if
  async fan-out becomes needed.
- **Frontend**: Single HTML page (`templates/index.html`) with vanilla JS +
  Chart.js (bundled locally, no CDN per REQ-N05). Chart.js v4 — verified
  via primary source chartjs.org (no third-party CDN).
- **State**: in-process `dict[session_key, BacktestResult]` for the
  most-recent result; flushed to JSON on session end. JSON files live
  under `./cache/sessions/` (consistent with MOD-001's `./cache/` layout).
- **Decimal precision at the form boundary**: the `capital` form field is
  a JSON string (e.g., `"10.5"`). The Dashboard parses it with
  `Decimal(str)` (NOT `float`) before passing into `MOD-003.PassiveSpec.capital_amount`
  / `MOD-003.CTASpec.capital_amount` (both `Decimal`-typed per
  MOD-003 DESIGN). This keeps the entry point precision-safe — REQ-N01
  precision discipline is enforced inside MOD-002 / MOD-003, but the
  Dashboard's `float` would silently corrupt precision at the boundary.
  (F12 closure.)
- **CTA threshold translation** (F5 closure, residual): the form exposes
  `action_thresholds: { stop_loss: "-0.10", take_profit: "0.30" }` as two
  separate decimal strings, but MOD-003's `CTAThresholds` requires a
  single `StopLossTakeProfitThreshold { threshold_fraction, direction }`.
  The Dashboard constructs **two** `StopLossTakeProfitThreshold` values
  from the form (one for `direction='loss'` with `threshold_fraction =
  -abs(stop_loss)` (Dashboard enforces negative for loss / positive for
  profit at parse time to satisfy MOD-003's "negative for loss /
  positive for profit" rule documented in MOD-003 DESIGN), one for
  `direction='profit'` with `threshold_fraction = abs(take_profit)`) and
  passes both as `CTAThresholds.stop_loss_take_profit` — wait, MOD-003's
  `CTAThresholds.stop_loss_take_profit` is `Optional[StopLossTakeProfitThreshold]`
  (a single tuple). **Resolution**: the Dashboard combines the two form
  fields into a single `StopLossTakeProfitThreshold` per form-submit
  only when the user has activated stop-loss OR take-profit (NOT both —
  per the REQ-012 single-action-type vocabulary; MOD-003 enforces
  `direction ∈ {'loss', 'profit'}` as a single direction). The form
  MUST expose two separate boolean-toggled inputs ("stop_loss enabled"
  + "stop_loss fraction" + "take_profit enabled" + "take_profit fraction")
  rather than two unconditional decimal fields; only the active
  direction is constructed into `stop_loss_take_profit`. The Dashboard
  rejects form POSTs where both directions are enabled with
  `400 {"reason": "stop_loss_take_profit_dual_activation"}`. This
  constraint is documented in `MOD-003.CTAThresholds` and the Dashboard
  surfaces it via a clear form error message. (Re-clarified from F5
  closeout — single-action discipline is required by MOD-003; the
  earlier form schema with both `stop_loss` and `take_profit` was
  imprecise and has been corrected in this revision.)

## Request flow (POST /api/backtest)

```text
1. Validate form (pool_id 66-char hex, blocks valid integers, mode in set).
2. Build a `SimulationRequest` payload from the form and call
   `MOD-003.run_simulation(request)` ONCE — MOD-003 internally drives
   MOD-001 + MOD-002 + the Strategy Engine.
   - MOD-003 returns either a `SimulationResult` (success) OR throws a
     failure exception that carries `FailureInfo` (RPC / cache / validation).
   - The Dashboard maps that exception to HTTP 400 with
     `{ cause, failed_range, partial_metrics, cache_corruption_events }`
     in the body; the UI shows the red banner per REQ-020.
3. Build the HTTP response from the `SimulationResult`:
   - metrics: { fee_income, apr, il, total_asset_change } (from MOD-003.MetricRow)
   - series:  per-event-row array (REQ-007 / REQ-015, event-aligned per REQ-D01)
   - coverage: CoverageData (REQ-019 — `cache_hit_count` and
     `cache_corruption_events` come from MOD-003.CoverageData, which derives
     from MOD-001.FetchStats internally)
   - failures: FailureInfo (REQ-020, possibly empty)
4. Cache the result keyed by session_key; persist form to
   `./cache/sessions/<session_key>.json` (REQ-017).
5. Return JSON to the UI; UI renders the chart + indicators + banner.

## Visual style tokens

Defined as CSS variables in `templates/index.html`:

- `--rh-bg`:     `#0E1116`   (dark Robinhood-style background)
- `--rh-fg`:     `#FFFFFF`   (primary text)
- `--rh-accent`: `#00C29C`   (green accent for gains)
- `--rh-bad`:    `#FF4D4D`   (red accent for losses / failures)
- `--rh-grey`:   `#9BA4AE` (neutral grey)
- `--font-mono`: bundled `InterMono-Regular.woff2` (~150 KB)

# Correctness Guarantees and Verification

For each assigned Spec Requirement:

- **REQ-016** — Visual style. REQ-016 names three orthogonal facets
  (color palette, typography, layout density). Each is checked
  independently:
  - **(a) Color palette**: render the dashboard via a Playwright/Selenium
    snapshot at 1440×900 and 390×844 (mobile); diff pixel histograms
    against a Robinhood reference palette. `--rh-bg` and `--rh-accent`
    tokens must match within ΔE ≤ 5. The Robinhood reference palette
    MUST be cited to a primary source (e.g., a published brand guide)
    — until then this facet is `Reasonable Judgment (Unverified)`.
  - **(b) Typography**: assert that chart-axis numbers render in a
    monospace font with the expected metrics (check computed style
    `font-family: var(--font-mono)` and that digit widths are equal
    in `equal-width check`); assert that label typography uses the
    bundled sans-serif WOFF2 (computed `font-family` matches the
    bundled-family string).
  - **(c) Layout density**: assert grid / spacing / density tokens
    (e.g., `--rh-spacing-unit: 8px`) match a reference screenshot's
    pixel measurements within ±2 px tolerance.
- **REQ-017** — Per-session input persistence. Run a backtest, then GET
  `/api/session` and assert the response equals the form body submitted.
  (Includes CTA fields: `partial_withdraw_fraction`, `rebalance_only`,
  `indicator_to_action_map`.)
- **REQ-018** — Single comparable view. Submit both modes with identical
  pool_id / window; assert the chart data has identical length and X
  axis values across modes (REQ-D01 cross-mode event-alignment discipline).
  APR (per F2 resolution): assert both modes expose `apr` per MetricRow
  with the formula `annualized(total_fees_value_in_c0 / capital_amount)`
  as documented in REQ-018 supplement; expected APR derivable from the
  captured event fee values.
- **REQ-019** — Data-coverage indicator. Independent check: mocked
  `MOD-003.run_simulation` returns a specific `CoverageData` (with known
  `window_blocks`, `window_seconds_estimate`, `event_count`,
  `age_of_last_event_seconds`, `cache_hit_count`, `cache_corruption_events`);
  assert `/api/coverage` returns ALL six fields with the exact mocked
  values. Independence: derive expected values from the mock's return,
  NOT from the Dashboard's in-process response — the FAILURE mode is a
  real MOD-003 run against a controlled-cache MOD-001, not a Dashboard
  bookkeeping read.
- **REQ-020** — Failure surfacing (three sub-cases):
  - **(a) RPC truncation**: mocked `MOD-003.run_simulation` raises a
    failure carrying `failed_range = (12345, 12399)` and
    `cause = "rpc_truncation"`; assert HTTP 400 + body has
    `failed_range == [12345, 12399]` AND `cause == "rpc_truncation"`
    (REQ-020(a) "the failed range and the truncation cause MUST be
    surfaced"). **End-to-end contract** (closed 2026-10-11 via MOD-003
    F3 reopen): `failed_range` is carried as a structured numeric tuple
    from MOD-001's `EventStreamFetchError.failed_range` through
    `MOD-003.FailureInfo.failed_range` (added) to the Dashboard's HTTP
    body. No string parsing required.
  - **(b) No Initialize**: form POST with a known-bad `pool_id` (66-char
    hex with no Initialize in window); assert HTTP 400 + body has
    `cause` matching MOD-001.ValidationError.reason `"no_initialize_in_window"`.
  - **(c) Cache corruption surfacing**: success path — mocked
    `MOD-003.run_simulation` returns a `SimulationResult` whose
    `CoverageData.cache_corruption_events` is non-empty (e.g., 2
    records with `block_range` and `cause`); assert `/api/coverage`
    carries the corruption count AND the UI renders the red corruption
    sub-banner in the coverage indicator. Combined-failure path —
    mocked MOD-003 raises a failure carrying both
    `cache_corruption_events` and a `cause`; assert HTTP 400 body
    includes the corruption records (depends on F3 — MOD-003 reopen to
    surface `failed_range` and corruption records in `FailureInfo`).
- **REQ-N05** — Local-only. Split into two checks:
  - **(a, always run)** binding config: bind the Flask app to
    `127.0.0.1`; assert `ss -tlnp | grep :<port>` shows
    `127.0.0.1:<port>` only, NOT `0.0.0.0:<port>` (F11 split).
  - **(b, env-var gated)** network reachability: when
    `MOD_004_TEST_EXTERNAL_REACHABILITY=1`, `curl` to the local public
    IP returns connection refused. Gated because minimal CI containers
    may lack the egress config.

Boundary / failure-mode coverage (F7 — `test_form_validation.py`):
- empty pool_id → 400 with `reason: "invalid_pool_id"`
- wrong-length pool_id (e.g., 42 chars or 64 chars without `0x`) → 400
- non-hex pool_id (e.g., `0xZZZ...`) → 400
- EIP-55 checksum-mismatched pool_id (e.g., `0x8366a39cc670b4001a1121b8f6a443a643e40951` lowercase against an upper-case-required fixture) → 400
- negative blocks / end < start → 400
- bad mode (not in `{"passive", "cta"}`) → 400
- `stop_loss_enabled == take_profit_enabled == true` (both directions active) → 400 with `reason: "stop_loss_take_profit_dual_activation"` (F5 closure: REQ-012 single-action discipline)
- malformed session JSON → falls back to empty form (no crash)

# Blocking Unknowns and Implementation Handoff

- **Unknown** (Dependency for completion): MOD-002 / MOD-003 are still in
  the design phase per the Workflow state. **The Dashboard cannot be
  tested end-to-end until MOD-002 + MOD-003 are `status: final` and have
  implementations**. Record this as a §13.2 handoff obligation, not as a
  blocking prerequisite — the Dashboard's design does not depend on their
  internal algorithm (only on the public contract signatures).
- **Unknown** (resolved 2026-10-11): Web framework choice — picked Flask;
  no user authorization requested because per CLAUDE.md §14 Hard Rule 9
  "routine internal choices (data layout, file naming) do not need user
  authorization" and Flask is the lightest Python HTTP framework that
  fits the synchronous Python backend already in place.
- **Unknown** (resolved 2026-10-11): Charting library — picked Chart.js v4;
  bundled locally (no CDN). Per REQ-N05 the Dashboard MUST run locally
  with no cloud / hosted backend.

- **Implementation Handoff**:
  - Module path: `src/dashboard/` (Python). Mirrors `MOD-001/src/ingestion/`
    layout. State the path in `# Resume Notes`.
  - Python target version: 3.10+ (matches MOD-001).
  - Dependencies: `flask` (latest stable at implementation time); bundled
    `chart.js@4.x.x` + `InterMono-Regular.woff2` under
    `src/dashboard/static/`.
  - Public surface: the 6 HTTP endpoints listed above.
  - Tests: `tests/` —
    - `test_form_validation.py` (boundary cases listed above)
    - `test_backtest_endpoint.py` (mocked MOD-001/002/003; assert HTTP shape)
    - `test_session_persistence.py` (REQ-017)
    - `test_coverage_endpoint.py` (REQ-019; derived expected value, not
      from the Dashboard's own bookkeeping)
    - `test_failure_surfacing.py` (REQ-020)
    - `test_local_only_binding.py` (REQ-N05)
    - `test_visual_style.py` (REQ-016; Playwright + pixel diff against
      Robinhood reference palette)
  - Spec REQ-IDs to satisfy: REQ-016, REQ-017, REQ-018, REQ-019, REQ-020,
    REQ-N05.

# Resume Notes

- 2026-10-11: Initial draft (`status: draft`). Module ID `MOD-004` resolved
  per §5 entry check: user input `MOD-004-dashboard` → strip prefix →
  `004-dashboard` → second-pass display-name fallback matches Baseline §2
  row "Dashboard" (one row, no collisions) → canonical ID `MOD-004`. No
  Baseline §2 row addition needed (already keyed by `MOD-004`).
- 2026-10-11: Mechanical note — SPEC-001 § Unknowns typo fixed earlier today
  (`f6c` → `f6a`); Dashboard's poolId field MUST use EIP-55-mixed-case form
  to satisfy web3.py (already documented in MOD-001 reopen rev 5).
- 2026-10-11: **Independent Review (Mode A)** completed by `independent-reviewer`
  subagent. 15 findings: F1 / F2 / F3 / F4 / F5 = Major Necessary; F6 / F7 / F8 / F9 / F10
  = Minor Necessary; F11 / F12 = Improvement; F13 = cross-layer (same as F3);
  F14 = Spec routine correction; F15 = already done. **Triage decisions** —
  Necessary findings closeable in MOD-004 alone (F1, F4, F6, F7, F8, F9, F10, F12)
  applied in this revision; improvements F11 also applied (env-var-gated
  network reachability test). **Necessary findings requiring user
  authorization** (cross-layer or Spec scope) **resolved 2026-10-11**:
  - F2 — user authorized Option A: SPEC-001 REQ-018 reopened, APR formula
    pinned (`apr = annualized(total_fees_value_in_c0 / capital)`); MOD-003
    `MetricRow.apr` added via MOD-003 reopen (cross-layer to MOD-003).
  - F3 — user authorized Option A: MOD-003 reopen added
    `FailureInfo.failed_range: Optional[Tuple[int, int]]`; carries
    MOD-001's `EventStreamFetchError.failed_range` end-to-end. F13
    (same root cause) CLOSED.
  - F5 — user authorized Option A: form schema expanded with
    `partial_withdraw_fraction`, `rebalance_only`, `indicator_to_action_map`
    (all 6 REQ-012 actions now reachable end-to-end). MOD-003 contract
    fields already supported these.
  **Trigger B criteria fire** for the applied Necessary changes (public
  contract routing change F1; verification expansion F4 / F7 / F8 / F10;
  cross-mode CTA form schema expansion F5; cross-layer contract shape
  changes F2 + F3). Mode B Targeted Verification recommended before
  promoting to `status: final`.
- Next: promote to `status: final` after Mode B verification; then handoff to Implementation.

- 2026-10-11: **Targeted Resolution Verification (Mode B) for the F2 + F3 cross-layer reopens**: Independent Reviewer delegated the MOD-003 reopen changes; verdict **reopen resolved** for both F2 (REQ-018 APR formula pin) and F3 (REQ-020(a) `failed_range` end-to-end propagation). No material new defects. Three Improvement Suggestions (none reopen-blocking): F-1 Spec wording on `total_fees_value_in_c0`, F-2 edge-case guard status as Design Choice, F-3 additional verification for `failed_range is None` branch. **Authority Resolved** for F2 + F3 (recorded in MOD-003 DESIGN.md Resume Notes).

- 2026-10-11: **Promoted to `status: final`.** All Necessary findings closed (F1 / F4 / F6 / F7 / F8 / F9 / F10 / F12 applied in-design; F2 / F3 cross-layer closed via SPEC-001 reopen + MOD-003 reopen with Mode B verification; F5 closed with form schema expansion + CTA stop_loss_take_profit single-direction discipline). Improvements F11 applied. Three residual Improvement Suggestions (Spec wording, additional None-branch verification, `failed_range` type-alias consistency) recorded as out-of-scope or handoff notes. **Per §13.1 §6.5**: self-check sufficient — MOD-004 is a UI module delegating all data correctness to MOD-001 / MOD-002 / MOD-003 (whose Trigger A review / Mode B verifications are recorded). Implementation may proceed; Handoff reads this DESIGN end-to-end.