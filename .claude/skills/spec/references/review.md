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

### 2.2 The six phases the Reviewer executes

1. **Authority Discovery** — locate and read each source Intent, related Spec, and verified-fact reference.
2. **Independent Derivation** — derive required system behavior, boundaries, invariants, failure modes, and acceptance obligations from the authoritative sources **before** reading the target Spec.
3. **Inspect Target** — read the target Spec and compare against the derivation. Look for missing items, not only inconsistencies among existing items.
4. **Risk-based Challenge** — for the actual risks of this Spec (money, data integrity, timing, contracts, security, recovery), propose counter-examples and failure scenarios.
5. **Fact Verification** — for each load-bearing factual claim, cite the source; prefer primary sources; mark `Unknown` when evidence is unavailable. Reuse `.claude/skills/intent/references/research.md` and `.claude/skills/spec/references/fact-verification.md`.
6. **Findings** — return structured findings per `.claude/agents/independent-reviewer.md` §3.

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

Each finding is owned by exactly one layer. The Reviewer names the owner; the Spec Skill records / surfaces it:

| Owner | When |
|---|---|
| Intent | User goal ambiguity, conflicting goals, missing user constraint, decision to revisit. |
| Spec | Missing / weak system behavior, missing acceptance, weak invariant, weak testability, internal Spec inconsistency. |
| Architecture | Module ownership, public contract, dependency direction, cross-module invariant responsibility. |
| Module Design / Contract | API / schema / algorithm design that doesn't yet have a Module to attach to. |
| Implementation | Code-level issue once you are at the Implementation stage. |
| Verification / Test | Empirical test not yet performed. |
| User | Genuine trade-off or preference that only the user can decide. |

**Cross-layer discipline:** if a Spec-level finding actually points to Architecture, route it as Architecture feedback. Do not ask Spec to redesign the module split.

### 2.6 Output format (Spec Skill presents this to the user)

The Reviewer returns its own structured Markdown report (see `.claude/agents/independent-reviewer.md` §3). The Spec Skill wraps that report and adds its own triage verdicts (see §2.7), not just the Reviewer's classifications:

```text
Independent Review: SPEC-NNN

Review Mode: Independent / Fresh Context / Read-only / No persistent memory

Authoritative Sources Read:
- INT-NNN: <one-line purpose>
- SPEC-XXX (related): <one-line purpose>

Review Scope:
- <in scope>
- <out of scope>

Findings:
(reproduced verbatim from the Reviewer's report)

Spec Skill Triage (independent judgment — see §2.7):
- F1 → Triage: <Accept | Reject | Request Evidence | Redirect to <layer> | Already Covered>
       Owner: <layer>; Resolution: <what this Skill recommends>
       Cross-layer: <yes/no — see .claude/references/cross-layer-coordination.md>
       Closure: <Review Executed>

Coverage:
- Confirmed coverage: <list>
- Missing or partial: <list>
- Unable to assess: <list>

Limitations:
- <e.g. empirical verification not performed, primary source X not fetched>

Closure Status:
- Review Executed: yes
- Authority Resolved: <no — pending owner decisions; partial — X resolved, Y pending; n/a>
- Implementation Verified: not claimed by this Skill

Overall:
- <Material issues identified | No material issues found | Unable to assess>
- <Explicit remaining uncertainty>
```

The Spec Skill **does not** silently rewrite the Reviewer's classifications. If this Skill disagrees with a finding, it says so explicitly and explains why.

### 2.7 Triage procedure

The Spec Skill performs an **independent** triage on each finding. The Reviewer's recommendation is one input; it is not the verdict.

For each finding, work through these questions in order:

1. **Is the finding actually valid?**
   - Re-read the evidence. Does it actually support the claim?
   - If the Reviewer misread the target, mark **Reject with evidence** and stop.

2. **Is the existing Spec already sufficient?**
   - Does an existing Requirement / acceptance criterion cover this?
   - Is the issue actually a verification or downstream design gap, not a Spec gap?
   - If yes → mark **Already Covered** (by Spec / by downstream guarantee) and stop. Record the existing reference.

