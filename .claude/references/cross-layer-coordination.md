# Cross-Layer Coordination

A minimal, on-demand reference for Skills (Intent, Spec, Architecture, Module Design, Implementation, Verification) when a finding, feedback, or change crosses authority layers. **Read this only when the current problem touches more than one layer.**

This is **not**:

- A Skill.
- A Subagent.
- A workflow engine.
- A new lifecycle state.
- An issue tracker.

It is a rules file. Load it from the Skill that needs to escalate, propagate, or coordinate.

## 0. Relationship to the Derive → Locate → Resolve → Verify reasoning

Each Skill that surfaces or routes issues applies a shared **Derive → Locate → Resolve → Verify** reasoning method, but the reasoning is performed inside the Skill itself, not by this document.

- **Derive** and **Locate** live in the Independent Reviewer (`.claude/agents/independent-reviewer.md` §0 / §3). The Reviewer reports findings; it does not act on them.
- **Resolve** and **Verify** live in the Owning Skill's triage (e.g. `.claude/skills/spec/references/review.md` §2.7). The Owning Skill decides the action and the closure language.

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

## 2. The five coordination stages

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
| **Review Executed** | The Review ran and returned its report. | Independent Reviewer |
| **Authority Resolved** | The owning layer has, with evidence, confirmed, modified, or rejected the issue. | Owning Skill (Intent / Spec / Architecture / Module Design / Implementation) |
| **Implementation Verified** | Actual runtime / data / contracts have been observed to satisfy the resolved requirement. | Verification (Test, runtime observation, code review) |

Rules:

- The Reviewer must never claim `Authority Resolved` or `Implementation Verified`.
- The Owning Skill must never claim `Implementation Verified` without Verification evidence.
- Verification never claims `Authority Resolved` — that is the upstream layer's decision.
- These are **logical states**, not new document lifecycle statuses. They are recorded in `# Resume Notes`, `# Unknowns and Upstream Feedback`, etc., as plain language — never as a `closed` field on a Finding.

## 6. Anti-patterns

The following are **not** cross-layer coordination; they are coordination failure modes. Avoid them.

- **All defects → Spec.** Routing Architecture / Module / Implementation findings back to Spec as "add a Requirement".
- **All suggestions → Confirmed Defect.** Inflating severity to demand a fix.
- **Tech solution → authoritative Requirement.** Writing "use Redis" into a Spec because a Reviewer proposed it.
- **Triage rubber-stamps.** The Owning Skill copying the Reviewer's recommendation without independent judgment.
- **Unconditional loops.** Reviewer → Fix → Reviewer → Fix with no clear stopping condition.
- **Self-closing.** Claiming `Implementation Verified` without empirical evidence.
- **Decision-talk fatigue.** Creating a feedback record for every micro-issue.
- **Same-root, duplicate findings.** Producing separate Findings for the same root cause instead of merging them.

## 7. When this reference is loaded

Load this file when a Skill:

- Receives a finding whose owner is not the current Skill.
- Needs to escalate or redirect.
- Is about to modify authoritative content and must check impact.
- Has multiple Findings with a common root cause.
- Receives a forward message from another Skill.

Do not load it for routine single-layer work.