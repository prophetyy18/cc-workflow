---
description: Independent verification triggers, delegation, evidence standard, and loop bounding shared by all Skills that invoke the Independent Reviewer.
---

# Independent Verification Reference

Shared, lightweight rules for how the current Skill uses the Independent
Reviewer subagent (`.claude/agents/independent-reviewer.md`) to close the
verification loop. Load this file when:

- The current Skill is about to delegate an Independent Review or a
  Targeted Resolution Verification.
- The current Skill is triaging a Reviewer's report and deciding whether
  further verification is needed.

This file does not redefine the Reviewer's reasoning frame, hard rules,
or output format — those live in the Reviewer definition itself.

## 0. Related References

- Reviewer reasoning frame, hard rules, output format:
  `.claude/agents/independent-reviewer.md`.
- Review Triage (Derive → Locate → Resolve → Validate):
  `.claude/skills/spec/references/review.md` §2.7.
- Closure semantics (`Review Executed` / `Authority Resolved` /
  `Implementation Verified`):
  `.claude/references/cross-layer-coordination.md` §5.
- Per-Skill review invocation:
  `.claude/skills/spec/SKILL.md` §14;
  `.claude/skills/architecture/SKILL.md` §7, §8.

## 1. Two Review Purposes, One Reviewer

A single `independent-reviewer` subagent supports two purposes. The
current Skill declares the purpose via the `Review Mode` field in the
delegation message.

### Mode A — Independent Review

Default purpose. Fresh-context second pass over an authoritative
artifact (Intent, Spec, Architecture, Module Design, Implementation).
Scope is the whole target; the Reviewer derives conditions from
authoritative sources and locates gaps, weaknesses, and contradictions
across the full artifact.

### Mode B — Targeted Resolution Verification

Focused purpose. After the current Skill has applied an authorized fix,
verify whether the original problem was actually resolved. Scope is the
change itself and its necessary ripple, NOT a fresh full review of the
artifact.

### What is shared, what differs

The Reviewer's tools (`Read` / `Glob` / `Grep` / `WebFetch` /
`WebSearch`), fresh-context discipline, non-fork execution, and
read-only constraint are identical in both modes. The differences:

- **Mode A** — full scope, Derive → Locate across the entire target.
- **Mode B** — scope is the diff and its ripple. The Reviewer first
  re-derives the correct outcome or Necessary Condition for the change
  independently (not from the Main Agent's Triage), then checks the
  modified target against it.

The Reviewer output format is the same in both modes. The `Scope` line
and the closure flavor (`Review Executed` vs `Targeted Verification
Executed`) let downstream readers tell which mode produced the report.

## 2. Delegation Handoff

Every call to the Reviewer must provide, in plain prose:

- `Review Type` — `Intent` | `Spec` | `Architecture` | `Module Design` | `Implementation`.
- `Review Mode` — `Independent Review` (default) | `Targeted Resolution Verification` (only when Triggers B/C apply).
- `Target` — exact file path(s) or artifact identifier.
- `Authoritative Sources` — paths the target was supposed to satisfy.
- `Basis` — current source item/contract versions or exact snapshots,
  unresolved prerequisites, and evidence methods/limits. Give facts,
  not the author's assertion that the prerequisites are closed.
- `Review Criteria` — exact path and only the sections applicable to the
  target. Do not load unrelated domain checks to make a small review look
  comprehensive.
- `Scope` — what is in / out. For Mode B, the specific change being
  verified (diff hunk, REQ-ID, Section).
- `Method` — "Independently derive expected requirements / outcome
  before evaluating."
- `Output` — "Evidence-based findings only."
- `Permissions` — "Read-only. Do not modify any file."

For Mode B, also include:

- `Original issue and evidence` — the finding that triggered the fix.
- `Authoritative basis for correct outcome` — what the fix must satisfy.
- `Independent re-derivation expected` — explicit request that the
  Reviewer re-derive the correct outcome / Necessary Condition before
  evaluating the modified target.

Forbidden in delegation (both modes):

- Author conclusions: "this Spec looks correct", "I've verified all facts."
- Pre-baked judgments about correctness.
- "The previous fix is sound — please confirm."
- "Please prove the design satisfies the Requirements."
- Anything that would let the Main Agent's own Triage result substitute
  for the Reviewer's re-derivation.

## 3. Triggers — When the Current Skill Auto-Runs the Reviewer

The current Skill invokes the Reviewer during normal execution. It does
not require the user to type `/review` for every important change.

### Trigger A — Important Deliverable

The current Skill is about to hand off or finalize an authoritative
artifact that touches:

- Money, assets, financial calculations.
- Security, permission, or access boundaries.
- Core data correctness (state reconstruction, replay, NAV, idempotency,
  atomicity).
- Public contracts, module boundaries, cross-module invariants, or
  dependency direction.
- Mathematics / quantitative bounds that load-bear on system behavior.
- A multi-step user path whose ordering or initial availability is
  necessary to complete the core goal, even when each screen or
  component is individually low risk.

Run Independent Review (Mode A) unless a sufficient fresh-context review
has already been performed and its evidence is still applicable.

### Trigger B — Material Resolution

The current Skill has applied an authorized fix that materially changes:

- A Requirement, invariant, or acceptance condition.
- A module boundary, public contract, or dependency direction.
- An authorization scope, constraint, or confirmed decision.
- A load-bearing formula, calculation, or numerical bound.

Before claiming the underlying issue is `Authority Resolved`, run
Targeted Resolution Verification (Mode B). The fix was proposed via the
Skill's own Triage; the Reviewer must independently verify it rather
than accept the proposal at face value.

### Trigger C — Significant New Risk

During the current Skill's execution, a new risk emerges that was not
visible to the previous review: a previously unstated assumption, a
previously hidden upstream constraint, a math error, or an acceptance
criterion whose expected result is incorrect.

Choose Mode A or Mode B based on whether a full review or focused check
is the right response. Trivial wording, formatting, or low-risk local
edits do not trigger automatic review.

### What does NOT trigger automatic review

- Pure wording or formatting edits that do not change Requirement
  semantics.
- Local refactors inside a single Requirement that preserve observable
  behavior.
- White-space, link-fix, or example-illustration changes.

For these, the current Skill's own Self-check (`spec/references/review.md`
§2.0) is sufficient. Self-check must never be presented as Independent
Review.

