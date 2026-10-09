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

Run a structured review on a Spec. By default this is executed as an **Independent Review** by the `independent-reviewer` subagent (`.claude/agents/independent-reviewer.md`) in a fresh context. The Spec Skill holds the report, the user decision, and the resolution path; the Reviewer only finds and reports.

### 2.0 Independent Review vs. Self-check

| Mode | When | Who executes | Output label |
|---|---|---|---|
| **Independent Review** (default) | User runs `/spec review <spec-id>`; or Spec is about to be archived and touches money / assets / security / core data correctness / public contracts. | A non-fork `independent-reviewer` subagent. Read-only. No persistent memory. | "Independent Review: SPEC-NNN" |
| **Self-check** | Trivial wording edits, pure typo fixes, internal-only quick passes. | The current Spec Skill in its own context. | "Self-check (not Independent Review): SPEC-NNN" |

Default to Independent Review. Self-check must never be presented as Independent Review.

### 2.1 Delegation message template

When delegating to the Independent Reviewer, the Spec Skill must construct a single neutral message containing the minimum fields below. **Do not** include author conclusions, pre-baked judgments, or hints about correctness.

```text
Review Type: Spec

Target:
docs/specs/SPEC-NNN/SPEC.md

Authoritative Sources:
- docs/intents/INT-NNN/INTENT.md
- <related SPEC-NNN/SPEC.md if any>
- <verified external fact file or URL if any>

Review Criteria:
.claude/skills/spec/references/review.md

Scope:
- Full Spec review
- (Optional) also include: <e.g. "focus on cross-Spec invariants with SPEC-002">

Method:
Independently derive expected requirements from the source Intent(s) and
related Specs before reading the target. Look for missing requirements,
not only inconsistencies among the requirements already listed.

Output:
Evidence-based findings only. Read-only. No file modifications.

Permissions:
Read-only: Read, Glob, Grep, WebFetch, WebSearch. Do not modify any file.
```

**Forbidden content in the delegation:**

- "I've verified all technical facts."
- "This Spec should have no major issues."
- "The architecture already confirmed this approach is correct."
- "Please prove this design satisfies the Requirements."
- Any other author conclusion presented as established fact.

Allowed: objective scope description, e.g. "This Spec concerns historical chain data, NAV calculation, and timing semantics for replay."

### 2.2 The phases the Reviewer executes

See `.claude/agents/independent-reviewer.md` §3 for the full procedure. The Reviewer's reasoning frame is **Derive → Locate**: derive what the authoritative sources require (Necessary Conditions, Design Choices, Unverified Assumptions), then locate where the target Spec misses, weakens, or contradicts a Necessary Condition. This Skill adds the independent triage in §2.7 (Resolve + Verify).

### 2.3 Checklist (criteria the Reviewer applies)

1. **Risk re-check** — re-run the intake risk categories against the current Spec content.
2. **Completeness** — every System Capability has at least one Requirement. Every cross-capability invariant is recorded in `# System Invariants and Dependencies`.
3. **Traceability** — every Requirement cites a source. No orphan Requirements. All cited Intent items still exist (verify by reading the Intent).
4. **Conflict** — no Requirement contradicts another Requirement in this Spec or a related Spec.
5. **Testability** — every Requirement can be observed, with clear pass/fail criteria. Numeric thresholds have measurement methods.
6. **Architecture boundary** — no Requirement names a specific module, API, schema, or storage choice. The `# Architecture Handoff` section lists open decisions but does not pre-decide them.
7. **Coverage cross-check** — for each Requirement, identify which Intent goal / constraint / decision it serves. Surface any that serve none.
8. **Source intent status** — if a source intent is still `active` (not `archived`), note that upstream changes may still occur.

### 2.4 Findings classification

Findings returned by the Reviewer are classified as exactly one of:

- **Confirmed Defect** — authoritative requirement / contract / fact proves a defect. Blocking / Major / Minor severity.
- **Probable Risk** — plausible risk, needs more evidence. Always includes `How to Verify`.
- **Missing Information** — required source absent; cannot conclude.
- **Improvement Suggestion** — valuable idea, **not** a violation of a confirmed requirement.

