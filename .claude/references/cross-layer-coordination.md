# Cross-Layer Coordination

A minimal, on-demand reference for Skills (Intent, Spec, Architecture, Module Design, Implementation, Verification) when a finding, feedback, or change crosses authority layers. **Read this only when the current problem touches more than one layer.**

This is **not**:

- A Skill.
- A Subagent.
- A workflow engine.
- A new lifecycle state.
- An issue tracker.

It is a rules file. Load it from the Skill that needs to escalate, propagate, or coordinate.

## 0. Relationship to the Derive → Locate → Resolve → Validate reasoning

Each Skill that surfaces or routes issues applies a shared **Derive → Locate → Resolve → Validate** reasoning method, but the reasoning is performed inside the Skill itself, not by this document.

- **Derive** and **Locate** live in the Independent Reviewer (`.claude/agents/independent-reviewer.md` §0 / §3). The Reviewer reports findings; it does not act on them.
- **Resolve** and **Validate** live in the Owning Skill's triage (e.g. `.claude/skills/spec/references/review.md` §2.7). The Owning Skill decides the action and the closure language. The triage Validate step is **proposed-resolution validation** — it does not claim the fix has been applied or verified empirically (those are downstream closure states in §5).

This document only defines the **cross-layer protocol** — when the Resolve step names a different authority, or when several authorities must act. The Identify / Escalate / Resolve / Propagate stages below are how cross-layer issues move between authorities; the `Resolve` stage here is *not* the Owning Skill's internal Resolve step (that happens earlier). Apply §4 (Minimum necessary escalation) whenever a Resolve decision crosses an authority boundary.

## 1. Authority layers (who decides what)

| Layer | Authority (decides) | Does NOT decide |
|---|---|---|
| **Intent** | User goals, important constraints, confirmed decisions, success criteria | System behavior, modules, APIs |
| **Spec** | System capabilities, functional / non-functional requirements, system invariants, acceptance | Module names, API shapes, schemas, algorithms |
| **Architecture** | Module responsibilities, public capability ownership, dependency direction, cross-module invariants | Specific APIs, schemas, internal algorithms |
| **Module Design** | Specific APIs, schemas, internal structure, algorithms | Why capabilities exist, what they must guarantee, system responsibility allocation |
| **Implementation** | Actual code | Anything not yet codified in the upstream layer |
| **Verification** | Empirical evidence that runtime / data / contracts behave as required | Authority correctness — verification reports observed behavior; authority remains with the layer that defined the requirement |
| **User / Product Owner** | Product defaults, trade-offs, business decisions the agent cannot make | Implementation details |

**Discipline:** an issue belongs to the **highest necessary** layer whose authority must change. Not always the layer the Reviewer first inspected. Not always Intent.

## 2. The six coordination stages

When a problem touches more than one layer, apply these stages in order. Skip any stage that does not apply.

### 2.1 Identify

Ask: "Can the current Skill resolve this issue while preserving all confirmed upstream constraints?"

If **yes** → resolve within the current Skill. Done.

If **no** → identify the **smallest** set of layers that must act.

Do not list every layer that *might* be relevant. List only the layers that *must* act.

### 2.2 Escalate (only as high as necessary)

Send a feedback message to the next-higher authority whose content must change. Use the feedback contract (§3).

Rules:

- **Do not default to Intent.** Most cross-layer issues are Spec / Architecture / Module Design issues.
- **Do not escalate beyond the necessary authority.** A module-internal algorithm error is Module / Implementation; do not push it to Spec or Intent.
- **One escalation per change.** If a single change requires multiple layers, the higher layer decides first, then propagation (§2.4) reaches the lower layers.

Examples:

| Issue | Highest necessary authority |
|---|---|
| Cache eviction algorithm wrong | Module / Implementation |
| API type signature wrong but contract Owner is clear | Contract Owner |
| Two modules claim ownership of the same authoritative state | Architecture |
| Spec lacks observable system behavior | Spec |
| User goal must be re-chosen | Intent / User |

### 2.3 Resolve

The target Skill reads its own authoritative basis and decides:

