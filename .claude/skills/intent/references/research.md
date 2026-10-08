# Research Methodology

Read this when verifying facts, checking API behavior, or investigating claims the user makes.

## Goal

Verify facts and surface unknowns before the downstream Spec Agent assumes them. The cost of a wrong fact compounds; the cost of an honest "unknown" is small.

## Source Priority

1. **Primary**: official docs, RFCs, source code of the library/API, the repo's own code.
2. **Secondary**: maintainer blog posts, accepted Stack Overflow answers, conference talks by authors.
3. **Tertiary**: aggregators, AI-generated content. Use only as leads — verify with primary before recording.

When in doubt, go to primary. "I read it on a blog" is not verification.

## Evidence Template

For each verified fact, record in `# Facts and Research`:

```markdown
- **Fact**: <one sentence, the minimum claim>
  **Source**: <URL or path:line in this repo>
  **Verified on**: <YYYY-MM-DD>
  **Method**: <how verified — read page X, ran command Y, inspected file Z>
  **Scope**: <what this covers and does not cover>
  **Uncertainty**: <remaining doubt, even after verification>
```

If the fact is non-trivial, move the full evidence to `research/<topic>.md` and link to it from `# Facts and Research`.

A research file is justified when:

- Multiple sources were consulted.
- Sources conflicted.
- Verification involved running code or commands.
- The fact is load-bearing for downstream Spec.

A research file is **not** justified for a single-page lookup. Keep it inline.

## Conflict Handling

When sources disagree:

- Record both, side by side, with sources and dates.
- Note which is more authoritative and why.
- If the conflict affects downstream Spec, mark the disputed fact in `# Unknowns` with a clear "must resolve before implementation" tag.

Do not pick a side silently. Do not average sources. Show the conflict.

## Unknowns

Anything that could not be verified goes in `# Unknowns`:

```markdown
- **Unknown**: <what is unknown>
  **Why it matters**: <downstream impact>
  **How to resolve**: <specific action, e.g., "read page X", "run benchmark Y">
```

`# Unknowns` is a first-class section. Do not delete items to make the doc look complete. Do not move unknowns into `# Facts and Research` to fill space.

## Hard Rules

- **No claim without a source.** "I think this is right" is not verification.
- **No fabricated URLs or API names.** If you can't cite it, don't claim it.
- **"I read it somewhere" is not verification.** Cite the page or file.
- **If you can't verify, say so** in `# Unknowns` and stop. Do not bluff through.
- **Distinguish what the user said** from what the agent independently verified. The user's claim is a fact about what the user said, not about the world.

## When to Research vs. Ask the User

Default to research when:

- The question is about external behavior (API, library, protocol, performance).
- The question is about this repo's existing code.
- The answer can be verified without the user's involvement.

Ask the user when:

- The question is about preference, taste, or values.
- The question is about proprietary / non-public context the agent cannot access.
- The question is about future intent the agent cannot infer.

When in doubt, prefer research — it costs less than asking and produces evidence.

## Verifying In-Repo Claims

For claims about this repo (file exists, function signature, behavior):

1. Use `Glob` / `Grep` to locate the relevant file.
2. `Read` it. Cite `path:line`.
3. If the claim is about runtime behavior, run the code and capture the output.
4. Record the verification command and output.

Do not paraphrase repo contents from memory. Always Read first.