## 4. Verification Principles

For each material claim the Reviewer inspects, apply at least one of
these methods. Different claim kinds demand different methods; cover the
ones relevant to the artifact under review.

### 4.1 Requirements

Re-derive the Necessary Condition from upstream sources. Check whether
the Requirement is sufficient, correct, and free of unauthorized scope
expansion. A Necessary Condition cannot be silently weakened; a Design
Choice cannot be silently promoted to a Necessary Condition.

### 4.2 Mathematics

When a load-bearing claim involves formulas, units, or quantitative
bounds:

- Re-derive from definitions.
- Check dimensional consistency.
- Test boundary conditions and special cases.
- Construct or reason about counterexamples that would falsify the claim.
- For a code execution path, the Main Agent may need to run a minimal
  numerical check (the Reviewer cannot execute code by design).

A claim of the form `X == Y` must be supported by derivation, code, or
a verified external source — not by analogy or pattern. Numbers
without sources are Unverified.

**Numerical expectations** in test fixtures, expected outputs, asserted
values, or hand-computed intermediates are a special case of `X == Y`:

- The Reviewer that asserts a numeric expectation is correct must
  re-derive it from primary sources (formula + arithmetic) **or
  independently recompute it with a separate tool** (mpmath,
  sympy, an algebraic identity, a closed-form with verified
  roots). "Independent" means a **separate derivation route** —
  not a re-run of the same arithmetic, and not "another model
  confirms the author's value". Calling a library that uses
  the same formula the author used does not constitute
  independent recomputation; the library would agree with
  the same wrong input.
- Author-self-verified algebra without independent recomputation
  is `Reasonable Judgment (Unverified)`, not `Verified`. Using
  a wrong self-verified numeric in a fixture for several
  iterations until the loop bound gives out is exactly the
  failure mode this principle prevents.
