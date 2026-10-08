---
name: intent
description: Capture, clarify, and persist user Intent. Turns rough ideas into a structured INTENT.md that downstream Spec Agents can read. Use when the user wants to start, resume, archive, or review an intent.
allowed-tools: Read, Edit, Write, Glob, Grep, Bash(*), WebFetch, WebSearch
arguments: [subcommand, target]
---

# Intent Skill

Lightweight intent management: capture → clarify → research → archive.

## Subcommand Routing

Read `$ARGUMENTS`. The first token is the subcommand:

| Subcommand | Behavior |
|---|---|
| (empty) | Show this help |
| `help` | Show this help |
| `new <title...>` | Create a new intent, begin clarifying |
| `list` | List all intents and their status |
| `show <id>` | Show the full INTENT.md for an intent |
| `resume <id>` | Continue work on an existing intent |
| `archive <id>` | Finalize and mark as archived (after user confirmation) |
| `reopen <id>` | Re-open an archived intent (warns about downstream impact) |

If the subcommand is unknown, show help and stop. Do not guess.

## Storage Layout

```text
docs/intents/<id>/
├── INTENT.md     # required
└── research/     # optional, only when deep research was needed
    └── <topic>.md
```

**ID format**: `YYYY-MM-DD-<slug>` — generated once at creation, never changes even if title changes.

To find all intents: `Glob` for `docs/intents/*/INTENT.md`. The `id` field in frontmatter is the source of truth.

## Subcommand: `new <title...>`

1. Generate ID: today's date (`date +%Y-%m-%d`) + kebab-case slug from the title (lowercase, ASCII, hyphens).
2. Create `docs/intents/<id>/` and `INTENT.md` with `status: active`.
3. Fill `# Original Intent` with the user's raw input verbatim.
4. Begin clarification. Read `references/clarification.md` for the methodology.
5. Persist updates to `INTENT.md` after every meaningful decision or research result. Don't wait until the end.

If a duplicate id already exists (same date + slug), ask the user to disambiguate rather than overwriting.

## Subcommand: `list`

1. Glob `docs/intents/*/INTENT.md`.
2. Read frontmatter of each (`id`, `title`, `status`, `impact_scope`, `updated`).
3. Print a compact table grouped by status (`active` first, then `archived`).

## Subcommand: `show <id>`

Read and print `docs/intents/<id>/INTENT.md` in full. No editing.

## Subcommand: `resume <id>`

1. Load the existing `INTENT.md`.
2. Read `# Resume Notes` to see where the last session left off.
3. Continue clarification or research from there. **Do NOT re-ask questions already in `# Decisions`.** Check it first.
4. Update `# Resume Notes` at the end of the session.

If `id` is ambiguous (multiple candidates match), list them and ask the user to pick. If exactly one matches a partial input, proceed without re-asking.

## Subcommand: `archive <id>`

1. Read `INTENT.md`.
2. Render a final summary covering: clarified intent, constraints, decisions, facts, unknowns, spec input.
3. Confirm with the user. **Do not archive without explicit confirmation.**
4. After confirmation: set `status: archived` in the frontmatter; update `updated` date.
5. Note for the user: archived intents can be reopened with `reopen`.

## Subcommand: `reopen <id>`

1. Confirm with the user. Warn that any downstream Spec may have been written against the archived version.
2. Set `status: active` in the frontmatter; update `updated` date.
3. Append a note to `# Resume Notes` explaining why it was reopened.

## INTENT.md Template

Generate the file with this structure. **Omit or trim sections that don't apply. Do not pad with fake content.**

```markdown
---
id: <id>
title: <title>
status: active
impact_scope: []
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
---

# Original Intent

<verbatim user input — do not paraphrase>

# Clarified Intent

<one-paragraph restatement of what the user actually wants, validated by user>

# Constraints and Success Criteria

<hard constraints; how we know it succeeded>

# Decisions

<list of user-confirmed decisions, each with date and short context>

# Facts and Research

<verified facts with source links; link to files in research/ if any>

# Unknowns

<remaining uncertainties that matter to downstream Spec>

# Evaluation

<agent's independent assessment: feasibility, risks, alternatives. Clearly labeled as agent opinion, NOT user requirement.>

# Spec Input

<self-contained brief for a Spec Agent with no prior context: what, why, success criteria, hard constraints, confirmed decisions, verified facts, unknowns, impact_scope, and what the Spec Agent must NOT decide on its own.>

# Resume Notes

<short status: last action, what's next>
```

## Methodology References

Read on demand, not all at once:

- Clarification (frontier questions, ambiguity taxonomy, decision dependency): `references/clarification.md`
- Research (evidence template, source priority, fact vs assumption): `references/research.md`

## Hard Rules

1. **Owner authority**: do not silently change the user's intent or constraints. If you disagree, surface it in `# Evaluation`, not by editing the user's words.
2. **Evidence before assumption**: facts must have sources. Unverified claims go in `# Unknowns`, never in `# Facts and Research`.
3. **No fabricated requirements**: omit sections that don't apply. Empty sections are fine; fake content is not.
4. **Persist early, persist often**: write `INTENT.md` after every meaningful clarification or research result. Don't rely on chat history.
5. **Confirm before archive**: never set `status: archived` without explicit user confirmation.
6. **Lightweight by default**: simple intents get quick clarification. Don't force the full taxonomy on a one-line request.
7. **Don't escape into Spec**: this skill never writes code, never proposes a solution architecture. That is the Spec Agent's job.
