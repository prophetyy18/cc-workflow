---
name: intent
description: Capture, clarify, persist, and evolve user Intent. Turns rough goals into a structured INTENT.md that downstream Spec Agents can read. Use when the user wants to start, modify, resume, link, archive, or review an intent. Also use when the user says "I want to build X", "let's plan Y", "create a new intent for Z", or asks to clarify, scope, or refine an existing intent.
allowed-tools: Read, Edit, Write, Glob, Grep, Bash(date*), Bash(mkdir*), WebFetch, WebSearch
---

# Intent Skill

Lightweight intent management. Each intent is a small folder with one `INTENT.md`. The skill is a single, focused workflow: understand → clarify → record → research → hand off. It does not design solutions, write code, or run specs.

## 1. Identity & Storage

Every intent has a stable ID `INT-NNN` (3-digit zero-padded). IDs are **immutable** — they do not change when the title, parent, or scope changes. Re-numbering is not supported; create a new intent if a re-number is truly needed.

Storage layout (flat, **no nesting for parent/child**):

```text
docs/intents/
├── INT-001/
│   ├── INTENT.md      (required)
│   └── research/      (optional, only when deep research was done)
│       └── <topic>.md
├── INT-002/
│   └── INTENT.md
└── ...
```

Discover all intents with `Glob` for `docs/intents/INT-*/INTENT.md`. The `id` field in frontmatter is the source of truth.

## 2. Subcommand Routing

Read `$ARGUMENTS`. Split on whitespace: first token is the subcommand, the rest is the target. The target is taken as a single string with original spacing preserved for `new` (titles can have spaces). For other subcommands, the target is a single ID or empty.

| Subcommand | Target | Behavior |
|---|---|---|
| (empty) or `help` | — | Show this help |
| `new` | `<title or description>` (rest of args) | Create a new intent, begin clarifying |
| `list` | — | List all intents grouped by status |
| `show` | `<id>` | Print the full `INTENT.md` |
| `refine` | `<id>` or `<id> <topic>` | Assess whether to modify, split into a child, or keep an existing intent |
| `resume` | `<id>` | Continue work on an existing intent |
| `archive` | `<id>` | Finalize and mark as archived (after user confirmation) |
| `reopen` | `<id>` | Re-open an archived intent (warns about downstream impact) |
| `tree` | — | Show parent / child / related hierarchy |

If the subcommand is unknown, do not guess. Show help and stop. Natural-language triggers (see §3) are also valid — they route to the same subcommand.

## 3. Natural-Language Operations

Users do not have to know the subcommand names. The model routes these intents:

| User intent (paraphrased) | Action |
|---|---|
| "I want to build X", "plan Y", "let's do Z" | If no existing intent matches → `new`; if one does → modify it |
| "update INT-NNN to add …", "change the goal of …" | Modify the named intent (or the only active one) |
| "make this a sub-intent of INT-002" | Set `parent` on the current intent |
| "link INT-001 and INT-003", "X is related to Y" | Add to `related` on both |
| "what's the status of INT-002?", "show me X" | `show` |
| "list everything", "what intents do we have?" | `list` |
| "show the hierarchy", "how are these related?" | `tree` |
| "is INT-001 too big?", "should I split this?", "把 X 拆成子 Intent" | `refine` |
| "we're done with X", "archive INT-002" | `archive` (after confirmation) |
| "I need to change X but it's archived" | `reopen` (after confirmation, with warning) |
| "does X still make sense?", "is Y feasible?" | Add to `# Evaluation` and `# Unknowns` |

**Modification is the default, not creation.** Before creating a new intent, search for an existing one whose goal is still the same. Only create new when the goal is genuinely independent.

## 4. Subcommand: `new <title or description>`

