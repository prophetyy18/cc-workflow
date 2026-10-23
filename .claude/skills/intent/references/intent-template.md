# INTENT.md Template

The field-level template for a new or restructured `INTENT.md`. Load it when
creating a new intent file or reorganizing an existing one; the section
names, order, and behavioral rules it must obey are summarized in
`SKILL.md` §13.

Keep the `#` section names and order — downstream readers use them. For each
section you retain, use its specified `##` headings and field labels so a
reader can distinguish confirmed input, inference, evidence, and open work.
Omit a subsection with no applicable content; do not invent data to fill the
shape.

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

<verbatim user input — do not paraphrase>

# Clarified Intent

## Confirmed Goal

- **Goal**: <outcome stated or confirmed by the user; keep their constraints intact>
- **Operation sequence**: <ordered user-visible steps from the real starting state>

## Assumptions to Confirm

- **(assumed)**: <agent inference, not a confirmed decision>
  **Confirm by**: <specific question for the user>

# Constraints and Success Criteria

## Hard Constraints

- **Constraint**: <non-negotiable requirement stated by the user>
  **Check**: <how a later stage can verify it>

## Success Criteria

- **Outcome**: <observable result the user wants>
  **Measure**: <what would show that it succeeded>

# Decisions

## Confirmed Decisions

- **Decision** (YYYY-MM-DD): <choice the user actually confirmed>
  **Rationale**: <brief context; do not present agent advice as confirmation>

# Facts and Research

## Verified Facts

- **Fact**: <one sentence, the minimum claim>
  **Source**: <URL or path:line in this repo>
  **Verified on**: <YYYY-MM-DD>
  **Method**: <how verified>
  **Scope**: <what this covers and does not cover>
  **Uncertainty**: <remaining doubt>

# Unknowns

## Open Questions

- **Unknown**: <what is unknown>
  **Why it matters**: <downstream impact>
  **How to resolve**: <specific action>

## Deferred Questions

- **Question**: <unanswered question deliberately deferred>
  **Return when**: <trigger or next stage that must resolve it>

# Evaluation

## Engineering Feasibility

- **Assessment**: <brief technical feasibility assessment based on known evidence>
  **Evidence**: <verified fact or explicit uncertainty supporting the assessment>

## Engineering Risks

- **Risk**: <technical failure mode, not a product or priority judgment>
  **Signal**: <earliest observable indication>
  **Mitigation**: <engineering action or question for a later stage>

# Relationships and Impact

## Links

- **Parent**: <INT-NNN or none>
- **Children**: <INT-NNN list or none>
- **Related**: <INT-NNN list or none>

## Impact Scope

- **Affected behavior**: <user-facing behavior that may change>
- **Modules or interfaces**: <verified paths or interfaces; otherwise record as Unknown>
- **Downstream Specs**: <known Spec IDs or none>

# Spec Input

## Goal and Context

- **Goal**: <one line, plus the pointer to the authoritative item, e.g. INT-001/G-01>
- **Why**: <reason stated by the user; mark any inference (assumed)>

## Requirements and Evidence

- **Source map**: <INT-001/G-01, INT-001/C-01, INT-001/S-01, INT-001/D-01 — one line of label each, no copied text>

## Decision Boundaries

- **Impact scope**: <pointer to # Relationships and Impact>
- **Do not decide**: <choices the Spec Agent must return to the user>

# Resume Notes

## Current State

- **Last action** (YYYY-MM-DD): <what was done>
- **Open questions**: <unresolved items or none>

## Next Action

- **Owner**: <user, this skill, or downstream agent>
- **Action**: <specific next step and return point>
```

## 1. Single Authority

One fact or decision has exactly one authoritative location:

| Content | Authoritative location |
|---|---|
| The user's verbatim request | `# Original Intent` |
| The confirmed goal and the operation sequence | `# Clarified Intent` |
| Hard constraints and success criteria | `# Constraints and Success Criteria` |
| Confirmed decisions | `# Decisions` |
| Verified facts | `# Facts and Research` |
| Open and deferred questions | `# Unknowns` |
| Relationships and affected areas | `# Relationships and Impact` |
| Progress and return point | `# Resume Notes` |

`# Spec Input` is a **handoff map**. It points at the sections above by item
ID (`INT-001/G-01`, `INT-001/C-01`, `INT-001/S-01`, `INT-001/D-01`) instead
of copying their content. A reader without conversation context follows the
pointers.

## 2. Optional Sections

`# Facts and Research`, `# Evaluation`, `# Relationships and Impact` and the
material parts of `# Spec Input` are used when the intent actually has that
content. A section with no real content may use `_TBD_` while drafting;
resolve or remove it before archive (`SKILL.md` §10). Never pad with fake
content.

## 3. Worked Notes

- The user's verbatim request stays in `# Original Intent`. If the user only
  said "I want a shared team calendar", external calendar sync is **not**
  confirmed: record it under `## Assumptions to Confirm` as
  `- **(assumed)**: The calendar must sync with external providers.` followed
  by `**Confirm by**: Ask which providers, if any, are required.` Do not put
  it under `## Confirmed Goal` or `## Confirmed Decisions` until the user
  answers.
- `# Evaluation` is limited to engineering feasibility and engineering risks.
  Keep it brief. Product value, market fit, priority, and whether the goal
  is worth pursuing belong to the user; raise such points as questions
  instead.
- `# Clarified Intent` states the user's operation sequence from a real
  starting point at user level. Detailed UI behavior, error and failure
  handling, and system state transitions belong to Spec (`SKILL.md` §18).

## 4. Compatibility

Existing `INTENT.md` files keep working: the section names and order are
unchanged, and every older field label above is still valid. When an older
document repeats the same content in several places, the repetition may
stay — it is no longer required, and new content does not create more of it.