- **Who does the recomputation.** The Reviewer Subagent is
  read-only — it cannot run Python, mpmath, or sympy. When
  numerical verification requires execution, the *Authoring
  Skill* (the one proposing the design or the change) runs
  it as part of producing the verification evidence. The
  Authoring Skill's allowed-tools must include the necessary
  execution tool (e.g. `Bash(python3*)` for `decimal` /
  `mpmath` / `sympy` experiments). Independent Reviewer
  verifies the *claim* ("the agent re-derived the expected
  value via mpmath with input X using a closed-form for p=1.1
  whose roots are 1.0 and 1.1/1.0; the value matches"), not
  by re-running the code itself.
- When independent recomputation is impossible (no symbolic
  library, no closed form derivable), the Finding is
  `Reasonable Judgment (Unverified)`, and the Main Agent must
  surface the Unknown — not paper over it with another fix
  iteration.

### 4.3 External / Protocol Facts

Claims about external systems, protocols, APIs, libraries, or standards
must be supported by a primary source (official docs, RFC, library
source) or recorded as Unknown. Secondary sources are leads only.
Reuse the standard in `.claude/skills/spec/references/fact-verification.md`.

Also check the **coverage** of the cited evidence, not only its
authenticity: a claim of absence or completeness is bounded by the
range its evidence actually searched
(`.claude/skills/spec/references/fact-verification.md` §2.1). And
cross-check the target's load-bearing facts against the project's other
recorded facts — a contradiction between two records is
a finding to report, not a question to settle by preferring the newer
or more convenient document.

### 4.4 Acceptance Criteria

When verifying a Requirement's acceptance, the Reviewer must check:

- The criterion is observable, with a clear pass / fail signal.
- The expected result in the criterion matches the Requirement.
- A wrong implementation could still pass (construct or reason about it).
- A correct implementation could still fail (construct or reason about
  it, e.g., off-by-one, timezone drift, monotonic-time assumption).
- The criterion is self-consistent — not silently dependent on the
  implementation under test (e.g., "the metric this test asserts" being
  the same metric the implementation computes).

A passing test is not proof that its expected result is correct. The
Reviewer's job is to find where the criterion's claim is wrong or
ambiguous — not to validate that the test framework ran.

### 4.5 Architecture and Contracts

When the artifact is module ownership, public contracts, dependency
boundaries, or cross-module invariants, the Reviewer must:

- Verify the design actually satisfies its upstream Requirements.
- Verify responsibility, dependency, and contract semantics are
  consistent.
- Verify cross-module invariants survive decomposition (no module-local
  tests cover system-level guarantees alone).
- Verify the Required Behavior, Failure Semantics, and Timing / State
  Semantics of the contract match authoritative sources.

**Related-consistency check** (cross-cutting; applicable to
*every* layer's verification, not just Architecture):

When a fix is verified on a specific test case, that single
test passing is *not* evidence of contract compliance. The
Reviewer (or the Authoring Skill at the gate) must also
reconcile the fix against:

- The public contract's claims that the fix's implementation
  touches (parameter shape, return shape, coercion posture,
  failure-mode narrowing). A `quantize` the contract did not
  authorize, a default value the contract did not document, a
  reordered argument — any of these is a contract conflict
  even when the originally-found test passes.
- The acceptance conditions for the affected Requirement.
  Does the implementation still satisfy each one?
- The downstream consumer's expectations, when the consumer's
  contract location is known. A change that satisfies the
  Producer's REQ but breaks the Consumer's call shape is a
  regression.
- The internal design rationale. If the rationale was "use
  Decimal throughout" and the implementation coerces to two
  decimals, the rationale is contradicted.

This is the same discipline `cross-layer-coordination.md` §2.5
applies to Provider reopen / Consumer follow — the verification
is the matching discipline on the Implementation side. It is
not a project-wide audit; it covers only the area changed by
the current fix.

### 4.6 Implementation

When the artifact is code, tests, or runtime behavior, the Reviewer
must check actual code paths, test results, or empirical observations.
A passing test suite is necessary but not sufficient:

- Confirm the test expectations themselves (§4.4).
- Confirm the empirical observation actually matches what the
  Requirement mandates.
- If the Reviewer cannot run the relevant runtime or test, mark
  `Limitation: empirical verification not performed`; do not promote
  `Implementation Verified`.

**End-to-end user-journey check** (anchor to
`cross-layer-coordination.md` §8). For a claim that a user goal with a
sequence is complete (UI flow, API call sequence, CLI commands, data
pipeline), acceptance must include a run from the real starting state
covering every step. A scoped module handoff instead checks the real
boundaries it owns and records the remaining integration path and owner.
The run is classified per §4.7
(real / offline replay / mock / not-run). If the real run cannot
execute, the gate does not close on the basis of "every
component / unit test passed"; name the missing pre-condition,
the test that would have run, and the gap class per §4.8 (config
/ cred / real protocol uninvestigated / impl matches contract
but no runtime evidence). A skipped real end-to-end test is a
real condition to surface — not a green checkmark, and not
"`Implementation Verified`" for end-to-end correctness.

The Reviewer is read-only and does not actually run the user's
sequence itself; the Reviewer checks that the artifact preserves
the user sequence and that the Authoring Skill produced the
classification evidence. The actual end-to-end run is the
Implementation / Verification layer's job, executed against the
real starting state.

### 4.7 Real Acceptance Reporting

For any test that targets an external dependency (network, chain,
data source, database, third-party SDK), the result report must
classify the **actual call path and data source**, not the test
name. The categories:

- **Real integration** — the test exercised the real external
  dependency in real time with real auth / data, the call path
  went outside the process boundary, and the assertions checked
  the live response.
- **Offline replay** — the test ran real code on a captured or
  pre-recorded response (a fixture file, a stored snapshot). The
  code path is real, but the data is from an earlier interaction.
  Useful; does not prove current network / auth / schema
  compatibility.
- **Mock / stub / manual-input** — the test replaced at least one
  external boundary with synthetic data (an in-process mock, a
  hand-typed JSON, a stubbed method that returns canned bytes,
  or the test was written by reading documentation rather than
  capturing live behavior). Mocks and stubs are valid for
  boundary / fault / schema-shape tests, and the test of a
  fault-recovery path can also be mock-based *if* the mock
  exercises the real fault-recovery code; what mock-based tests
  cannot prove is **the live compatibility / current network /
  auth / schema of the dependency** — that requires real
  integration. Boundary and fault-recovery are not "the parts
  that don't matter" — they are core behavior the mock is
  covering, and the report must say so. **Not** real-integration
  evidence on the data-source axis.
- **Not run / skipped / failed** — the test file exists or the
  assertion code was written but the test did not run, was
  skipped, or failed; record what was *not* verified rather than
  substituting "should work later".

A test calling a "real SDK" but mocking its inputs and outputs
entirely is `mock / stub / manual-input` on the data-source axis.
A test replaying a real captured response is `offline replay`,
even if the SDK call path is real. Classification is by what
actually happened at the boundary, not by the test name.

For each test targeting an external boundary, the result report
records, at minimum, the **target boundary / environment /
data source / execution result / coverage scope / unverified
parts**. A passing result is necessary, not sufficient: the
report must say what was *checked* against the live response, not
just that a call succeeded.

For an interactive user sequence, also record the **interaction
boundary**: real browser or client actions, automated browser
actions, direct service requests, or code inspection. A live
service response proves only the service steps exercised; it does
not prove that a user can reach them through the product UI.
Start with the actual initial page or state, then record each
input, response, visible success or failure, and next available
action. State which transitions were not exercised. A fixture
that begins after a prerequisite action cannot prove that the
prerequisite is reachable.

### 4.8 Real by default

Test planning identifies the real boundaries the task must exercise.
Mocks can test boundary shape, fault handling and schema round-trips;
report their scope without claiming they exercised a live integration.

When the real dependency is not currently accessible:

- Name the specific test that was not run.
- State what is missing: connection address, real object
  identifier, time window, dependency version, network access,
  credential, paid-tier permission, write-side-effect
  authorization, or other.
- Self-investigate first: public docs, the project's existing
  configuration, captured-but-stale fixtures, sandbox endpoints,
  read-only mirrors. Only ask the user for what is genuinely
  out of reach.
- Tell the user exactly what to provide and where the work
  resumes once provided.
- Sensitive credentials: local config / secret management. Do
  not paste credentials into chat / log.
- Real tests with side effects (write, on-chain transaction,
  paid API call) require explicit authorization before they run.
  Prefer read-only paths that can satisfy the same acceptance
  criterion.

Skipping a real test because conditions are unavailable is
allowed; that skip must be reported. Calling a "real test"
accepted because all tests passed when real tests did not run is
**not** permitted.

When required real acceptance for a claimed scope has not been performed,
the Main Agent does **not** announce that scope closed. A module handoff
requires real evidence for its required public and available integration
boundaries; it does not require unrelated unfinished modules to complete the
whole user journey. Report module code/contract handoff and system-path
acceptance as separate claims. The user goal remains open until the required
sequence runs from the real starting state with visible success and failure
behavior. For any missing real check, record its precondition, the test that
would have run, owner and return point in `# Resume Notes` (or equivalent).
Do not relabel an unverified module boundary as a Consumer follow-up or a
mock-only result as live evidence to close that module handoff.

This rule gates each claim at its observed boundary. A Module Design may
become `final` when its contracts are complete and the real-run obligation
is explicitly handed to Implementation; `final` alone is not real-run
evidence. After an
upstream change, classify old evidence against the changed path
before reusing it, and rerun only the affected boundaries.

Three gap classes — config / credential / execution pre-condition
(1), real protocol / OAuth / response schema uninvestigated (2),
implementation matches known contract but no runtime evidence (3)
— are distinct:

- (1) is the lightest: surface the missing config, ask the user
  for what's out of reach, save state. The implementation may
  already be correct against the spec; the gate is the missing
  input.
- (2) is heavier: the implementation may need a design /
  re-investigation. The "user just provides config" path is not
  safe to assume; the missing primary-source verification may
  reveal a contract gap the impl has not anticipated.
- (3) means the implementation looks right against authoritative
  contract, but no real run has been observed. Surface which
  gap class the unsatisfied real test belongs to before closing.

**A measurement that is still running.** A bounded, expensive, or
rate-limited external measurement that has not returned is neither a
pass nor a fail, and it is not the same situation as a test that was
never run. It is a fourth situation: the claim stays Unverified, the
measurement's scope and its resume point are recorded
(`change-impact.md` §3), and the pending result counts in neither
direction. The affected decision proceeds on the evidence already in
hand when that evidence is sufficient to decide it — apply the test in
`.claude/skills/spec/references/fact-verification.md` §8 — and work
that does not depend on the pending measurement continues
(`cross-layer-coordination.md` §2.5.c). Do not extend a measurement
without bound to obtain certainty, and do not hold the whole chain
waiting for it.

### 4.9 Preserve evidence kind and boundary across layers

When reusing a claim, keep its **observed**, **estimated**, **assumed**, or
**unverified** nature, source version, conditions and command/method beside
the existing evidence record. Separate the actual observation from the
derivation and its assumptions; link back rather than copying a stronger
claim into Spec, Design or a review brief.

A measured rate on one operation may support a conditional estimate for a
larger path; it does not measure that path or prove an acceptance bound
impossible without a justified derivation. Keep the confirmed bound and
operation order while investigating compliant designs. If data is only
partly available, name which user actions are available; enabling an action
earlier than the confirmed order changes product behavior. Only a run of the
stated boundary supports a measured end-to-end duration.
If that run is unavailable, apply §4.8 and preserve the missing evidence.

## 5. Evidence Standard

The Reviewer distinguishes three levels of confidence and must label
each material claim with one:

- **Verified** — direct evidence from an authoritative source, a primary
  document, or empirical observation. The Reviewer's own re-derivation
  counts as Verified.
- **Reasonable Judgment (Unverified)** — plausible reasoning without
  primary evidence. Useful for surfacing candidate issues; must NOT be
  promoted to a Confirmed Defect.
- **Unknown** — the Reviewer cannot establish the fact within current
  limits. Recorded as `Missing Information`, with a `How to Verify`
  pointer.

The Reviewer must NEVER treat another agent's conclusion (including the
Main Agent's Triage verdict or the Author's "this fix is correct"
assertion) as independent evidence. The Reviewer re-derives from
authoritative sources.

## 6. Bound the Loop

A Targeted Resolution Verification finding surfaces a fix-needed
item. The cycle has a **single, consistent state machine** —
there is no separate "continue inside" rule that can be read in
opposition to a stop rule.

### 6.1 The cycle

```
Fix  ↔  Targeted Resolution Verification
```

A fix is verified once against its Necessary Condition and changed scope.
Reuse unaffected evidence. Triage new findings before entering another
cycle: only a violated Necessary Condition or a material regression caused
by the current fix blocks it. Distinct pre-existing gaps are routed to
their owner and scheduled by their actual dependency; they do not force
another review of the same fix. Ordinary improvements are recorded/deferred,
not promoted to mandatory work or a reason for another full review. Keep
the original finding IDs and review basis stable across targeted rounds;
do not enlarge the target merely because a reviewer suggested more probes
or more complete recovery prose.

### 6.2 When the same finding needs more than one round

A finding may persist across rounds only when each round
produces **new evidence** about the finding's Necessary
Condition. Before the next round:

1. **Re-derive the original Necessary Condition.** If the
   fixture's expected value is `-0.001134430...`, the value
   must derive from the same source after every iteration. If
   it cannot, the *test* was authored incorrectly, not the
   implementation.
2. **Compare each iteration's evidence quality.** Author-self-
   verified algebra and a separate-tool recomputation are not
   the same evidence. If a previous round's evidence was weak,
   that is *why* it did not hold — change the evidence source
   (independent recomputation, mpmath / sympy comparison, hand-
   derived closed form, a separate derivation route). Do not
   tweak the same weak evidence into alignment.
3. **Distinguish the fix dimension** by impact (per
   `cross-layer-coordination.md` §2.5.b) — not by operation
   name. A fix that the impact factors classify as in-
   authority for the owning Skill does **not** need a fresh
   user authorization; continue the cycle with a stronger
   evidence source. A fix that crosses the factors needs a
   fresh user authorization — branch into cross-layer
   coordination §2.5.b; do not chain the user-decision loop
   into the same cycle as a routine correctness fix.

### 6.3 Stop conditions

Pause the affected loop for diagnosis when any of these holds:

- **Necessary Condition not converging under independent
  evidence.** The same NC fails to verify across two rounds
  despite a fresh evidence source. Two independent attempts
  that both disagree with the NC mean the *approach* is wrong,
  not the value. Iteration count is not a budget to spend.
- **The fix requires upstream correction** — use cross-layer
  coordination and existing task authorization. A layer boundary alone
  does not require a new user decision.
- **The remaining gap is a goal / scope / key-constraint
  decision the Main Agent cannot make alone.**

Investigate the disputed premise, evidence source or method before another
fix; do not relabel the issue, weaken acceptance or transfer it downstream.
If that investigation produces a genuinely new corrective basis, record it
and resume the scoped loop. Otherwise save the failing condition and return
point, continue unaffected work, and report the actual missing input or
capability. Ask the user only for a real product/authorization decision.

### 6.3.a Reviewer execution failure

Before a required reviewer call, record its target, source snapshot,
Necessary Condition and return point in the existing Resume Notes. This
lets a new session recover even if the process ends before the call returns.
Do not mark Review Executed until a report is actually received.

Timeout, tool failure, missing or incomplete report is **no review result**,
not PASS or Review Executed. Save the source/target snapshot, scope, error
and return point. After diagnosing the execution failure, retry once with
the same necessary scope (or a fresh independent reviewer with the same
basis). If unavailable again, keep the required review open. Other evidence
may support diagnosis and unaffected work, but does not impersonate a
required Independent Review. Do not restart a full review endlessly or ask
the user to schedule retries. A later retry needs a changed availability
condition and the saved scope.
If the tool/agent registry already establishes that independent execution
is unavailable, record the limitation directly; no retry is useful. Check
an available alternative once, not by scanning the machine for similarly
named skills. Loading a review Skill in the author's context does not create
an independent reviewer. A nested CLI started from the author's shell without
the project's Reviewer definition, exact basis and read-only boundary is not
an alternative review result.

### 6.4 Anti-patterns within the cycle

These are the looping-discipline failures the cycle is designed
to prevent. They are named so they are not absorbed back into
"continue vs. stop" rhetoric:

- **Tweaking the same evidence source.** Two rounds of
  "author verifies their own fix" is the failure mode. If the
  fix did not hold, change the evidence source.
- **Continuing past a stop condition.** An iteration that
  needs a goal / scope decision is not a routine correctness
  fix; routing to cross-layer coordination is mandatory, not
  optional. A "user-authorized beyond the cap" bypass does not
  buy correctness, only continued iteration.
- **Lowering the original guarantee** to make the cycle pass
  (renaming the problem, accepting a smaller subset, deleting
  the failing test). The guarantee is the cycle's reason for
  existing.
- **Asking the user to choose between known-broken and
  Implementation-guessing.** Both options are unfaithful to
  the cycle; surface the constraint with evidence and let the
  user choose between a real decision and more work, not
  between two forms of failing.

The Reviewer may surface a problem the Main Agent cannot resolve
in the current authorization. That is a feature, not a failure
mode.

## 7. Closure Language Discipline

The Reviewer reports execution honestly. Two flavors, one canonical
state.

| Mode | Flavor reported by the Reviewer |
|---|---|
| Mode A — Independent Review | `Review Executed: yes — Mode: Independent Review — Scope: <target>` |
| Mode B — Targeted Resolution Verification | `Targeted Verification Executed: yes — Scope: <the change>` |

Both flavors are instances of the canonical `Review Executed` state in
`.claude/references/cross-layer-coordination.md` §5. The Reviewer MUST
NOT claim `Authority Resolved` or `Implementation Verified` in either
mode.

The Main Agent / Owning Skill asserts `Authority Resolved` after the
authoritative content is actually changed; `Implementation Verified`
after empirical observation. Neither is the Reviewer's claim.
