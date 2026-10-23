# INTENT.md Template

The field-level contract for a new or restructured `INTENT.md`: the
template, the section map, where each kind of content belongs, the layer
ownership table, the semantic consistency check, and the decision provenance
labels. Load it when creating a new intent file or reorganizing an existing
one. The Intent's identity, classification rule, and routing live in
`SKILL.md`.

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

The block above is the **full skeleton**, not a form to fill in. Keep the
section names and their order; keep only the sections that carry real
content (`references/intent-template.md` §3).

### 1.1 Section map

| Section | When | Authoritative for |
|---|---|---|
| `# Original Intent` | always | The user's own words, verbatim |
| `# Clarified Intent` | always | The desired outcome and its success evidence; the user-visible flow when the goal has an ordered path |
| `# Constraints and Success Criteria` | when it has content | Limits, boundaries, exclusions; success criteria that are not attached to a goal |
| `# Decisions` | when a choice was made | Choices the user made, each labeled by who made it (§8); agent inferences stay in their own subsection and are never counted as decisions |
| `# Facts and Research` | when it has content | External facts that bear on the goal's feasibility or on a user decision |
| `# Unknowns` | when it has content | Undecided product choices, split into blocking and non-blocking |
| `# Evaluation` | when it has content | Engineering feasibility and engineering risk only |
| `# Relationships and Impact` | when it has content | Parent / child / related, impact scope |
| `# Spec Input` | when it has content | Handoff pointers plus what the Spec Agent must not decide |
| `# Resume Notes` | when it has content | Position, next owner, next action |

**Document length follows the number of independent product decisions, not
the number of modules, Specs, or API surfaces involved.**

## 2. Single Authority

One piece of business meaning has one home. The rules that follow, in the
form they apply while writing:

| What changed | Where it goes |
|---|---|
| The desired outcome | `# Clarified Intent` (a new goal item, the old one kept as history) |
| A limit or exclusion | `# Constraints and Success Criteria` |
| A choice the user made | `# Decisions`, with date and provenance label |
| An open product choice | `# Unknowns` (blocking or non-blocking) |
| An external fact | `# Facts and Research` |

- **A goal is stated once.** `# Constraints and Success Criteria`,
  `# Decisions`, and `# Spec Input` point at it; they never restate it.
- **Success evidence belongs to its goal.** A standalone `S-xx` entry exists
  only for a criterion that spans goals.
- **A stated limit is not also a Decision.** A Decision is not also a
  Constraint. Two homes for one fact is how two authoritative records drift
  apart and start contradicting each other.
- **A user-stated choice that is already a Goal or a Constraint is not copied
  into `# Decisions`.** `# Decisions` holds the choices that were *made* —
  typically after a clarification, and typically with a history worth
  keeping.
- **`# Spec Input` never copies content.** It points at item IDs and names
  the choices the Spec Agent must return to the user.
- **An inference is never a decision.** `(assumed)` items live under
  `## Inferred, Not Authorized` and are never counted as confirmation.
- **One uncertainty, one entry.** An inference that is still waiting for the
  user is one non-blocking question in `# Unknowns` — not an `(assumed)`
  entry and a question about the same thing.
- **An undecided product choice lives in `# Unknowns` only** — blocking when
  the answer changes the goal, scope, or a core constraint; non-blocking when
  a later stage can settle it.
- **`# Resume Notes` and `# Relationships and Impact` record position,
  history, and effect** — never a second copy of a goal, a constraint, or a
  decision. They point at item IDs or name the section.

## 3. Required, Optional, and Empty

- Always written: `# Original Intent` and `# Clarified Intent`.
- Written when they have content: `# Constraints and Success Criteria`,
  `# Decisions`, `# Facts and Research`, `# Unknowns`, `# Evaluation`,
  `# Relationships and Impact`, `# Spec Input`, `# Resume Notes`.
- **A section with no real content is omitted**, not filled with a
  placeholder. At creation time only `# Original Intent` exists; the others
  appear as content is confirmed.
- A goal with nothing under it yet is better expressed as a single open
  question in `# Unknowns` than as an empty section.
- Downstream readers read INTENT.md by heading, so an absent section means
  **nothing of that kind was recorded** — an absent
  `# Constraints and Success Criteria` means "no hard constraints", an absent
  `# Unknowns` means "no open question", an absent `# Decisions` means "no
  choice was made". Absence is never an error, and no empty section is
  created to satisfy a reader.

## 4. Writing Rules

