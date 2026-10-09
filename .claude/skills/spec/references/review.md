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

A finding is a **problem statement**, not yet a decision.

**Multi-layer findings are normal.** A Spec Review finding may surface an issue that lives in Spec, Architecture, Module Design, Implementation, Verification, User, or several of them at once. The Reviewer may tag multiple affected layers in `Potentially Affected Layers`. The Reviewer's `Suggested Decision Authority` is one input; it is not the verdict.

**Each concrete decision has exactly one owning layer.** Triage may surface that a problem affects several layers; the **resolution work** is then split into one decision per layer, each with its own owner. A Spec Requirement edit is owned by Spec; a contract-gap investigation is owned by Architecture; a default-value choice is owned by User. Do **not** bundle cross-layer edits into one Spec change to make the work look lighter. If the resolution is multi-layer, produce multiple rows in the triage output, not a single shared edit.

| Owner | When |
|---|---|
| Intent | User goal ambiguity, conflicting goals, missing user constraint, decision to revisit. |
| Spec | Missing / weak system behavior, missing acceptance, weak invariant, weak testability, internal Spec inconsistency that is not a downstream design issue. |
| Architecture | Module ownership, public contract, dependency direction, cross-module invariant responsibility, Baseline Applicability gap. |
| Module Design / Contract | API / schema / algorithm design that does not have a Module attached yet; interface-field, default-value, magic-number choices are not Spec Requirements. |
| Implementation | Code-level issue once you are at the Implementation stage. |
| Verification / Test | Empirical test not yet performed; observation gap. |
| User | Genuine trade-off, default value, magic number, product preference that only the user / product owner can decide. |

**Cross-layer discipline:** if a Spec-level finding actually points to Architecture, route it as Architecture feedback; do not ask Spec to redesign the module split. Conversely, do **not** push an Architecture / Module / User decision into Spec just because the Review surfaced it during a Spec Review. The "exactly one owner" rule applies to **each concrete action**, not to the finding's full resolution.

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

The Spec Skill performs an **independent** triage on each finding. The Reviewer's recommendation is one input. **Triage verdict does not equal Reviewer verdict.** The Reviewer's classification (Confirmed Defect / Probable Risk / Missing Information / Improvement Suggestion), Severity, Sufficiency Bucket, and Proposed Resolution may all be wrong. The Owning Skill re-derives each from the authoritative sources. There is **no required distribution** across verdicts — a batch of N findings may legitimately become N Accepts, N Rejects, N Redirects, or any mix, as long as each verdict is supported below.

For each finding, walk the questions in order. Stop at the first verdict you can defend with evidence.

1. **Re-derive the evidence.** Re-read the cited evidence. Does it actually support the claim, or did the Reviewer confuse a related-but-different Requirement, misread a section, or extrapolate beyond the source? If the evidence does not support the finding → **Reject with evidence** and stop.

2. **Re-classify the finding's type.** Independently check whether the Reviewer's classification is right.
   - Is there an authoritative Requirement, contract, or fact that proves a defect? If no, downgrade to **Probable Risk** or **Improvement Suggestion**.
   - Is the issue actually **Missing Information** because the source Intent or related Spec is silent or ambiguous?
   - Is the issue an **Improvement Suggestion** the Reviewer mistakenly promoted to Confirmed Defect?
   Promotion / demotion between these classes requires new evidence; do not do it casually.

3. **Re-derive the Severity.** Replace the Reviewer's Blocking / Major / Minor / Informational with your own, derived from the actual impact on user goals, system invariants, money / assets / data correctness, and downstream blast radius. A Reviewer's severity is a guess; the triage severity is the one that goes into `# Unknowns and Upstream Feedback`.

4. **Is the existing Spec already sufficient?** Does an existing Requirement / acceptance criterion cover this, **semantically** (not just by reference)? Is the issue actually a verification gap, downstream design gap, or acceptance wording weakness? If yes → **Already Covered** (cite the existing REQ, contract, or downstream guarantee) and stop.

5. **Does the proposed fix introduce new problems?** Read the suggested Possible Resolution and ask:
   - Does it encode a specific module, API, schema, algorithm, interface field, magic number, or product default that Spec is forbidden from owning? If yes, the **fix is wrong** even if the finding is valid; this is an automatic **Reject with evidence** or **Redirect**, depending on what the actual problem is.
   - Does it move work from Spec to Architecture / Module Design / Verification without justification?
   - Would it weaken a different Requirement, contract, or invariant?
   - Does it require a user / product decision the agent cannot make alone?
   A finding's validity and its proposed fix's validity are independent judgments. A valid finding can still carry a bad fix.

6. **What is the highest necessary authority whose content must change?** Apply `.claude/references/cross-layer-coordination.md` §4 (Minimum necessary escalation). Do not default to Spec. Do not default to Intent. If the resolution affects multiple layers, plan multiple single-owner decisions (§2.5). If no authority change is needed → **Reject with evidence** (the issue is moot).