1. Read `# Original Intent` from the user's raw input. Verbatim, no paraphrase.
2. **Before creating**, scan existing intents. If a close match exists, ask the user: "This looks similar to INT-XXX. Modify it, or create a new one?"
3. Generate ID: scan `docs/intents/INT-*/INTENT.md`, find max `INT-NNN`, take `INT-` + (max+1) zero-padded to 3 digits. If user provided an explicit ID, use it (after confirming no conflict).
4. Create `docs/intents/INT-NNN/INTENT.md` with `status: active`. Create `docs/intents/` if missing.
5. Fill the frontmatter (`id`, `title`, `status`, `created`, `updated`). Leave `parent`, `related`, `impact_scope` empty unless the user named them.
6. Fill `# Original Intent` verbatim. Other sections start as `_TBD_`.
7. Begin clarification. Read `references/clarification.md` for the methodology.
8. Persist after every meaningful clarification or research result. Don't batch at the end.

A duplicate ID is never overwritten. If collision, ask the user to disambiguate.

## 5. Subcommand: `list`

1. `Glob` `docs/intents/INT-*/INTENT.md`.
2. Read frontmatter of each.
3. Print a compact table. `active` first, then `archived`. Columns: `id`, `title`, `status`, `parent`, `related` (count), `updated`.

## 6. Subcommand: `show <id>`

Read and print the full `INTENT.md`. No editing. If the ID is ambiguous (partial match returns multiple), list candidates and ask.

## 7. Subcommand: `refine <id> [topic]`

Assess whether to modify the existing intent, split it into a child intent, or keep it as-is. Refinement is **boundary-driven, not size-driven** — splitting is only justified when a sub-goal has its own outcome and decision space (see §18 hard rules).

1. Load the target `INTENT.md`. If `$topic` is given, focus the assessment on that topic within the intent.
2. Read the parent intent (if any) and directly related intents for context.
3. Check for existing children to avoid duplication. `Glob docs/intents/INT-*/INTENT.md` and look for `parent: <id>` in their frontmatter.
4. Evaluate three refinement conditions:
   - **Independent outcome** — is there a *user-valued* outcome (something the owner can independently prioritize, revise, accept, defer, or remove) that can be stated as its own goal? A system capability or technical responsibility does not qualify — those belong to Spec and Architecture respectively (see §20).
   - **Independent decision space** — does it have its own key user decisions, fact-investigation scope, constraints, unknowns, or trade-offs?
   - **Meaningful benefit** — would splitting clearly improve clarification, decision boundaries, context, or downstream traceability?
5. Choose one of three outcomes:
   - **Modify** — extend the existing intent. No new file. Preserve ID. Update `# Resume Notes`.
   - **Create child** — propose a new intent with `parent: <id>`. Show the proposed split. Get user confirmation before creating.
   - **Keep** — explain why no split is needed. No file changes.
6. On "Create child":
   - If the parent is `archived`, that is fine. The parent stays archived. The new child is `active`.
   - Create the new intent with the next available `INT-NNN`.
   - Move the relevant sub-goal, decisions, facts, and unknowns to the child. Reference (do not duplicate) the parent's global constraints.
   - In the parent, replace the moved content with a pointer to the child. **Do not silently delete** items that may be cited by downstream Specs.
   - Record the split in both intents' `# Resume Notes` and `# Relationships and Impact`.
   - Re-validate relationships (no cycles, all refs resolve, parent unchanged unless explicitly edited).
7. On "Modify" or "Keep": just update `# Resume Notes`.

If a sub-intent already covers the candidate topic, surface the existing one and ask whether to modify it instead. Do not create duplicates. Do not split a large but clear intent just because it is large, cross-domain, or will produce multiple Specs.

## 8. Subcommand: `resume <id>`

1. Load `INTENT.md`.
2. Read `# Resume Notes` to see where the last session left off.
3. Read `# Decisions` first. **Do not re-ask answered questions.**
4. Continue clarification or research from the open frontier.
5. Update `# Resume Notes` at the end of the session.

If the ID is partial and exactly one intent matches, proceed. If multiple match, list and ask.