- **Current authority sufficient** — the issue can be resolved inside this Skill without authoritative content change. Close.
- **Authoritative change required** — make the change. Record the rationale and what evidence supports it.
- **Insufficient evidence** — request more evidence. Do not invent.
- **Owner decision required** — escalate to the User / Product Owner.
- **Wrong authority / redirect** — the target layer cannot resolve this; redirect back to the correct layer with reason.

Rules:

- The target Skill **does not automatically accept** Reviewer / Triage suggestions. It judges independently.
- The target Skill records its decision, rationale, and any downstream impact in its own work document (Spec / ARCHITECTURE / MODULE / INTENT). It does not create a parallel decision log.
- If the target Skill disagrees with the request, it returns a `Rejected` decision with reasoning.

### 2.4 Propagate (only where dependencies justify)

When authoritative content actually changes, check:

- **Vertical impact** — downstream layers that consume the changed authority.
- **Sibling impact** — peer artifacts sharing the same requirement, contract, or capability.

Use existing impact machinery when available:

- Architecture Skill: `/architecture impact <spec-id>` walks `Requirement Change → Capability → Provider → Public Contract → Consumers → Verification`.
- Spec Skill: §19 Downstream Routing.
- Intent Skill: §13 `Relationships and Impact`.

Rules:

- Base propagation on **actual dependencies**, not topical similarity:
  - Authoritative Requirement references.
  - Known module responsibility mappings.
  - Public Contract Owner and Consumers.
  - Real code dependencies.
  - Existing verification obligations.
- When dependencies are unclear, mark `Unknown`. Do not pretend to have located all affected objects.
- Do not trigger a full project scan for every change. Scale to the actual change.

### 2.5 Verify and Return

Before the originating Skill accepts a returned Fix and proceeds, it
**re-checks the authoritative artifact against the resolution** — it
does not rely on the returner's claim alone. The check is small but
strict:

- Did the targeted authoritative content actually change in the
  expected way (read the file / state the return message references,
  not just the prose summary)?
- Does the artifact now satisfy every Necessary Condition the
  Fix was supposed to restore? A Necessary Condition introduced by
  the Fix must be checked the same way a Necessary Condition
  introduced by original authoring is checked.
