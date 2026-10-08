# Clarification Methodology

Read this when handling `new`, `resume`, or any clarification round within the intent skill.

## Goal

Turn ambiguous intent into testable, scoped, traceable input for a downstream Spec Agent — without writing code or designing solutions.

## Frontier Model

Model the intent as a **tree of decisions**. A question is on the **frontier** if all its prerequisite decisions are answered.

Each round:
1. Compute the frontier (questions whose dependencies are resolved).
2. Ask all frontier questions in one batch (or split if too many).
3. Record answers in `# Decisions`. The frontier expands.
4. Repeat until the frontier is empty, the user stops, or remaining questions are low-impact.

A question whose answer depends on another question still open in this round belongs to a later round. Do not ask it yet.

## Question Taxonomy

Cover these categories when relevant. Skip any that don't apply:

1. **Goal**: what the user actually wants to achieve (vs. the surface request).
2. **Scope**: in/out of bounds — which features, modules, users.
3. **Constraints**: hard limits (tech stack, time, compatibility, budget, platform).
4. **Success criteria**: how we know it worked. Must be testable.
5. **Assumptions**: things the user is taking for granted that we should make explicit.
6. **Risks**: what could go wrong, what the user is worried about.

## Prioritization

For each candidate question, score **impact × uncertainty**:

- **Impact**: if we get this wrong, how much downstream rework?
- **Uncertainty**: how confident are we in the current answer?

Ask high-impact, high-uncertainty first. Skip questions where:

- The answer is agent-verifiable (research it instead via `WebFetch` / `WebSearch` / repo inspection — see `research.md`).
- The downstream Spec Agent can decide it without blocking correctness.
- The user has already answered (check `# Decisions` first).

## Asking

- **One batch per round.** Ask multiple questions at once when they're truly independent. Don't drip-feed one at a time across many turns.
- **Prefer multiple choice** with a recommended option. Explain the recommendation in one sentence.
- For each question, include a one-sentence "why it matters."
- If a question has a known default, state it as the recommendation.
- Keep questions short. No labels-as-questions ("Acceptance device matrix (FR-023)" is invalid; ask the actual question).

## Validating Understanding

After the first round (or whenever major new info arrives), write back a one-paragraph restatement of the clarified intent and ask the user to confirm or correct. This goes into `# Clarified Intent`. Do not skip this step — it is the cheapest way to catch misunderstanding before it propagates.

## Scope Boundaries

- **Do not propose solutions.** Stay at goal / scope / constraint level. The Spec Agent handles solution design.
- **Do not start Spec writing or implementation.**
- **Do not pad with speculative edge cases** the user didn't raise. If the user is okay with an undefined edge, leave it in `# Unknowns`.
- **Do not re-ask settled questions.** `# Decisions` is the source of truth.

## Stop Conditions

Stop asking when:

- The frontier is empty.
- The user says stop.
- Remaining questions are low-impact (impact × uncertainty below threshold).
- The user has reached fatigue — defer remaining items to `# Unknowns` and let the Spec Agent handle them.

## Recording Decisions

For each confirmed decision, write to `# Decisions`:

```markdown
- YYYY-MM-DD: <decision> — <one-line context or rationale the user gave>
```

Decisions are immutable once recorded. If a decision changes later, append a new entry; do not edit the old one.

## Impact Scope

As the picture clarifies, populate `impact_scope` in the frontmatter with:

- Modules / files in this repo that will likely be touched.
- Public interfaces that may change.
- Related existing Specs.
- Related other intents (by id).
- Existing user-facing behavior that may shift.

It's okay for this to be incomplete at first. Update it as new info arrives. Mark unknown entries explicitly rather than fabricating module names.