## 9. Subcommand: `archive <id>`

1. Load `INTENT.md`.
2. Render a final summary: clarified intent, constraints, decisions, facts, unknowns, spec input.
3. **Confirm with the user explicitly.** Never archive without explicit confirmation.
4. On confirmation: set `status: archived`, update `updated`. Append a short note to `# Resume Notes` (e.g., "Archived after N clarification rounds; X decisions recorded").
5. Tell the user: archived intents can be reopened with `reopen`.

## 10. Subcommand: `reopen <id>`

1. Confirm with the user. Warn that any downstream Spec may have been written against the archived version.
2. Set `status: active`, update `updated`.
3. Append a note to `# Resume Notes` explaining why it was reopened. Optionally add a `# Spec Impact` reminder: which downstream Specs may need to be re-checked.

## 11. Subcommand: `tree`

Walk parent/related links across all intents. Print a hierarchy:

```text
INT-001  LP backtest system        [active]
├── INT-002  Historical data        [active, parent=INT-001]
├── INT-003  Replay engine          [active, parent=INT-001]
│   └── (no children)
└── INT-004  Strategy evaluation    [active, parent=INT-001, related=INT-003]

INT-005  Dashboard                 [active]
└── (no parent, related=INT-001, INT-003)

INT-006  Old prototype             [archived]
```

Orphans (no parent) are roots. `related` is shown in parentheses, not as a tree edge. Detect and report cycles, self-parent, and missing-parent references as warnings.

## 12. Relationships

### 11.1 `parent`

A child has exactly one parent. Parent is for "this is a sub-goal of X" — a logical ownership relationship. Setting/changing parent requires:

- The target parent must exist.
- Walking up the new parent's ancestors must not include the child (no cycle).
- An intent cannot be its own parent.
- Archived parents are allowed as a parent, but warn.

### 11.2 `related`

A loose "this affects that" link. Multiple related links allowed. Add a related link only when there is a real cross-effect, not just topical similarity.

### 11.3 `impact_scope`

What this intent touches in the project. Examples:

- Modules / files in this repo.
- Public interfaces.
- Related Specs.
- Related other intents (by id).
- Existing user-facing behavior.

`impact_scope` is not the same as `parent` or `related`. It is "what real-world things will move?" Populate it as clarification progresses. Mark unknown entries explicitly rather than fabricating module names.

## 13. INTENT.md Template

```markdown
---
id: INT-NNN
title: <short title>
status: active
parent: INT-NNN        # omit if none
related:               # omit if none
  - INT-NNN
impact_scope: []       # populate as you learn; [] is fine initially
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# Original Intent

<verbatim user input — do not paraphrase>

# Clarified Intent

<one-paragraph restatement of what the user actually wants, validated by user. If the agent's restatement has any agent-inferred assumption, label it "(assumed)".>

# Constraints and Success Criteria

<hard constraints; how we know it succeeded. Testable where possible.>

# Decisions

- YYYY-MM-DD: <decision> — <one-line context or rationale>
- YYYY-MM-DD: <decision> — …

# Facts and Research

- **Fact**: <one sentence, the minimum claim>
  **Source**: <URL or path:line in this repo>
  **Verified on**: <YYYY-MM-DD>
  **Method**: <how verified>
  **Scope**: <what this covers and does not cover>
  **Uncertainty**: <remaining doubt>

# Unknowns

- **Unknown**: <what is unknown>
  **Why it matters**: <downstream impact>
  **How to resolve**: <specific action>

# Evaluation

<agent's independent assessment: feasibility, risks, alternatives. Clearly labeled as agent opinion, NOT user requirement.>

# Relationships and Impact

<parent/child tree position; related intents; impact_scope walkthrough; downstream Specs that may consume this.>

# Spec Input

<self-contained brief for a Spec Agent with no prior context: what, why, success criteria, hard constraints, confirmed decisions, verified facts, unknowns, impact_scope, and what the Spec Agent must NOT decide on its own.>

# Resume Notes

<short status: last action, what's next, key open questions.>
```