3. **What is the highest necessary authority whose content must change?**
   - Apply `.claude/references/cross-layer-coordination.md` §4 (Minimum necessary escalation).
   - Do not default to Spec. Do not default to Intent.
   - If no authority change is needed, mark **Reject with evidence** (the issue is moot).

4. **Is this a New Requirement or an acceptance / clarification edit?**
   - Apply the **Requirement Sufficiency Gate** (see `.claude/agents/independent-reviewer.md` §2 Phase 3.5).
   - Only bucket 4 (`New Requirement Needed`) justifies a semantic Spec addition.
   - Buckets 1, 2, 5, 6 are not Spec edits.

5. **Is this an Owner Decision, not an authority decision?**
   - Default values, product trade-offs, magic numbers → **Owner Decision Required** → User / Product Owner.
   - Do not silently fill in a default; the Reviewer and the Spec Skill do not own the decision.

6. **Is the evidence sufficient?**
   - If the Reviewer cited `Unknown` or unverified facts, mark **Request Evidence** and stop.

7. **Does the issue have a common root cause with another finding?**
   - If yes, merge into a single triage row. Preserve the original finding IDs as verification targets.
   - Do not produce duplicate work.

#### 2.7.1 Triage verdict options

| Verdict | Meaning | When |
|---|---|---|
| **Accept** | The finding is valid; this Skill will modify Spec content. | After passing all 7 questions; only bucket 4 of the Sufficiency Gate. |
| **Accept with caveat** | Valid but the modification is bounded (e.g. acceptance wording only). | Bucket 2 or 3 of the Sufficiency Gate. |
| **Reject with evidence** | The finding is invalid or already covered. Cite the existing Requirement / acceptance / downstream guarantee. | Question 1, 2, or 3. |
| **Request Evidence** | The finding may be valid but the evidence is insufficient. State what evidence is needed. | Question 6. |
| **Redirect to <layer>** | The finding is valid but belongs to a different authority. Use the feedback contract in `.claude/references/cross-layer-coordination.md` §3. | Question 3. |
| **Already Covered** | The issue is real but covered by an existing Requirement or downstream guarantee. Cite it. | Question 2. |
| **Owner Decision Required** | The issue requires a user / product decision. Surface to the user. | Question 5. |

#### 2.7.2 What "Accept" produces

An Accept produces a **single** Spec change with:

- The Requirement ID (existing or new).
- The minimal wording change.
- The acceptance / verification language.
- The source citation (Intent item ID or existing Requirement).
- A new `# Resume Notes` entry: "Independent review on YYYY-MM-DD — finding F-N accepted — REQ-NNN modified/added on YYYY-MM-DD."

A triaged Accept never produces a Spec edit that encodes:

- A specific module, API, schema, or algorithm.
- A magic number without justification.
- A product default.

If the proposed change would encode any of the above, redirect to the correct layer (Architecture / Module Design / User) before applying.

#### 2.7.3 What "Redirect" produces

A Redirect uses the feedback contract from `.claude/references/cross-layer-coordination.md` §3.1. This Skill:

- Records the redirect in the target's `# Unknowns and Upstream Feedback`.
- Surfaces the redirect to the user with the Suggested Decision Authority and Required Decision.
- Does not apply the change itself if the redirect target is outside Spec's authority.

#### 2.7.4 Closure language discipline

After triage, the Skill records only the closure state it can honestly claim:

| Closure state | Who records it |
|---|---|
| **Review Executed** | This Skill, after the Reviewer returns. Always recorded. |
| **Authority Resolved** | The owning layer, after the authoritative content has been changed or formally rejected. **Not** recorded by the Spec Skill for findings redirected to other layers — those layers record their own Authority Resolved. |
| **Implementation Verified** | Verification (Test / runtime observation). Never recorded by the Spec Skill. |

Do not write `closed: yes` on a finding. Do not add a new lifecycle state. Use `# Resume Notes` and `# Unknowns and Upstream Feedback` for the language.

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