- Do cross-document References in the artifact (e.g. "depends on
  `<other-doc>` (`<status>`)") still match the **current** state
  of the cited document, or do they survive only as historical
  context? If stale (e.g., a Provider was promoted from `draft`
  to `final` after a reopen but the Consumer still says
  "currently draft"), the originating Skill notes the drift and
  fixes it in the same loop or routes it forward via the same
  feedback contract — never silently let the drift persist.

If any of those reads is not what the originating Skill expects,
the Fix did not actually land. Treat the return message as
unverified and re-route.

### 2.5.b Status-gate disciplines (cross-Skill)

The same discipline applies to any status transition that
encodes a completion claim (Spec `archived`, Module Design
`final`, Implementation `handoff`):

- Read the artifact's `# Unknowns` / `# Blocking Unknowns and
  Implementation Handoff` / equivalent sections **at the moment of
  the transition**. The transition is invalid if any item is still
  flagged Blocking; resolve or reclassify first.
- Read the artifact's `Source <other-doc>` / "depends on" /
  cross-module References and confirm they match the **current**
  authoritative state of the cited document (not historical). If
  stale, update or surface as Architecture-completeness, Spec, or
  Implementation follow-up — do not finalize on stale references.
- Trigger evidence declared in the Skill's §13 must be on hand,
  not claimed. "Will be done by Implementation" is not Trigger A
  evidence at the Design gate — it is a follow-up handoff
  obligation that Implementation owns.

The downstream Owner returns:

```text
Source Issue Reference: <where this came from>
Decision: <Accepted | Rejected | Deferred | Redirected>
Rationale: <one short paragraph>
Actual Changes: <list of file paths / item IDs changed, or "none">
Verification Performed: <how the change was checked, or "no verification yet">
Outstanding Obligations: <what remains, if anything>
```

The originating Skill judges whether its own authority problem is now resolved.

**Three states are distinct** (see §5):

- Review Executed.
- Authority Resolved.
- Implementation Verified.

None implies the others. Do not collapse them.

### 2.6 Resume

Closing the feedback loop is not the end. The Main Agent (not the user) resumes the original task that was paused when the cross-layer issue surfaced.

- After §2.5 returns `Accepted` (or the originating Skill's analogue), load `# Resume Notes` for the originating task — for a module, the module's `DESIGN.md` is the canonical home; the Implementation Skill reads / writes there too (it does not start a separate log).
- Continue from the recorded position. Do not restart the task from the top.
- A routine correction (a local fix inside the originating Skill's authority) does not require a fresh user confirmation. Reserved confirmations are for material changes to goal / scope / key constraints / new trade-offs; those still go to the User.
- If the cycle completed but the original task is now materially different from what the user originally asked for, surface the delta. Otherwise resume silently and report only when the work produces a normal delivery moment.

The shared doc records the rule; each Skill's Cross-layer Triggers section instantiates it for that Skill's authored files.

## 3. Feedback contract

When escalating or propagating, use the minimum fields below. Do not invent new formats per Skill — these are common across all layers.

### 3.1 Forward message

```text
Source: <Skill / artifact that is sending>
  e.g. spec/SKILL.md reviewing docs/specs/SPEC-001/SPEC.md
Finding / Issue Reference: <F-N from a Review report, or a short description if no Review>
Target Authority: <Intent | Spec | Architecture | Module Design | Implementation | Verification | User>
Affected Authoritative Items:
  - <e.g. INT-001/C-01, SPEC-001/REQ-003, ARCHITECTURE §X>
Problem:
  <what is wrong or missing, in one short paragraph>
Evidence:
  - <path:line, URL, or runtime observation>
Required Decision:
  <what the target layer must decide or change>
Potential Impact:
  <which downstream layers / artifacts might be affected if this changes>
Requested Response:
  <what format the response should take; default = §3.2>
```

### 3.2 Return message

```text
Source Issue Reference: <mirror of the Forward message's id>
Decision: <Accepted | Rejected | Deferred | Redirected>
Rationale:
  <why this decision; cite authoritative basis>
Actual Changes:
  - <file path / item ID changed> — <one line>
  - "none" if decision is Rejected or Deferred
Evidence:
  - <path:line, URL, or runtime observation supporting the change>
Affected Downstream Scope:
  - <layers / artifacts that must now re-check> or "none"
Outstanding Obligations:
  - <verification still pending, related issues not yet addressed, etc.>
```

### 3.3 Where messages are stored

- In-session: as plain text between Skills via the Main Agent.
- Cross-session: written into the relevant existing authoritative document — `# Unknowns and Upstream Feedback`, `# Resume Notes`, ARCHITECTURE baseline change log, etc. **No parallel issue tracking system.**

## 4. Minimum necessary escalation (the core rule)

**Escalate only when the current authority cannot resolve the issue while preserving confirmed upstream constraints.**

When an issue spans multiple layers:

1. Find the **highest necessary authority** whose content must change.
2. Resolve that authority first.
3. Propagate downward through actual dependencies.
4. **Do not require every affected layer to redesign.**
5. **Stop** when the affected layer already has sufficient authority.

The goal is the minimum set of changes that:

- Fixes the root cause.
- Preserves all confirmed upstream constraints.
- Updates only the layers that need updating.

Anything beyond that is over-engineering.

## 5. Closure semantics (do not collapse these)

| State | Definition | Who marks it |
|---|---|---|
| **Review Executed** | The Review ran and returned its report. The Independent Reviewer supports two flavors under this single state: **Independent Review** (Mode A, full scope) and **Targeted Resolution Verification** (Mode B, focused on a specific change after an authorized fix). The Reviewer records the flavor and scope it actually executed under. | Independent Reviewer |
| **Authority Resolved** | The owning layer has, with evidence, confirmed, modified, or rejected the issue. | Owning Skill (Intent / Spec / Architecture / Module Design / Implementation) |
| **Implementation Verified** | Actual runtime / data / contracts have been observed to satisfy the resolved requirement. | Verification (Test, runtime observation, code review) |

Trigger rules for invoking the Reviewer in either flavor, the shared
Evidence Standard, and the loop bounding for post-fix verification live
in `.claude/references/verification.md`. This document does not
duplicate them; load that file only when the current Skill is about to
delegate, triage, or sequence a verification call.

Rules:

- The Reviewer must never claim `Authority Resolved` or `Implementation Verified`.
- The Owning Skill must never claim `Implementation Verified` without Verification evidence; this includes asserting `Authority Resolved` after a Targeted Resolution Verification has merely returned — see `.claude/references/verification.md` §6 for the loop bounding.
- Verification never claims `Authority Resolved` — that is the upstream layer's decision.
- These are **logical states**, not new document lifecycle statuses. They are recorded in `# Resume Notes`, `# Unknowns and Upstream Feedback`, etc., as plain language — never as a `closed` field on a Finding.

## 6. Anti-patterns

The following are **not** cross-layer coordination; they are coordination failure modes. Avoid them.

- **All defects → Spec.** Routing Architecture / Module / Implementation findings back to Spec as "add a Requirement".
- **All suggestions → Confirmed Defect.** Inflating severity to demand a fix.
- **Tech solution → authoritative Requirement.** Writing "use Redis" into a Spec because a Reviewer proposed it.
- **Triage rubber-stamps.** The Owning Skill copying the Reviewer's recommendation without independent judgment.
- **Unconditional loops.** Reviewer → Fix → Reviewer → Fix with no clear stopping condition. The shared loop-bounding rule lives in `.claude/references/verification.md` §6: one initial Targeted Verification per fix; at most one additional corrective fix plus one additional Targeted Verification; beyond that, surface the unresolved constraint and stop. Do not lower the original system guarantee to make a review pass.
- **Self-closing.** Claiming `Implementation Verified` without empirical evidence.
- **Decision-talk fatigue.** Creating a feedback record for every micro-issue.
- **Same-root, duplicate findings.** Producing separate Findings for the same root cause instead of merging them.
- **Auto-delegation of trivial edits.** Routing every Spec / Architecture edit to a full Independent Review regardless of impact. The Trigger rules in `.claude/references/verification.md` §3 — not the user's `/review` input — decide when an automatic review fires.

Additional anti-patterns, surfaced by actual run evidence:

- **Bundle unrelated findings in one revision.** A single fix
  revision that addresses a necessary defect AND a list of
  Improvements loses the necessary-vs-optional distinction. Pair
  the necessary fix with one of: queuing the Improvement for a
  separate revision; rejecting it with evidence; or asking the
  user only when the Improvement changes goal / scope / a key
  constraint. Do not let Improvements piggyback on a necessary
  fix to ride past triage.
- **Stale cross-document references at the status gate.** A
  Spec / Architecture / Module Design doc that still cites
  `currently draft` for a Provider that has since been promoted
  to `final` (or any analogous drift) is a default-FAIL on the
  status transition. Reconcile the references against current
  state at the moment of the transition — not in a "later
  cleanup" pass.
- **Status gates that read intent, not content.** "No Blocking
  Unknown remains" is true in prose but false in # Unknowns when
  one entry is still flagged Blocking. The check at the gate
  reads the section, not the prose.
- **Routine correctness escalation.** A rounding-mode tweak, a
  fixture number, an encoding constant, a parameter rename — none
  of these is a goal / scope / key-constraint change. Asking the
  user for a fresh authorization to apply them burns the
  verification loop and confuses "I have a problem" with "the
  user has to choose something". Reserve user authorization for
  the latter.
- **"Self-verified algebraically" as evidence.** Mentioning an
  algebraic check the author performed is not independent
  evidence. The Reviewer — or an external library — must
  recompute. See `verification.md` §4.2 / §4.4 and
  `independent-reviewer.md` §4 / §5.
- **Local fix → module-ready inference.** A single Targeted
  Verification that clears a local fix does not, by itself, make
  a module implementation-ready. Implementation Handoff
  requires the Trigger A evidence declared in the relevant §13
  to be on hand, not promised by follow-ups.

## 7. When this reference is loaded

Load this file when a Skill:

- Receives a finding whose owner is not the current Skill.
- Needs to escalate or redirect.
- Is about to modify authoritative content and must check impact.
- Has multiple Findings with a common root cause.
- Receives a forward message from another Skill.

Do not load it for routine single-layer work.