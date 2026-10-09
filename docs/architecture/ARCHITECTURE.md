# Architecture Baseline — Robinhood Chain UniswapV4 LP Backtest System

Adopted: 2026-10-09
Source Spec: `docs/specs/SPEC-001/SPEC.md` (status: archived)

## 1. System Context

The system is a backtester for UniswapV4 LP positions on Robinhood Chain (chain ID 4663), targeting the standard concentrated-liquidity model with multiple fee tiers. It supports two strategy modes — passive range LP and CTA signal-driven active LP — over the same reconstructed event stream, with a local Robinhood-styled web dashboard for input and visualization.

The Baseline adopts `SPEC-001` (status: archived, 2026-10-09) as its sole authoritative Spec.

## 2. Modules and Responsibilities

The baseline uses a 4-module structure chosen as the simplest that satisfies the 5 Spec capabilities.

| Module | One-line Responsibility | Related Requirements |
|---|---|---|
| **Ingestion** | Acquire V4 events from public Robinhood Chain RPC; reconstruct pool state per event; persist to local cache. | REQ-001, REQ-002, REQ-003, REQ-020(a)(c), REQ-N02, REQ-N03 |
| **LP Math** | Pure functions for CL conversions, fee math, capital / IL / value computation. | REQ-004, REQ-005, REQ-006 (compute parts), INV-04 |
| **Strategy Engine** | Event-driven simulation loop; passive strategy; CTA strategy with indicator framework and action dispatcher. | REQ-007, REQ-008, REQ-009, REQ-010, REQ-011, REQ-012, REQ-013, REQ-014, REQ-015, REQ-D01, REQ-D02, REQ-N01, REQ-N04, INV-02, INV-03, INV-05 |
| **Dashboard** | Local web UI for input form, strategy visualization, data-coverage indicator, failure surfacing. | REQ-016, REQ-017, REQ-018, REQ-019, REQ-020, REQ-N05 |

## 3. Capability / Requirement Ownership

| Spec Capability | Primary Owner Module |
|---|---|
| V4 event ingestion + pool-state reconstruction | Ingestion |
| LP math engine | LP Math |
| Passive range LP simulation | Strategy Engine (passive strategy) |
| CTA strategy engine | Strategy Engine (CTA strategy) |
| Local web dashboard | Dashboard |

Every important Requirement in `SPEC-001` is owned by exactly one module (REQ-001-003 / REQ-020(a)(c) / REQ-N02 / REQ-N03 → Ingestion; REQ-004-006 → LP Math; REQ-007-015 / REQ-D01-D02 / REQ-N01 / REQ-N04 → Strategy Engine; REQ-016-020 / REQ-N05 → Dashboard). No Requirement is orphaned.

## 4. Dependency Boundaries

Dependency DAG (acyclic):

```text
LP Math         (no dependencies on other modules)
Ingestion       (no dependencies on other modules)
Strategy Engine → LP Math, Ingestion
Dashboard       → Strategy Engine
```

Rules:

- **Allowed public dependencies**: each module may call the public contract of any module it depends on per the DAG above.
- **Forbidden dependencies**:
  - Dashboard MUST NOT call LP Math or Ingestion directly; it MUST go through Strategy Engine's public contract.
  - LP Math MUST NOT depend on Ingestion or Strategy Engine; LP Math MUST remain a set of pure functions.
  - Ingestion MUST NOT depend on Strategy Engine; event flow is unidirectional.
  - No circular dependencies are permitted.

Authoritative state owners (each piece of state has exactly one owner):

- Ingestion owns: raw cached event payloads (REQ-N02) and the reconstructed pool-state timeline (INV-01).
- Strategy Engine owns: per-position state during simulation (INV-03, INV-04).
- Dashboard owns: input form state, current visualization state.
- LP Math owns: no state (pure functions).

Critical shared semantics:

- The event stream produced by Ingestion is the canonical timeline (INV-01). Both passive and CTA strategies consume this single timeline.
- Simulation proceeds event-by-event (INV-02). Strategy Engine must never observe events from blocks greater than the current block.

## 5. Public Capabilities and Contract Ownership

