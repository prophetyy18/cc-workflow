# Clarification Methodology

Read this when handling `new`, `resume`, or any clarification round within the intent skill.

## Goal

Turn ambiguous intent into testable, scoped, traceable input for a downstream Spec Agent — without writing code or designing solutions.

## 1. Frontier Model (Decision Dependency)

Model the intent as a **tree of decisions**. A question is on the **frontier** if all its prerequisite decisions are answered.

Each round:

1. Compute the frontier (questions whose dependencies are resolved).
2. Ask all frontier questions in one batch (or split if too many — see §3 quota).
3. Record answers in `# Decisions`. The frontier expands.
4. Repeat until the frontier is empty, the user stops, or remaining questions are low-impact.

A question whose answer depends on another still-open question belongs to a **later round**. Do not ask it yet.

## 2. Question Taxonomy (Intent-Focused)

Cover these categories when relevant. Skip any that don't apply:

1. **Goal**: what the user actually wants to achieve (vs. the surface request).
2. **Scope**: in / out of bounds — features, modules, users.
3. **Constraints**: hard limits (tech stack, time, compatibility, budget, platform).
4. **Success criteria**: how we know it worked. Must be testable.
5. **Assumptions**: things the user is taking for granted that we should make explicit.
6. **Risks**: what could go wrong, what the user is worried about.
7. **Relationships**: parent / child / related intents this goal should be linked to.
8. **Impact scope**: what existing modules, interfaces, or behaviors this goal will likely touch.

Categories 1–6 are the core. 7–8 are only invoked when the user already has a populated intent tree (e.g., during `resume` on a large project) or when the goal clearly crosses existing scope.

## 3. Quota: Max-5 + Deferred

Hard cap: **5 questions per clarification pass**. Re-asks for the same question do not count as new questions. When quota is exhausted with unresolved high-impact items remaining, they go into a `## Deferred` block in `# Unknowns`:

```markdown
## Deferred (clarification quota reached)

- <unanswered question> — why it matters
```

A new `resume` opens a fresh quota. Deferred items are re-considered first.

Avoid asking two low-impact questions when a single high-impact area is unresolved.

## 4. Question Format

Every frontier question must have:

- A real interrogative ending in `?` (not a label like "FR-023").
- A one-sentence "Why it matters."
- A **recommended answer** with one-sentence reasoning. Word the question so a one-word "yes" accepts the recommendation.
- 2–4 mutually exclusive options if multiple choice, or a free-form short answer otherwise.

For free-form answers, prompt the user to answer in **≤5 words** when possible. This prevents rambling answers that are themselves ambiguous.

## 5. Prioritization

For each candidate question, score **impact × uncertainty**:

- **Impact**: if we get this wrong, how much downstream rework?
- **Uncertainty**: how confident are we in the current answer?

Ask high-impact, high-uncertainty first. Skip questions where:

- The answer is agent-verifiable — research it instead (see `research.md`).
- The downstream Spec Agent can decide it without blocking correctness.
- The user has already answered — check `# Decisions` first.

## 6. Facts vs. Decisions Split

**Facts are the agent's job. Decisions are the user's.** Before asking anything, ask: "Could I find this out by reading code, docs, or running a search?" If yes, dispatch the search and use the result; do not put the user to work for it.

When a fact needs exploration, treat it as an unsettled prerequisite. **Do not block the whole frontier** waiting for it. Ask the other frontier questions now; only questions downstream of that fact wait.

## 7. Recording Decisions

Append to `# Decisions` after every confirmed answer:

```markdown
- YYYY-MM-DD: <decision> — <one-line context or rationale the user gave>
```

Decisions are append-only. **If a new answer contradicts an old one, replace the contradicted text** in the affected section (e.g., `# Clarified Intent`, `# Constraints`). Do not leave the contradiction standing. Note the replacement in `# Resume Notes` if it was non-trivial.

## 8. Stated vs. Assumed

When writing the `# Clarified Intent` restatement (see §10), distinguish:

- What the **user said** — record verbatim in `# Original Intent`; restate faithfully.
- What the **agent inferred** — label every inferred piece as "(assumed)" inline.

Example:

> User wants a real-time price feed for ETH/USDC on Uniswap V3. They will use it in a trading bot (assumed). Latency target is sub-second (assumed).

The user can strike any "(assumed)" they don't agree with.

## 9. 4-Point Self-Review

Run this checklist before persisting each major update:

1. **Placeholder scan** — any "TBD", "TODO", unfilled blanks? Either fill or move to `# Unknowns`.
2. **Internal consistency** — contradictions? Does `# Clarified Intent` agree with `# Decisions`?
3. **Scope check** — does this intent's clarification and decision space benefit from independent management? If yes, propose a child intent. If no, keep as is. Do not split just because the intent is large, cross-domain, or will produce multiple Specs.
4. **Ambiguity check** — could any sentence be interpreted two different ways? If yes, pick one and make it explicit.

Fix inline. Do not hand a half-baked intent to the user or to a Spec Agent.

## 10. Validate Understanding

After the first round (and whenever major new info arrives), write a one-paragraph restatement of the clarified intent into `# Clarified Intent` and ask the user to confirm or correct. This is the cheapest way to catch misunderstanding before it propagates.

## 11. Scope Boundaries

- **Do not propose solutions.** Stay at goal / scope / constraint level. The Spec Agent handles solution design.
- **Do not start Spec writing or implementation.**
- **Do not pad with speculative edge cases** the user didn't raise. If the user is okay with an undefined edge, leave it in `# Unknowns`.
- **Do not re-ask settled questions.** `# Decisions` is the source of truth.

## 12. Refinement Hints

During clarification, if a sub-goal surfaces, apply the **user-objective test** (see SKILL.md §21): is it a user-valued outcome the owner can independently prioritize, revise, accept, defer, or remove? If yes, and it has its own decision space and meaningful benefit from independent management, you may suggest the user run `/intent refine <id>` to evaluate a split. If the sub-goal is a system capability or technical responsibility, do not propose a split — let Spec or Architecture handle it. Do not interrupt ordinary clarification, and do not propose splitting in every round. A large cross-domain intent that is already clear does not need to be split just because Specs will eventually multiply.

## 13. Stop Conditions

Stop asking when:

- The frontier is empty.
- The user says stop.
- 5-question quota is reached; defer the rest.
- Remaining questions are low-impact (impact × uncertainty below threshold).
- The user has reached fatigue — defer remaining items and let the Spec Agent handle them.

## 14. Lightweight Override

For one-line or trivially clear requests, do not run the full taxonomy. Skip directly to:

- A one-paragraph `# Clarified Intent` restatement.
- One round of frontier questions (≤3).
- Persist and stop.

The full methodology is for genuinely ambiguous or large intents. Default to lightweight.