**Goals.** Describe the result the user wants, not the features they imagine.
Prefer business outcomes; keep the user's own vocabulary. Do not enumerate
internal steps — a goal may describe the necessary user-visible scenario
without spelling out the system's internal sequence. One goal = one
independent outcome; a goal may feed several Specs. When a request mixes two
business models that the user may not have noticed, record it as stated and
ask which outcome is meant (`references/clarification.md` §7).

**Success evidence.** "The user can see that the strategy stopped after the
single-leg failure and the exposure was reported" — user-observable, not
"the state machine handles PARTIAL_FILL correctly". Evidence the user
cannot observe belongs to Spec acceptance, not here.

**Constraints.** Record only limits the user stated, business boundaries
that must not move, risk limits the user asked for, and explicit exclusions.
Do not promote ordinary engineering practice into a hard constraint:
"the fill failure must be handled" is a constraint, "use an idempotency key
and a durable event log" is a design decision for Spec and Architecture.

**Expectations are not guarantees.** "I want to make money" is a desired
outcome, not "every executed trade must be profitable" — that is a promise
the system cannot keep. Keep expected return, execution cost, realized
profit, and the uncertainty of future market conditions apart
(`references/research.md` §5).

**Decisions.** Every entry carries a date and a provenance label (§8).

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

## 5. Layer Ownership

| Layer | Decides | Never pulled into Intent |
|---|---|---|
| **Intent** | why the user wants it, what result they want, what must not change, which product choices are still the user's, how the user knows it worked | — |
| **Spec** | observable system behavior, states and error paths, inputs and outputs, functional requirements, acceptance | system behavior and acceptance |
| **Architecture / Module Design** | module responsibility, interfaces, data and persistence, algorithms, technical dependencies | design and mechanisms |
| **Research** | external fact verification, feasibility evidence, dynamic parameter snapshots, sources and their limits | general technical research |

Cross-layer background may be repeated briefly, but the authoritative
definition lives in exactly one place. The test is whether the content
carries the **meaning of the user's goal** — not whether it happens to
contain a technical term.

## 6. Relationships

- `parent` — exactly one parent; "this is a sub-goal of X". The parent must
  exist, walking up must not include the child (no cycle), and an intent
  cannot be its own parent. An archived parent is allowed, with a warning.
- `related` — a loose "this affects that" link; multiple allowed. Add one
  only for a real cross-effect, not topical similarity.
- `impact_scope` — what this intent touches in the real world: modules or
  files, public interfaces, related Specs, related intents, existing
  user-facing behavior. Not the same as `parent` or `related`. Populate it as
  clarification progresses; mark unknown entries explicitly instead of
  inventing module names.

## 7. Semantic Consistency Check

Run it before saving a new or changed Intent, and again at archive. It is a
check, not a deliverable — do not produce a review report for it.

1. **Fidelity** — does any statement contradict `# Original Intent`?
2. **Provenance** — is an inference written as confirmed fact? Is any
   `(assumed)` item sitting in `# Decisions` as a confirmed choice?
3. **Constraint provenance** — is a limit present that the user never
   stated, with ordinary engineering practice promoted to a hard constraint?
4. **Coherence** — do the goals and the constraints contradict each other?
5. **Expectation vs. guarantee** — is an outcome the system cannot promise
   (profit, price, uptime, third-party behavior) written as a system
   guarantee?
6. **No duplication** — are there two entries with the same meaning?
7. **Layer discipline** — has a design decision been made early?
8. **Ambiguity** — does a key term in a goal still have two readings that
   would change the goal?

Fix what is wrong in the document and keep the history. If a fix would change
a meaning the user confirmed, ask the user instead of editing.

## 8. Decision Provenance

Every entry in `# Decisions` says who made it:

| Label | Meaning |
|---|---|
| `USER-STATED` | The user said it outright. It usually also appears as a Goal or a Constraint — do not copy it there again. |
| `CONFIRMED` | The user explicitly confirmed it after a clarification. |
| `INFERRED` | The agent inferred it. Inference is not authorization; it never appears as a confirmed decision. |
| `UNRESOLVED` | A product choice still open. It lives in `# Unknowns` as blocking and is not repeated in `# Decisions`. |

## 9. Compatibility

Existing `INTENT.md` files keep working: the section names and order are
unchanged, and every older field label is still valid. When an older
document repeats the same content in several places, the repetition may stay
— it is no longer required, and new content does not create more of it.
Restructuring an old document into this template is allowed, but it is never
required and it is never done in bulk: migrate one intent when it is touched
anyway, and keep every old pointer resolvable
(`references/item-ids.md` §7).
