# Review and Coverage Methodology

The full rules for risk review (during intake), Spec review (`/spec review`), and coverage analysis (`/spec coverage`). Read on demand when running any of these.

## 1. Risk Review (during intake)

Run when starting a new Spec (`/spec <intent-id>` or `/spec new`).

### 1.1 Categories (apply when relevant)

- **Goal clarity** — is the user goal unambiguous enough to derive system behavior?
- **Constraint compatibility** — do constraints across multiple related Intents agree?
- **Fact verification** — are load-bearing facts verified? Reuse the verification standard from the intent skill's `research.md`.
- **Unprovable assumptions** — does the goal depend on something that cannot be verified?
- **Infeasible core requirement** — is any core requirement technically infeasible?
- **High-impact risk** — does the system touch assets, security, core data correctness, or other high-stakes areas?
- **Blocking Unknowns** — are there Unknowns that prevent the Spec from being written?

### 1.2 Blocking vs. Non-Blocking

- **Blocking** — the Unknown is required to write correct Requirements. Pause and resolve before continuing.
- **Non-Blocking** — the Unknown affects downstream design but not Requirement definition. Record in `# Unknowns and Upstream Feedback` and continue.

### 1.3 Routing per finding

- User goal ambiguity / contradiction → `/intent feedback <intent-id> <source>`.
- Constraint conflict across Intents → `/intent-reconcile <id1> <id2> [<id3> ...]`.
- Spec-level issue (incomplete system behavior, missing acceptance) → handle in this Spec.
- Architecture-level issue (module ownership, public contract) → record in `# Architecture Handoff` or `# Unknowns and Upstream Feedback`. Do NOT auto-feedback to Intent.
- Fact not yet verified → run verification or record as Unknown with a `How to resolve` step.

### 1.4 Output

A short list of findings. For each: severity (Blocking / Non-Blocking), category, proposed resolution.

Do not produce a fixed full-category report. Apply only what is relevant.

## 2. Spec Review (`/spec review <spec-id>`)

Run a structured review on a Spec.

### 2.1 Checklist

1. **Risk re-check** — re-run the intake risk categories against the current Spec content.
2. **Completeness** — every System Capability has at least one Requirement. Every cross-capability invariant is recorded in `# System Invariants and Dependencies`.
3. **Traceability** — every Requirement cites a source. No orphan Requirements. All cited Intent items still exist (verify by reading the Intent).
4. **Conflict** — no Requirement contradicts another Requirement in this Spec or a related Spec.
5. **Testability** — every Requirement can be observed, with clear pass/fail criteria. Numeric thresholds have measurement methods.
6. **Architecture boundary** — no Requirement names a specific module, API, schema, or storage choice. The `# Architecture Handoff` section lists open decisions but does not pre-decide them.
7. **Coverage cross-check** — for each Requirement, identify which Intent goal / constraint / decision it serves. Surface any that serve none.
8. **Source intent status** — if a source intent is still `active` (not `archived`), note that upstream changes may still occur.

### 2.2 Output

A structured report. No automatic edits — the user decides what to change.

```text
## Review Report: SPEC-NNN

### Risk re-check
- <finding>: <severity>; <resolution>

### Completeness
- Capabilities: <covered / partial / uncovered list>
- Invariants: <covered / partial / uncovered list>

### Traceability
- Orphan Requirements: <list or "none">
- Unresolved source references: <list or "none">

### Conflict
- <finding>: <between which Requirements>

### Testability
- Untestable: <list or "none">

### Architecture boundary
- Boundary violations: <list or "none">

### Coverage cross-check
- Requirements serving no Intent item: <list or "none">

### Source intent status
- <INT-NNN>: <active / archived>; <impact on this Spec>
```

## 3. Coverage Analysis (`/spec coverage <intent-id>`)

Check how well an Intent's important content is reflected in existing Specs.

### 3.1 Extract from the Intent

- **Goals** — from `# Clarified Intent`.
- **Hard constraints** — from `# Constraints and Success Criteria`.
- **Confirmed decisions** — from `# Decisions`.
- (Optionally) **item IDs** — if the Intent uses stable item IDs.

### 3.2 For each item, search

- All Specs that list this intent in `source_intents`.
- For each, read Requirements that cite this item (by item ID or by semantic match).

### 3.3 Assess semantic coverage

For each item, classify:

- **Covered** — at least one Requirement actually satisfies the item's content (semantically, not just by reference).
- **Partial** — Requirement addresses part of it; the gap is named.
- **Uncovered** — no Requirement addresses it.
- **Unknown** — Insufficient information to judge; needs clarification.

### 3.4 Output

A coverage table:

| Intent item | Status | Evidence | Gap (if any) |
|---|---|---|---|
| INT-001/G-01 | Covered | SPEC-002/REQ-001 | — |
| INT-001/C-02 | Partial | SPEC-002/REQ-005 | Missing failure-mode coverage |
| INT-001/D-03 | Uncovered | — | Not yet addressed by any Spec |

### 3.5 Important

- Coverage is about **Requirement definition**, not implementation.
- It does NOT prove code is correct.
- It does NOT prove tests pass.
- A reference to an item ID is necessary but not sufficient. The Requirement's actual content must satisfy the goal.

### 3.6 Large Intent

A large Intent does not need to be split into sub-Intents to achieve coverage. Coverage is a per-Intent check; if gaps exist, decide whether to create a new Spec, extend an existing Spec, or accept the gap as out of scope (deferred to Architecture, or not required at all).

## 4. Change Impact

When a Spec changes, the relevant Intents, other Specs, and downstream Architecture / contracts may be affected. Apply this discipline:

- Wording-only edits: no impact check needed.
- Adding a new Requirement: check that no existing Requirement contradicts it.
- Modifying an existing Requirement: check `source_intents` items are still relevant; if a source Intent has changed, re-check coverage.
- Removing a Requirement: surface in `# Resume Notes`; do not delete silently.
- Material change to a `source_intents` item: the user may want to add or modify a Requirement.

Do not run a full project impact scan on every change. Scale the check to the actual change.