**Omit or trim sections that don't apply.** Empty sections are fine. **Do not pad with fake content** to make the document look complete. If a section would only contain "TBD", write `_TBD_` and move on.

## 14. Modification Flow (vs Creation)

When the user asks to change an existing intent:

1. Identify which intent. Use `$id` if given; otherwise infer from context (most recently active, or the one the user is currently discussing).
2. **Confirm if the change is material** (touches goal, success criteria, or a confirmed decision). For trivial wording fixes, just edit.
3. Edit in place. Preserve the ID. Add a new entry to `# Decisions` for the change (`YYYY-MM-DD: <what changed> — <why>`).
4. Update `updated` to today.
5. If the change affects other intents (parent, related, or downstream Specs), note this in `# Relationships and Impact` and warn the user.

For an `archived` intent that needs editing, `reopen` first.

## 15. Clarification Method

Read [references/clarification.md](references/clarification.md) for the full algorithm. Summary:

- Model intent as a **frontier** of decisions. Each round, ask all questions whose prerequisites are settled.
- Each question ships with a recommended answer. Word it so "yes" accepts.
- Research is the agent's job. Ask the user only about decisions.
- Hard cap **5 questions per clarification pass** with a `## Deferred` bucket for the rest. Re-validate after every answer; replace contradicted text, do not append.
- After meaningful new info, write back a "stated vs assumed" restatement and confirm.
- Stop when the frontier is empty, the user says stop, or fatigue sets in.

## 16. Research Method

Read [references/research.md](references/research.md). Summary:

- Verify before recording. Cite the URL or repo path. Do not paraphrase repo contents from memory.
- Distinguish user-stated facts from agent-verified facts.
- A research file in `research/<topic>.md` is justified when multiple sources were consulted, sources conflicted, verification involved running code, or the fact is load-bearing for downstream Spec.
- Single-page lookups stay inline. Don't create files for one fact.

## 17. Hand-off

The skill never writes code or designs solutions. Its output is the `INTENT.md`. The `# Spec Input` section must let a Spec Agent with no prior conversation context understand:

- The user's actual goal and why.
- Success criteria and hard constraints.
- Confirmed decisions and the date they were made.
- Verified facts and their sources.
- Remaining unknowns.
- Impact scope and relationships.
- What the Spec Agent is **not** allowed to decide on its own.

A downstream Spec should cite the intents it consumes (by ID) so this skill can detect when an intent changes.

**An Intent may produce zero, one, or many Specs.** The `# Spec Input` section is the contract each consuming Spec reads; do not write it with a single specific Spec in mind. Intent hierarchy does not determine Spec decomposition — a large cross-domain Intent can directly feed multiple Specs without first being split into children.

## 18. Hard Rules