Public contracts (specific APIs and schemas are Module Design's responsibility):

| Public Capability | Provider Owner | Known Consumers | Required Behavior | Failure Semantics | Contract Location |
|---|---|---|---|---|---|
| Event Stream Provider | Ingestion | Strategy Engine | Ordered sequence of `(event, post-state)` pairs for a pool within a window, fetched from cache or RPC with pagination across REQ-001 / REQ-003 limits | REQ-020(a)(c): failed range + cause surfaced; existing valid cache preserved | TBD by Module Design |
| LP Math Functions | LP Math | Strategy Engine | Pure functions: CL conversions between `(sqrtPriceX96, tick, liquidity)` and `(amount0, amount1)`, fee accrual between events, IL vs REQ-D02 reference price series, position net value | Numerical exceptions propagate; no silent failure | TBD by Module Design |
| Strategy Result Provider | Strategy Engine | Dashboard | Metric series for passive + CTA aligned by event index (REQ-D01), CTA action log, coverage indicator data (REQ-019) | REQ-020: failure class surfaced to Dashboard; computation halts on unrecoverable boundary | TBD by Module Design |
| Dashboard Input Form | Dashboard | — | Form fields per REQ-017; client-side validation; submission triggers a Strategy Engine run | REQ-020(b): invalid input rejected before computation; validation error surfaced | TBD by Module Design |

No contract currently exists at file-level; Module Design is responsible for the first concrete contract.

## 6. System Invariant Responsibilities

| Invariant | Integration Owner | Verification Path |
|---|---|---|
| INV-01 Single price stream | Architecture / Ingestion | End-to-end: both passive and CTA strategies consume the same canonical event stream from Ingestion; an integration test verifies event-by-event parity. |
| INV-02 No future-data leakage | Strategy Engine | End-to-end: simulation step for block N only sees events from blocks ≤ N; a controlled-fixture test with deliberately placed future data verifies. |
| INV-03 Single-position CTA + 6-action dispatch | Strategy Engine (CTA strategy) | CTA strategy unit test for per-action semantics (REQ-013) + INV-03 dispatch coverage; integration test against the spec's six actions. |
| INV-04 Capital conservation | LP Math + Strategy Engine | End-to-end: total capital invariant (free cash + position value at REQ-D02 reference) holds across all events for both modes. |
| INV-05 Closed action vocabulary in v1 | Strategy Engine (CTA dispatcher) | Static check: action set in CTA dispatch matches REQ-012; no additional actions permitted in v1.

## 7. Architecture Decisions

- **AD-1 (2026-10-09) — 4-module structure**. Chosen over finer-grained alternatives. The 5 Spec capabilities reduce cleanly to 4 cohesive modules; passive and CTA strategies are co-located in Strategy Engine because they share the event-driven simulation loop and decision cadence. Splitting strategies into separate modules would create an artificial boundary without a corresponding responsibility split.

- **AD-2 (2026-10-09) — Python tech stack inherited as user constraint** (per `INT-001#decisions`). Architecture does not pre-decide the dashboard framework; Module Design may choose within the Python ecosystem.

- **AD-3 (2026-10-09) — Cache key dimensions are fixed to `(pool_address, start_block, end_block)`** (REQ-003). The exact serialization format is Module Design's responsibility.

- **AD-4 (2026-10-09) — IL reference price = pool's own reconstructed swap-price series** (REQ-D02). No external oracle module exists in the Baseline; this is the smallest sufficient approach.

- **AD-5 (2026-10-09) — REQ-N01 deterministic-precision constant** is fixed by the math library / numerical format the Architecture / Module Design pair selects; recorded per session. Architecture defers the concrete library choice to Module Design.

## 8. Spec Baseline References

- `docs/specs/SPEC-001/SPEC.md` — status: archived, updated 2026-10-09. Sole authoritative Spec adopted by this Baseline.

## 9. Open Architecture Questions

None blocking. Deferred to Module Design:

- **Dashboard framework selection** (Streamlit vs. alternative within the Python ecosystem).
- **Event Stream Provider pagination semantics** — REQ-020(a) surface area vs. retry / resumability policy.
- **CTA indicator plug-in interface shape** (REQ-010) — concrete method signatures and types.
- **REQ-N01 deterministic-precision concrete choice** — math library / numerical format the Architecture / Module Design pair will adopt.
- **V4 contract-address provenance** — must be empirically verified by Implementation before use (recorded in `SPEC-001#unknowns-and-upstream-feedback`); this is an Implementation acceptance obligation, not an Architecture question.

## 10. Handoff to Module Design

Modules involved: Ingestion, LP Math, Strategy Engine, Dashboard.

Required reading for Module Design: this Baseline + `SPEC-001` (sole source Spec). No prior conversation context required.

For each module, Module Design receives:

- Its Responsibilities section (§2) and the relevant Requirements.
- Its allowed dependencies and forbidden dependencies (§4).
- The public capabilities it provides or consumes (§5) — Module Design must produce the concrete contracts.
- The System Invariants it must preserve (§6).

No Architecture decision is left unresolved at the spec / architecture layer. All deferred items in §9 are Module Design's responsibility.