Suggestions are not defects. Do not promote or demote between these classes without new evidence.

### 2.5 Finding ownership and resolution

A finding is a problem statement, not yet a decision. The Reviewer may flag several affected layers; the **Suggested Decision Authority** is one input, not the verdict.

Each concrete decision has exactly one owner. A multi-layer finding produces multiple single-owner actions, not one shared Spec edit. Apply `cross-layer-coordination.md` §2 (Identify / Escalate / Resolve / Propagate) and §4 (Minimum necessary escalation) — do not redefine them here. The owner table below is a Spec-side reminder.

| Owner | When (Spec-side reminder) |
|---|---|
| Intent | User goal ambiguity, conflict, missing constraint, decision to revisit. |
| Spec | Missing / weak system behavior, missing acceptance, weak invariant, weak testability, internal Spec-only inconsistency. |
| Architecture | Module ownership, public contract, dependency direction, Baseline Applicability gap. |
| Module Design / Contract | API / schema / algorithm design, interface-field, default-value, magic-number choices — none of these are Spec Requirements. |
| Implementation | Code-level issue at the Implementation stage. |
| Verification | Empirical test not yet performed; observation gap. |
| User | Trade-off, default value, magic number — agent cannot decide alone. |

### 2.6 Output format (Spec Skill presents this to the user)

Reproduce the Reviewer's report verbatim, then append the Spec Skill's own triage block (see §2.7). Do not silently rewrite the Reviewer's classifications; if this Skill disagrees with a finding, say so explicitly and explain.

```text
Independent Review: SPEC-NNN
<Reviewer's report verbatim — see `.claude/agents/independent-reviewer.md` §4>

Spec Skill Triage (independent judgment — see §2.7):
- F1 → <verdict>; Owner: <layer>; Resolution: <one line>
       Cross-layer: <yes/no — see cross-layer-coordination.md §2>
       Closure: <state honestly claimable — see §2.7.6>

Coverage:
- Confirmed coverage: <list>
- Missing or partial: <list>
- Unable to assess: <list>

Limitations:
- <what this Skill did not verify>

Overall:
- <Material issues identified | No material issues found | Unable to assess>
- <Explicit remaining uncertainty>
```

Scale the triage block to the issue. Plain findings: one-line verdict with cite. Material, contested, or cross-layer findings: brief Derive / Locate / Resolve / Verify reasoning plus verdict.

### 2.7 Triage procedure

This Skill applies **Derive → Locate → Resolve → Verify** to each Reviewer finding. The Reviewer's classification, severity, proposed fix, and "Gap Character" hint are **inputs** — re-derive each from the authoritative sources. Verdicts are **conclusions of reasoning**, not menu picks. There is no required distribution across verdicts; a batch of N findings may legitimately become N Accepts, N Rejects, N Redirects, or any mix, as long as each verdict is supported below.

Scale to the issue:

- **Plain findings** — pick the verdict the reasoning supports and cite one line of evidence. No full Derive/Locate/Resolve/Verify trace required.
- **Material, complex, contested, or cross-layer findings** — walk the four steps and record brief reasoning. Reserved for cases that touch money, security, data correctness, public contracts, or any layer above/below Spec.

When a follow-up batch revisits similar findings, re-derive from sources, not from the previous triage.

#### 2.7.1 Derive — what does the source require?

State the necessary condition the Reviewer claims is violated or missing. Distinguish:

- **Necessary Condition** — without it, the confirmed goal cannot be correctly met. This is what Spec is obliged to encode.
- **Design Choice** — one of several valid ways to meet the goal. Belongs to Architecture / Module Design / Implementation; not a Spec Requirement.
- **Unverified Assumption** — premise without evidence; cannot be treated as fact.

If no Necessary Condition supports the claim → `Reject with evidence`. A Necessary Condition that turns out to be a Design Choice dressed up as a guarantee is also `Reject with evidence` — the agent has no authority to mandate a specific design.

#### 2.7.2 Locate — where is the gap?

Against the current authoritative content (this Spec + downstream guarantees + related Specs):

