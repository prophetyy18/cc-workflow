# Requirements Methodology

The full rules for converting system capabilities into verifiable Requirements. Read on demand when deriving or reviewing Requirements.

## 1. Goal

Every Requirement in a `SPEC.md` must answer four questions:

1. **Observable** — what behavior can be observed?
2. **Correct** — under what conditions is it correct?
3. **Violation** — what constitutes a violation?
4. **Edge / Failure** — what boundary or failure mode must be verified separately (if any)?

If a Requirement cannot answer all four, it is not ready to be a Requirement.

## 2. Three Categories

### 2.1 Functional Requirements

What the system must do. Each one typically defines:

- **Preconditions** — what must be true before the behavior runs.
- **Trigger** — what initiates the behavior.
- **Valid input** — what inputs are accepted, and their semantic meaning.
- **Expected behavior** — what the system does.
- **State change** — what observable state changes.
- **Output / observable result** — what is produced.
- **Edge conditions** — boundary inputs that still need correct behavior.
- **Illegal input / failure** — what happens with bad input or system error.

### 2.2 Non-Functional Requirements

Only include NFRs that genuinely apply. Common categories:

- **Correctness** — result must match expected outcome within stated bounds.
- **Data integrity** — no silent loss, no unauthorized mutation.
- **Reproducibility** — same input + same conditions → same output.
- **Consistency** — different paths produce consistent results.
- **Security** — access control, audit, secret handling.
- **Performance** — latency, throughput, resource bounds.
- **Recoverability** — failure recovery, partial restart, replay.
- **Observability** — what the system exposes about its state.

Do not mechanically fill all categories. Pick the ones that meaningfully constrain the system. Numeric thresholds (e.g., "p99 < 200ms") need a measurement method.

### 2.3 Derived Requirements

Requirements derived from existing user goals to guarantee correctness. Mark as **Derived** with explicit reasoning.

Example: if the user requires historical strategy backtesting, then "no use of future data" is a derived requirement needed to make the backtest correct. The user's intent doesn't say "don't use future data" — but it's a necessary consequence of the backtest being valid.

Derived Requirements must:

- Cite the user goal they derive from.
- State the reasoning (why this is needed for correctness).
- Be flagged for user confirmation if they materially expand scope.

Do not disguise agent preferences as Derived Requirements.

## 3. Stable Item IDs

When a Requirement has real traceability value, assign `SPEC-NNN/REQ-NNN`:

- The first Requirement in a Spec is `REQ-001`. Increment by 1 per Spec.
- Subscripts allowed for natural sub-parts: `REQ-001.a`, `REQ-001.b`. Use only when one Requirement is naturally a multi-part test.
- IDs do NOT change on wording edits.
- A Requirement whose meaning materially changes should get a new ID; the old one is kept as a historical record.
- Cross-references from other documents use `SPEC-NNN/REQ-NNN`.

## 4. Source Attribution

Every Requirement must cite a source:

- `INT-001/G-01` — Intent goal item ID (preferred when available)
- `INT-001/C-01` — Intent constraint item ID
- `INT-001/D-01` — Intent decision item ID
- `INT-001#constraints-and-success-criteria` — file + section fallback when no item ID exists

Do not invent IDs that do not exist. If an Intent does not yet have item IDs, the Spec may introduce them in the Intent first, or use the file + section fallback.

## 5. What a Requirement is NOT

- A technology choice (no module names, no API names, no schemas).
- An implementation algorithm.
- A performance SLA without a measurement method.
- A test case (Requirements produce tests; they aren't the tests themselves).
- A user story phrased as a Requirement.

## 6. Anti-Patterns

- **Vague correctness** — "the system should be fast" → specify latency with measurement method.
- **Unbounded input** — "accept any user input" → specify valid ranges.
- **Co-mingled concerns** — one Requirement that mixes functional, performance, and security; split them.
- **Implicit dependencies** — Requires X but doesn't say so; cross-reference explicitly.
- **Magic thresholds** — numeric values without justification. If a number is needed, derive it from a user constraint or a measurable goal.

## 7. Edit Discipline

- Wording-only edits preserve the Requirement ID.
- Adding a new testable concern adds a new Requirement with a new ID.
- Removing a Requirement: do not delete; mark as `superseded by REQ-NNN` or `withdrawn on YYYY-MM-DD` with a one-line reason. This preserves history.
- Merging two Requirements into one: keep the more stable ID; mark the other as merged with a note.

These preserve traceability across revisions.

## 8. Cross-Capability Invariants

When capabilities are split across multiple Specs, certain correctness conditions only hold when the capabilities work together. These **system invariants** must be:

- Recorded in `# System Invariants and Dependencies` of every Spec that participates.
- Identified by asking: "if Spec A and Spec B are both correctly implemented individually, could the combined system still violate a user constraint?" If yes, an invariant is missing.

Common kinds:

- **No leakage** — e.g., "no future data used in any path that simulates a historical decision".
- **Unified accounting** — e.g., "all strategies use the same NAV calculation".
- **Deterministic composition** — e.g., "replay must produce the same state regardless of execution order".
- **Atomicity** — e.g., "a state change either fully completes or is fully rolled back".

Invariants are not tested in one Spec; they require an end-to-end verification at the system level.
