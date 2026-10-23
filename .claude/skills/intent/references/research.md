# Research Methodology

Read this when a fact must be established, a claim verified, or conflicting
sources reconciled. The load condition is listed in `SKILL.md` §6.

## Goal

Establish the few external facts that decide whether the user's goal is
achievable, and keep everything else out of Intent. The cost of a wrong fact
compounds; the cost of an honest "unknown" is small.

## 1. Source Priority

1. **Primary**: official docs, RFCs, source code of the library/API, the
   repo's own code, the vendor's own dashboard.
2. **Secondary**: maintainer blog posts, accepted Stack Overflow answers,
   conference talks by authors.
3. **Tertiary**: aggregators, AI-generated content. Use only as leads —
   verify with primary before recording.

When in doubt, go to primary. "I read it on a blog" is not verification.

## 2. What Enters Intent

A fact belongs in `# Facts and Research` only when it does one of these:

1. It decides whether the goal is **achievable as stated** (the fee level
   makes the strategy unprofitable; the API does not expose the needed
   field).
2. It **underpins a decision the user made** (the user chose a threshold
   because of a known fee structure).
3. It **changes the meaning of a stated constraint** (the exchange's
   withdrawal window contradicts "funds are available immediately").

Everything else — API parameter lists, endpoint inventories, order types,
snapshot tables, order-book mechanics, SDK details — is **research**, not
Intent content. Keep it in `research/<topic>.md` (or in the Spec that needs
it) and reference the file when it matters. If no downstream layer needs it
yet, it does not need to exist yet.

**Dynamic parameters** (prices, fee rates, funding rates, balances) are
snapshots, not durable facts. Record one in Intent only when it decided a
user question, and then record it with its date and its scope. Never write a
snapshot as a standing constraint.

## 3. Evidence Template

For each fact that does enter Intent:

```markdown
- **Fact**: <one sentence, the minimum claim>
  **Source**: <URL or path:line in this repo>
  **Verified on**: <YYYY-MM-DD>
  **Scope**: <what this covers and does not cover — for a claim of absence
    or completeness, name the searched range>
  **Uncertainty**: <remaining doubt, even after verification>
```

The scope rule is the same one the Spec layer applies — see
`.claude/skills/spec/references/fact-verification.md` §2.1.

If the fact is non-trivial, move the full evidence to
`research/<topic>.md` and link to it from `# Facts and Research`.

A research file is justified when multiple sources were consulted, sources
conflicted, verification involved running code, or the fact is load-bearing
for downstream work. A research file is **not** justified for a single-page
lookup — keep it inline.

## 4. Consistency Between Facts and Conclusions

A recorded fact and a recorded conclusion must not contradict each other.
This is the most common way an Intent loses the user's trust: a fact says
"negative funding is paid by shorts to longs" and an evaluation says
"negative funding favours the perpetual short" — one of them is wrong.

When a new fact contradicts something already written:

1. Re-verify against the primary source.
2. Correct the **conclusion** that was wrong — the fact usually wins, but
   not automatically; check the reasoning too.
3. Record the correction with its reason, so the history stays traceable.
4. If the corrected fact changes the meaning of the user's goal, raise it
   with the user instead of rewriting the goal.

## 5. Expectation, Cost, and Realized Outcome

Keep four things apart when the goal is about money or performance:

| Concept | Meaning |
|---|---|
| Expected outcome | What the user hopes for (an opportunity to profit) |
| Execution cost | What it costs to execute (fees, spread, slippage) |
| Realized outcome | What actually happened (a filled trade's P&L) |
| External uncertainty | What is unknown (future funding rates, market moves) |

A user's "I want to make money" belongs to the first row. Converting it
into "every executed trade must be profitable" invents a guarantee the
system cannot make, and it turns a desired outcome into an acceptance
criterion that downstream layers cannot satisfy. Record the expected
outcome, the cost factors, and the uncertainty; leave the realized outcome
to the Spec and Implementation layers.

## 6. Conflict Handling

When sources disagree:

- Record both, side by side, with sources and dates.
- Note which is more authoritative and why.
- If the conflict affects the goal, mark it in `# Unknowns` as blocking.

Before recording, also check the project's other recorded facts — other
Intents' research, Spec research, project evidence notes — for a record
that contradicts this one. A contradiction between two records is settled by
re-verification against the primary source, not by trusting the newer
document. Until it is settled, the fact stays unverified and the items that
cite it are pending revalidation.

Do not pick a side silently. Do not average sources. Show the conflict.

## 7. User Claims vs. Verified Facts

A claim the user makes about the world is a **fact about what the user
said**, not a fact about the world. If the user asserts a load-bearing
capability, verify it independently before recording it as a fact. If
verification fails, record the user's assertion as an assumption in the
goal or constraint, and put the verification gap in `# Unknowns`.

## 8. Unknowns

Anything that could not be verified goes to `# Unknowns`:

```markdown
## Blocking

- **Question**: <what is unknown>
  **Why it matters**: <what it changes in the goal, scope, or a constraint>
  **Owner**: user

## Non-blocking

- **Question**: <what is unknown>
  **Resolve in**: <Spec / Configuration / Implementation>
```

`# Unknowns` is a first-class section. Do not delete items to make the
document look complete, and do not move unknowns into `# Facts and
Research` to fill space. Do not record the same uncertainty in two places —
it goes here once.

## 9. Hard Rules

- **No claim without a source.** "I think this is right" is not verification.
- **No fabricated URLs or API names.** If you can't cite it, don't claim it.
- **"I read it somewhere" is not verification.** Cite the page or file.
- **If you can't verify, say so** in `# Unknowns` and stop. Do not bluff.
- **Distinguish what the user said** from what the agent independently
  verified.
- **Never leave a fact and a conclusion in contradiction** (§4).

## 10. When to Research vs. Ask the User

Default to research when the question is about external behavior (API,
library, protocol, performance) or about this repo's existing code, and the
answer can be verified without the user.

Ask the user when the question is about preference, taste, or values; about
proprietary context the agent cannot access; or about future intent the
agent cannot infer.

When in doubt, prefer research — it costs less than asking and produces
evidence.

## 11. Verifying In-Repo Claims

For claims about this repo (file exists, function signature, behavior):

1. Use `Glob` / `Grep` to locate the relevant file.
2. `Read` it. Cite `path:line`.
3. If the claim is about runtime behavior, run the code and capture the
   output.
4. Record the verification command and output.

Do not paraphrase repo contents from memory. Always Read first.

## 12. Research Quota

Research is not unlimited. If verification requires a long chain of lookups
(more than ~3–4 web fetches or repo sweeps for a single fact), stop and:

- record what was found so far;
- move the rest to `# Unknowns` as **non-blocking** with a concrete
  resolution path;
- note the partial answer where it changes the goal's feasibility.

The quota never converts into a research task for the user. The downstream
Spec Agent can pick up the unresolved research with the full quota
available.