- A Necessary Condition is missing from Spec → likely Spec gap.
- An existing Requirement / acceptance criterion already satisfies this **semantically** → `Already Covered` (cite it).
- A Requirement exists but its acceptance / verification language is weak → acceptance-only edit (`Accept with caveat`).
- A Requirement is unambiguous only after wording clarification → clarification edit (`Accept with caveat`).
- The gap is module ownership / public contract / capability attribution → not Spec's job.
- The gap is actual code / runtime / empirical verification → not Spec's job.
- The gap is a trade-off / default value / magic number → `Owner Decision Required` (User).
- The evidence is incomplete or unverified → `Request Evidence` (state what would resolve).
- Same root cause as another finding → `Merge with F-N`.

If the gap touches several layers, locate each independent decision separately; do not bundle cross-layer fixes into one Spec edit.

#### 2.7.3 Resolve — minimum necessary change

**Authority-boundary check before Accept.** If the proposed fix encodes any of:

- A specific module, API, schema, algorithm, interface field, or storage choice;
- A magic number, threshold, or product default whose value is not (cited from) the source Intent;
- An Architecture, Module, Contract, or Verification decision made silently;
- Acceptance language that is not observable (no clear pass / fail, no measurement for thresholds);

the **fix is wrong even if the gap is real**. Reject the fix; resolve at the right authority.

**Owner layer.** Apply `cross-layer-coordination.md` §4 (Minimum necessary escalation). The fix lives at the highest necessary authority whose content must change. Cross-layer issues produce multiple single-owner actions, not one shared edit. A module-internal algorithm error is not a Spec edit; a User trade-off is not a Requirement.

#### 2.7.4 Verify — does the fix restore the guarantee?

Re-derive the Necessary Condition from the source and check the chosen fix restores it.

- Restored → proceed.
- Over-constrained (the fix now encodes a Design Choice as if it were a Necessary Condition) → reject the fix; choose a smaller or different fix.
- Weakens another Requirement, contract, or invariant → reject the fix.
- Introduces a new Unverified Assumption → `Request Evidence`.

A finding's validity and its proposed fix's validity are independent judgments. A valid finding can carry a bad fix; a "valid fix" without a real gap is meaningless work. If no authority change is needed (`Reject with evidence`) or the work belongs elsewhere (`Redirect`), the Verify step is satisfied by the routing decision.

#### 2.7.5 Verdicts

Each verdict is the named conclusion of Derive → Locate → Resolve → Verify. Pick the verdict whose reasoning check holds; cite the supporting evidence.

| Verdict | Reasoning check that must hold |
|---|---|
| **Accept** | Necessary Condition real; gap real in this Spec; fix passes boundary check; Verify restores the condition. |
| **Accept with caveat** | Gap real; edit bounded to acceptance wording or wording clarification; Verify restores. |
| **Reject with evidence** | No Necessary Condition supports the claim, OR the fix is wrong on boundary / Verify grounds. Cite what defeats the claim or the fix. |
| **Already Covered** | Derive holds; an existing Requirement or downstream guarantee already satisfies the gap semantically. Cite it. |
| **Redirect to <layer>** | Derive holds; the gap is in another authority that Spec cannot resolve while preserving confirmed upstream; the receiving authority is the right owner. |
| **Owner Decision Required** | The gap is a trade-off / default / magic number the agent cannot decide. Surface to the User; record as Pending. |
| **Request Evidence** | Plausible but evidence insufficient. State what would resolve. |
| **Merge with F-N** | Same root cause as another finding; triage once, preserve original F-IDs as verification targets. |

There is no "default to Accept" and no "default to Reject". A follow-up batch re-derives from sources.

#### 2.7.6 Cross-layer routing and closure language

**Routing.** Use the `cross-layer-coordination.md` §3 feedback contract: record the routing in the target's `# Unknowns and Upstream Feedback`, surface to the user with `Suggested Decision Authority` and `Required Decision`. Do not apply the change if the target is outside Spec's authority.

**Closure.** Record only the closure state honestly claimable. See `cross-layer-coordination.md` §5. Never write `closed: yes`; never introduce a new lifecycle state.

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
