# Clarification Methodology

Read this when handling `new`, `resume`, or any clarification round within
the intent skill, and when a user decision must be asked. The load condition
is listed in `SKILL.md` §15.

## Goal

Remove the ambiguity that would change **the user's goal** — nothing more.
The clarification effort is proportional to the uncertainty of the user's
*product decisions*, not to the engineering complexity of the goal. A
five-module feature with three settled decisions needs one question; a
one-line request whose economics can be read two ways needs that question
answered before anything else happens.

Clarification is not a phase that must produce a questionnaire. It is a way
to avoid writing down something the user never meant.

## 1. The Worth-Asking Test

A question belongs to the user when a wrong answer would change the **goal,
the scope, a key constraint, or a product choice** — something only the user
can settle. Everything else is research, configuration, or a downstream
design decision.

Ask it when **all three** hold:

1. Different answers produce a materially different goal, scope, constraint,
   or product choice.
2. No evidence available to the agent settles it.
3. Waiting for the answer blocks the next meaningful step — a Spec cannot
   be written correctly without it.

If only 1 holds, record the uncertainty and let the downstream layer settle
it. If 1 and 2 hold but 3 does not, it is a **non-blocking** open question,
not a question to ask now.

## 2. Never Ask

- **What the user already said.** A stated constraint is not a question.
  Read `# Original Intent` and `# Decisions` before asking anything.
- **Engineering decisions.** Order type, retry strategy, idempotency key,
  state-machine shape, storage format, language and framework — Spec,
  Architecture, and Module Design own these.
- **Numbers that can be configured at runtime.** Threshold values,
  fee schedules, position sizes, limits — the user usually wants them
  configurable, not decided during Intent. Ask only when the *number itself
  is the business rule* the user is trying to express.
- **Facts.** "What does this API return?", "what is the current rate?" —
  look it up (`references/research.md`).
- **Edge cases the user did not raise.** If the user is comfortable leaving
  it undefined, leave it undefined downstream.
- **A question whose default is obvious and whose wrong answer would not
  change the goal.** Do not spend the user's attention on it.

## 3. Frontier Model

Model the intent as a **tree of decisions**. A question is on the frontier
when all its prerequisites are answered. Each round:

1. Compute the frontier — only questions that pass §1.
2. Ask the frontier questions in one batch (see §4).
3. Record each answer where it belongs (§5). The frontier expands.
4. Repeat until the frontier is empty, the user stops, or the remaining
   questions are non-blocking.

A question whose answer depends on another still-open question belongs to a
later round. A fact that is still being researched does not block the whole
frontier: ask the other questions now.

**Do not split the intent because the request is complex, spans several
modules, or will produce several Specs.** A split is a boundary decision
(`SKILL.md` §8.1), not a reaction to workload.

## 4. How Many, and How

- **Prefer one to three questions.** The cap is **five per pass**; a
  genuine goal-level ambiguity rarely needs more than three.
- Ask in one batch, ordered by impact. Split the batch only when the user
  is visibly saturated.
- Every question is a real interrogative, has a one-sentence "why it
  matters", and offers 2–4 mutually exclusive options when the choice is
  clear — or a free-form answer when the user's own framing is needed.
- Offer a recommendation only when evidence supports one, and state the
  assumption and its reason. Do not phrase an unresolved product choice so
  that agreement is the easiest answer.
- Do not re-ask a question already answered; check `# Decisions` and
  `# Original Intent` first.

## 5. Where the Answer Goes

| The answer is | Record it as |
|---|---|
| The outcome the user wants | A goal in `# Clarified Intent` |
| A limit the user set | A constraint in `# Constraints and Success Criteria` |
| A choice the user made | A decision in `# Decisions`, labeled `CONFIRMED` |
| Something the agent inferred | `## Inferred, Not Authorized` — never a decision. If it needs an answer, it is one non-blocking question in `# Unknowns` instead, not both |
| A choice that is still open | `# Unknowns` (blocking or non-blocking) |

Record each answer **once**. If the user's answer is already visible in the
goal or the constraint, do not also write it as a decision.

## 6. Facts vs. Decisions

**Facts are the agent's job. Decisions are the user's.** Before asking
anything, ask: "Could I find this out by reading code, docs, or running a
search?" If yes, dispatch the search and use the result — do not hand the
user a research task. A fact that cannot be established is recorded as an
unknown with a resolution path, not as a question for the user.

## 7. Do Not Introduce a Business Model

The agent's job is to capture the user's economics, not to improve them.
When a request contains two readings with materially different business
meaning — "keep my position size unchanged" versus "open a new offsetting
position", "arbitrage the spread" versus "arbitrage the fee difference" —
record the request as stated, name the two readings, and ask which one is
meant. Do not merge them, do not pick the more elegant one, and do not write
a blended version into the goal.

## 8. Validate Understanding

After the first round, and whenever major new information arrives, restate
the goal in the user's own language inside `# Clarified Intent` and ask for
confirmation or correction. This is the cheapest way to catch a
misunderstanding before it propagates into a Spec.

## 9. Stop Conditions

Stop asking when:

- the frontier is empty;
- the user says stop;
- the pass quota is reached — the rest go to `# Unknowns` as non-blocking
  unless they change the goal, in which case name the one that does;
- the remaining questions are non-blocking;
- the user is clearly saturated — record what is open and hand it on.

## 10. Lightweight Path

For a one-line or clearly-scoped request, skip the taxonomy:

1. Write `# Original Intent` verbatim.
2. Restate the goal in one or two sentences in `# Clarified Intent`.
3. Ask at most one question, only if §1 holds.
4. Persist and stop.

## 11. Self-Review Before Persisting

Run the semantic consistency check in `SKILL.md` §13.4. It replaces a
separate review pass: placeholder scan, contradiction against the original
request, provenance of every claim, goal-versus-constraint coherence,
expectation written as guarantee, duplicate entries, early design
decisions, and any key term that still has two readings. Fix inline; do not
hand a half-baked intent to the user or to a Spec Agent.
