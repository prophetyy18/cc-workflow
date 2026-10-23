# INTENT.md Template

The field-level contract for a new or restructured `INTENT.md`. Load it when
creating a new intent file or reorganizing an existing one. The section set
and the reasoning behind it are in `SKILL.md` §13; this file is the template
and the writing rules.

The `#` section names are a **compatibility surface** — Spec, Architecture,
Implementation and Intent-Reconcile read INTENT.md by these headings. Keep
the names and the order. What the second round of this skill changed is
*what goes inside them*, and the fact that most of them are now optional.

## 1. Template

```markdown
---
id: INT-NNN
title: <short title>
status: active
parent: INT-NNN        # omit this field if none
related:               # omit this field if none
  - INT-NNN
impact_scope: []       # YAML list of known affected areas; [] until known
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# Original Intent

## User Request

<verbatim user input — no paraphrase, no agent interpretation>

# Clarified Intent

## Goal / Desired Outcome

- **G-01**: <the result the user wants, in business terms>
  **Why**: <the user's reason, if they gave one>
  **Success evidence**: <what the user can observe that it was reached>

## User-Visible Flow

<only when the goal has an ordered path>

1. <step, in confirmed order>

# Constraints and Success Criteria

## Hard Constraints

- **C-01**: <a limit that must not be violated>
  **Check**: <how a later stage observes it>

## Scope Exclusions

<optional — only explicit exclusions>

- <what is out of scope, and who said so>

## Success Criteria

<optional — only criteria that span goals; a criterion that belongs to one
goal sits with that goal>

- **S-01**: <observable result>

# Decisions

## Confirmed Decisions

- **D-01** (YYYY-MM-DD · CONFIRMED): <a choice the user actually made>
  **Rationale**: <the context the user gave>

## Inferred, Not Authorized

<optional — agent inferences, clearly separated>

- **(assumed)**: <inference> — **Confirm by**: <question, or "not needed">

# Facts and Research

<optional — only facts that bear on the goal>

## Verified Facts

- **Fact**: <one sentence, the minimum claim>
  **Source**: <URL or path:line in this repo>
  **Verified on**: <YYYY-MM-DD>
  **Scope**: <what this covers and does not cover>
  **Uncertainty**: <remaining doubt>

# Unknowns

<optional — open product choices>

## Blocking

- **Question**: <an open product choice>
  **Why it matters**: <what changes in the goal, scope, or a core constraint>
  **Owner**: user

## Non-blocking

- **Question**: <an open item that a later stage can settle>
  **Resolve in**: <Spec / Configuration / Implementation>

# Evaluation

<optional — engineering only>

## Engineering Feasibility

- **Assessment**: <brief technical feasibility assessment>
  **Evidence**: <the verified fact or the explicit uncertainty it rests on>

## Engineering Risks

- **Risk**: <a technical failure mode, not a product or priority judgment>
  **Signal**: <earliest observable indication>
  **Mitigation**: <an engineering action, or a question for a later stage>

# Relationships and Impact

<optional>

## Links

- **Parent**: <INT-NNN or none>
- **Children**: <INT-NNN list or none>
- **Related**: <INT-NNN list or none>

## Impact Scope

- **Affected behavior**: <user-facing behavior that may change>
- **Modules or interfaces**: <verified paths, or recorded as unknown>
- **Downstream Specs**: <known Spec IDs or none>

# Spec Input

<optional — a short handoff map, never a copy>

## Consume

- **Goals**: <INT-001/G-01 — one line of label each>
- **Constraints**: <INT-001/C-01>

## Do Not Decide

- <the product choices that remain the user's>

# Resume Notes

<optional>

## Current State

- **Last action** (YYYY-MM-DD): <what was done>
- **Open questions**: <unresolved items or none>

## Next Action

- **Owner**: <user, this skill, or a downstream agent>
- **Action**: <the specific next step and the return point>
```

## 2. Single Authority

The section map is in `SKILL.md` §13.1 — one piece of business meaning, one
home. The rules that follow from it, in the form they apply while writing:

- **A goal is stated once.** `# Constraints and Success Criteria`,
  `# Decisions`, and `# Spec Input` point at it; they never restate it.
- **Success evidence belongs to its goal.** A standalone `S-xx` entry exists
  only for a criterion that spans goals.
- **A stated limit is not also a Decision.** A Decision is not also a
  Constraint. Two homes for one fact is how two authoritative records drift
  apart and start contradicting each other.
- **A user-stated choice that is already a Goal or a Constraint is not
  copied into `# Decisions`.** `# Decisions` holds the choices that were
  *made* — typically after a clarification, and typically with a history
  worth keeping.