1. **Owner authority.** Never silently change user intent or constraints. If disagreeing, surface it in `# Evaluation`, not by editing the user's words.
2. **Evidence before assumption.** Facts need sources. Unverified claims go in `# Unknowns`, never in `# Facts and Research`.
3. **No fabricated requirements.** Omit empty sections. Don't pad.
4. **Modification is the default, creation is the exception.** If the underlying objective is the same, modify.
5. **Persist early, persist often.** Save `INTENT.md` after every meaningful clarification or research result. Don't wait until the end of the session.
6. **Confirm before archive.** `status: archived` only with explicit user confirmation.
7. **Confirm before reopen.** Warn about downstream Spec impact.
8. **ID is immutable.** Never re-number. Never change `id` field.
9. **Lightweight by default.** A one-line request gets a one-line clarification. Don't force the full taxonomy.
10. **Don't escape into Spec.** This skill never writes code, never proposes a solution architecture. That is the Spec Agent's job.
11. **Validate relationships.** No self-parent, no cycles, no missing-parent refs. Check on every change.
12. **Stated vs assumed split.** When restating the clarified intent, label anything the agent inferred (not the user said) as "(assumed)".
13. **Refinement is boundary-driven, not size-driven.** Do not split an intent because it is large, cross-domain, or will produce many Specs. Split only when a sub-goal has its own outcome and decision space, and the split yields meaningful benefit.
14. **Intent hierarchy does not mirror Spec decomposition or module structure.** A single intent can produce multiple Specs; multiple intents can support one Spec. The Spec skill owns that slicing, not the Intent skill.
15. **Modify is the default for refinement.** If the new content extends the existing goal, modify. Splitting requires a genuinely independent sub-goal.
16. **Preserve parent goal on split.** When creating a child, the parent's overall goal and global constraints stay on the parent. The child takes only the specific sub-goal and its own decisions.
17. **No silent deletion on split.** Items moved from parent to child must be replaced in the parent by a pointer (e.g., "see INT-XXX"). Downstream Specs that cite the original location must still resolve.
18. **Archived parents stay archived.** Creating a child of an `archived` parent does not reopen the parent. The new child is `active`.
19. **Don't reconcile inline.** When a semantic overlap, shared abstraction, or inherited-constraint conflict is detected, do not run the full reconciliation in this skill. Surface the candidate and point the user to `/intent-reconcile ID1 ID2`. See §19.
20. **User-objective test.** Before creating a child Intent, ask: does the candidate represent a distinct user-valued outcome that the owner can independently prioritize, revise, accept, defer, or remove? If no, do not create a child — the candidate is system behavior (Spec's job) or technical responsibility (Architecture's job). See §20.

## 19. Lightweight Reconcile Trigger

During `new`, material `modify`, or `refine`, perform a lightweight semantic check against existing intents. Ask one question:

> Does this change expose a material semantic overlap, shared abstraction, inherited-constraint conflict, or incompatible goal with an existing intent?

**If no** — continue the normal flow.

**If yes** — surface the candidate intent(s) and the reason in one or two sentences. Suggest the user run `/intent-reconcile <new-id> <existing-id>` to compare. Print the command as text; do not pretend to invoke the reconcile skill from this skill. If the reconcile skill is available in the current environment and the user explicitly agrees, the model may call it via the native Skill tool — but only with explicit user authorization to start reconciliation.

Domain similarity (same tech stack, same data source) is not sufficient on its own. Only trigger on a real semantic overlap, conflict, or shared abstraction.

Do not loop. At most one reconcile suggestion per change. Further iterations require explicit user request.

## 20. Intent Boundary and Decomposition

An Intent represents an independently meaningful **user objective**, not a technical capability, module, feature list, or implementation task.

### Three Layers

1. **User Objective** — a result the owner wants and can independently prioritize, revise, accept, defer, or remove. This is what an Intent captures.
2. **System Capability** — behavior required to fulfill one or more user objectives. Belongs primarily to **Spec**.
3. **Technical Responsibility** — architecture, module, interface, implementation. Belongs to **Architecture / Module Design**.

### Create a child Intent only when

- It represents a distinct user-valued outcome within the parent objective.
- The owner can meaningfully manage its scope or priority separately.
- Separate management improves clarity, evolution, or traceability.

### Do not create a child Intent merely because

- A capability has independent technical decisions.
- A module can be implemented or tested independently.
- A feature requires substantial research.
- The system uses multiple domains or technologies.
- A parent Intent produces multiple Specs.
- A document has become large.

### Routing Specific Concerns

- If the proposed separation is primarily about **system behavior** → retain the Intent; let Spec decompose capabilities.
- If the proposed separation is primarily about **module ownership, APIs, data storage, or algorithms** → defer to Architecture or Module Design.

When uncertain, compare alternative structures and explain which user objectives would actually become independently manageable.

Preserve the owner's original goals and all applicable constraints. Do not split or generalize merely to achieve a cleaner document hierarchy.