7. **Apply the Requirement Sufficiency Gate.** (See `.claude/agents/independent-reviewer.md` §2 Phase 3.5.) Reclassify the Reviewer's bucket — it may be wrong.
   - Only bucket 4 (`New Requirement Needed`) justifies a semantic Spec addition. Justify why none of the other five apply.
   - Bucket 1 (existing Requirement sufficient) → no Spec edit.
   - Bucket 2 (acceptance needs strengthening) → **Accept with caveat**, edit acceptance only.
   - Bucket 3 (wording clarification) → **Accept with caveat**.
   - Bucket 5 (Owner Decision) → route to User; do not edit Spec.
   - Bucket 6 (Downstream Design / Verification) → **Redirect** to the right layer.

8. **Is this an Owner Decision, not an authority decision?** Default values, product trade-offs, magic numbers, UI defaults, "should we..." trade-offs → **Owner Decision Required** → User / Product Owner. Do not silently fill in a default; the Reviewer and the Spec Skill do not own the decision.

9. **Is the evidence sufficient?** If the Reviewer cited `Unknown` or unverified facts → **Request Evidence**; state what evidence would resolve it. Do not promote to Confirmed Defect on incomplete evidence.

10. **Does the issue share a root cause with another finding?** If yes, merge into a single triage row. Preserve the original finding IDs as verification targets. Do not produce duplicate work.

**Discipline:** there is no "default to Accept" and there is no "default to Reject." Each finding gets its own evidence-based verdict. If the same Reviewer returns a follow-up batch with similar findings, triage is repeated from the sources, not from the previous triage.

**Cross-layer propagation in triage:** a finding's resolution may legitimately produce multiple single-owner actions (e.g. add acceptance language in Spec **and** open a Module Design question). Record those as separate actions with separate owners under the same triage row. Do not bundle them into one Spec edit.

#### 2.7.1 Triage verdict options

Each verdict is this Skill's own conclusion, not a copy of the Reviewer's. The Reviewer's classification, severity, bucket, and proposed fix are inputs to triage, not the verdict. There is **no required distribution** across verdicts — do not pre-decide how many Accepts or Rejects a batch should contain. Apply only what the questions support.

| Verdict | Meaning | Re-classifies the Reviewer? | When |
|---|---|---|---|
| **Accept** | The finding is valid; this Skill will modify Spec content as a real semantic addition. | Yes; confirms Reviewer's classification, bucket = 4. | After all prior questions pass; only Sufficiency Gate bucket 4. |
| **Accept with caveat** | Valid but the modification is bounded (acceptance wording only, clarification only). | Yes; re-buckets to 2 or 3. | Sufficiency Gate bucket 2 or 3. |
| **Reject with evidence** | The finding's claim is invalid, mis-evidenced, the proposed fix is wrong, or no authority change is needed. Cite what defeats the claim or why the fix is wrong. | Yes; downgrades severity or rejects the fix. | Questions 1, 2, 3, 5, or 6. |
| **Request Evidence** | The finding may be valid but evidence is insufficient. State what evidence would resolve it. | Implicitly downgrades to Probable Risk. | Question 9. |
| **Redirect to <layer>** | The finding (or its proposed fix) belongs to another authority. One concrete owner per action. Use the feedback contract in `.claude/references/cross-layer-coordination.md` §3. | Yes; redirects owner. | Question 6 (and possibly 5). |
| **Already Covered** | The issue is real but covered by an existing Requirement or downstream guarantee. Cite it. | Yes; soft-rejects the proposed edit. | Question 4. |
| **Owner Decision Required** | The issue requires a user / product decision. Surface to the user; record as Pending until the user answers. | Yes; routes to User. | Question 8. |
| **Merge with F-N** | Same root cause as another finding; triage once, capture IDs as verification targets. | Combines effects. | Question 10. |

A batch of N findings may legitimately produce N Accepts, N Rejects, N Redirects, or any mix. The user's prompt explicitly allows this; do not pad verdicts for variety, and do not stretch to Accept just to look cooperative.

#### 2.7.2 What "Accept" produces

An Accept produces a **single** Spec change with:

- The Requirement ID (existing or new).
- The minimal wording change.
- The acceptance / verification language.
- The source citation (Intent item ID or existing Requirement).
- A new `# Resume Notes` entry: "Independent review on YYYY-MM-DD — finding F-N accepted — REQ-NNN modified/added on YYYY-MM-DD."

Before recording the Accept, the Skill re-checks the proposed change against Spec's authority boundaries:

- No new Requirement encodes a specific module, API, schema, algorithm, interface field, or storage choice.
- No new Requirement encodes a magic number, threshold, or product default without explicit user-side justification. If the source Intent supplies the value, cite it. If not, the change is a User decision — downgrade to **Owner Decision Required** instead of Accept.
- No new Requirement silently fixes what should be an Architecture, Module Design, Contract, or Verification decision.
- The Acceptance wording is observable: a test or run can confirm pass / fail; numeric thresholds have measurement methods; internal Spec state is not asserted as Acceptance.

If any of these checks fail, the Accept is **downgraded** to one of:

- **Accept with caveat** — keep the edit but trim it to acceptance language only.
- **Reject with evidence** — the finding's fix is wrong; record what is wrong with the fix.
- **Redirect to <layer>** — the resolution is owned by Architecture / Module / Verification / User.

The proposed fix is not the verdict. The triage question 5 ("Does the proposed fix introduce new problems?") is the gate.

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