- **`# Spec Input` never copies content.** It points at item IDs and names
  the choices the Spec Agent must return to the user.
- **An inference is never a decision.** `(assumed)` items live under
  `## Inferred, Not Authorized` and are never counted as confirmation.
- **One uncertainty, one entry.** An inference that is still waiting for the
  user is one non-blocking question in `# Unknowns` — not an `(assumed)`
  entry and a question about the same thing.
- **An undecided product choice lives in `# Unknowns` only** — blocking when
  the answer changes the goal, scope, or a core constraint; non-blocking
  when a later stage can settle it.

## 3. Required, Optional, and Empty

- Always written: `# Original Intent`, `# Clarified Intent`,
  `# Constraints and Success Criteria` — they may each be very short.
- Written when they have content: `# Decisions`, `# Facts and Research`,
  `# Unknowns`, `# Evaluation`, `# Relationships and Impact`, `# Spec Input`,
  `# Resume Notes`.
- **A section with no real content is omitted**, not filled with a
  placeholder. At creation time only `# Original Intent` exists; the others
  appear as content is confirmed.
- A goal with nothing under it yet is better expressed as a single open
  question in `# Unknowns` than as an empty section.

## 4. Writing Rules

**Goals.** Describe the result the user wants, not the features they imagine.
Prefer business outcomes; keep the user's own vocabulary. Do not enumerate
internal steps — a goal may describe the necessary user-visible scenario
without spelling out the system's internal sequence. One goal = one
independent outcome; a goal may feed several Specs.

**Success evidence.** "The user can see that the strategy stopped after the
single-leg failure and the exposure was reported" — user-observable, not
"the state machine handles PARTIAL_FILL correctly". Evidence the user
cannot observe belongs to Spec acceptance, not here.

**Constraints.** Record only limits the user stated, business boundaries
that must not move, risk limits the user asked for, and explicit exclusions.
Do not promote ordinary engineering practice into a hard constraint:
"a single-leg fill failure must be handled" is a constraint, "use
`clientOrderId` and a durable event log" is a design decision for Spec and
Architecture.

**Expectations are not guarantees.** "I want to make money" is a desired
outcome. It does not become "every executed trade must be profitable" —
that is a promise the system cannot keep, and writing it as one creates a
goal the downstream layers cannot satisfy. Keep the four things apart:
expected return, execution cost, realized profit, and the uncertainty of
future market conditions.

**Decisions.** Every entry carries a date and a provenance label:
`USER-STATED`, `CONFIRMED`, `INFERRED`, or `UNRESOLVED` (`SKILL.md` §13.5).
An `UNRESOLVED` decision is a blocking entry in `# Unknowns`; it is not
repeated here.

**Open questions.** Only questions whose answers change the goal, the
scope, or a core constraint are worth tracking as blocking. Runtime
parameters, API details, and implementation choices are non-blocking and
usually belong to a later stage. If a question has an obvious default and
the wrong answer would not change the goal, do not ask it at all.

**Facts.** Record a fact only when it bears on the goal — it decides whether
the goal is achievable as stated, or it underpins a decision the user made.
Fee schedules, funding-rate snapshots, and API parameter lists are
research, not Intent content, unless one of them changes the goal's
feasibility or a user's decision (`references/research.md` §2).

## 5. Two Short Examples

A simple request produces a short document:

```markdown
# Original Intent

## User Request

我需要一个个人待办事项工具。

# Clarified Intent

## Goal / Desired Outcome

- **G-01**: 我能记录、查看和完成自己的待办事项。
  **Success evidence**: 待办事项在一次会话中保持可见，并能标记完成。

# Constraints and Success Criteria

## Hard Constraints

- **C-01**: 待办事项保存在本地，不需要账号登录。
```

A confirmed constraint added later lands in the constraints section, with
its history — not as a new goal, and not copied into `# Decisions`:

```markdown
# Constraints and Success Criteria

## Hard Constraints

- **C-01**: 待办事项保存在本地，不需要账号登录。
- **C-02**: 待办事项必须支持按截止日期排序。
  **Check**: 排序结果对用户可见。
```

## 6. Compatibility

Existing `INTENT.md` files keep working: the section names and order are
unchanged, and every older field label is still valid. When an older
document repeats the same content in several places, the repetition may
stay — it is no longer required, and new content does not create more of it.
Restructuring an old document into this template is allowed, but it is never
required and it is never done in bulk: migrate one intent when it is
touched anyway, and keep every old pointer resolvable
(`references/item-ids.md` §5).
