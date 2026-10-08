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
| `feedback` | `<intent-id>` (optional: source path or ID) | Receive and route upstream feedback from Spec / Architecture / Module |
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
| "spec found an issue with INT-001", "architecture needs INT-002 changed" | `feedback` |
| "I need to change X but it's archived" | `reopen` (after confirmation, with warning) |
| "does X still make sense?", "is Y feasible?" | Add to `# Evaluation` and `# Unknowns` |

**Modification is the default, not creation.** Before creating a new intent, search for an existing one whose goal is still the same. Only create new when the goal is genuinely independent.

## 4. Subcommand: `new <title or description>`

1. Read `# Original Intent` from the user's raw input. Verbatim, no paraphrase.
2. **Before creating**, scan existing intents. Classify the new goal into one of four paths:
   - **A — Modify existing.** The new content extends the same user-objective as an existing intent. Update in place.
   - **B — Create child.** The new content is a user-valued sub-goal with its own outcome (passes the user-objective test, see §21) and independent priority. Make it a child of the closest parent.
   - **C — Create independent.** The new content is a separate user-objective that should not be subordinate to any existing intent. Create a new top-level intent.
   - **D — Reconcile.** The new content has material semantic overlap, shared abstraction, or constraint conflict with existing intents. Suggest `/intent-reconcile <new-id> <existing-id>`.
3. **Confirm the path with the user before creating or modifying.** Same product / system does not mean same intent. A clearly independent user goal becomes a new intent (top-level or child), not a merge.
4. **Technical capabilities are not independent intents.** RPC access, DB schema design, API definitions, and specific algorithms are not user goals. If the request is primarily about these, surface that and route to Spec / Architecture / Module Design instead of creating an intent. If the user wants a capability to support their goal, capture the goal and let downstream decide the technical means.
5. After user confirms the path, follow the appropriate flow:
   - **A** → modify the existing intent in place. Preserve ID. Use the modification flow (§15).
   - **B** → either invoke `/intent refine` on the parent to formally split, or directly create a child with the parent's confirmation. New child gets a fresh ID with `parent: <existing-id>`.
   - **C** → continue to step 6 (ID generation, file creation, clarification).
   - **D** → print the `/intent-reconcile` command as text for the user to run. Do not pretend to invoke the reconcile skill from this skill.
6. For path C, generate ID: scan `docs/intents/INT-*/INTENT.md`, find max `INT-NNN`, take `INT-` + (max+1) zero-padded to 3 digits. If user provided an explicit ID, use it (after confirming no conflict).
7. Create `docs/intents/INT-NNN/INTENT.md` with `status: active`. Create `docs/intents/` if missing.
8. Fill the frontmatter (`id`, `title`, `status`, `created`, `updated`). Leave `parent`, `related`, `impact_scope` empty unless the user named them.
9. Fill `# Original Intent` verbatim. Other sections start as `_TBD_`.
10. Begin clarification. Read `references/clarification.md` for the methodology.
11. Persist after every meaningful clarification or research result. Don't batch at the end.

A duplicate ID is never overwritten. If collision, ask the user to disambiguate.

## 5. Subcommand: `list`

1. `Glob` `docs/intents/INT-*/INTENT.md`.
2. Read frontmatter of each.
3. Print a compact table. `active` first, then `archived`. Columns: `id`, `title`, `status`, `parent`, `related` (count), `updated`.

## 6. Subcommand: `show <id>`

Read and print the full `INTENT.md`. No editing. If the ID is ambiguous (partial match returns multiple), list candidates and ask.

## 7. Subcommand: `refine <id> [topic]`

Assess whether to modify the existing intent, split it into a child intent, or keep it as-is. Refinement is **boundary-driven, not size-driven** — splitting is only justified when a sub-goal has its own outcome and decision space (see §19 hard rules).

1. Load the target `INTENT.md`. If `$topic` is given, focus the assessment on that topic within the intent.
2. Read the parent intent (if any) and directly related intents for context.
3. Check for existing children to avoid duplication. `Glob docs/intents/INT-*/INTENT.md` and look for `parent: <id>` in their frontmatter.
4. Evaluate three refinement conditions:
   - **Independent outcome** — is there a *user-valued* outcome (something the owner can independently prioritize, revise, accept, defer, or remove) that can be stated as its own goal? A system capability or technical responsibility does not qualify — those belong to Spec and Architecture respectively (see §21).
   - **Independent decision space** — does it have its own key user decisions, fact-investigation scope, constraints, unknowns, or trade-offs?
   - **Meaningful benefit** — would splitting clearly improve clarification, decision boundaries, context, or downstream traceability?
5. Choose one of three outcomes:
   - **Modify** — extend the existing intent. No new file. Preserve ID. Update `# Resume Notes`.
   - **Create child** — propose a new intent with `parent: <id>`. Show the proposed split. Get user confirmation before creating.
   - **Keep** — explain why no split is needed. No file changes.
6. On "Create child", classify by impact on the parent's authoritative content:
   - **Case A — Create child without changing parent meaning.** No new sub-goal, constraint, or decision is added to the parent; only its `Relationships and Impact` may record the new child. The parent intent is **not** reopened, even if `archived`. The new child is `active`.
   - **Case B — Materially change parent intent.** Adding, removing, or materially changing the parent's goal, scope, constraints, success criteria, or confirmed decisions. **Reopen the parent first** with user confirmation (whether it is `archived` or `active`), then apply the change.
   - **Case C — Move existing content from parent to child.** A goal, constraint, or decision is relocated from the parent to the new child. This is treated as a material change to the parent: **reopen first** if the parent is `archived`. Preserve the original wording in the parent's `# Resume Notes` (or a migration map), and update any downstream references so old pointers still resolve to either the new location or the historical record.
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
4. **Archive does not require downstream Spec to be complete.** Intent is considered ready for archive when the user confirms the goal, scope, and decisions are sufficiently clarified. Spec, Architecture, and Module work may proceed in parallel or later. If a downstream artifact later finds a real upstream problem, it can route the issue back through `/intent feedback`, which may lead to `reopen` — but that is not automatic.
5. On confirmation: set `status: archived`, update `updated`. Append a short note to `# Resume Notes` (e.g., "Archived after N clarification rounds; X decisions recorded").
6. Tell the user: archived intents can be reopened with `reopen`, and can also receive `feedback` without reopening.

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

## 12. Subcommand: `feedback <intent-id> [source]`

Receive upstream feedback from Spec, Architecture, Module Design, or Implementation, and route the issue to the right ownership level. A short natural-language message ("spec found an issue with INT-001") is also valid feedback.

### Arguments

- `<intent-id>` — the target intent to inspect (required).
- `[source]` — file path or ID of the source artifact, e.g. `docs/specs/SPEC-002/SPEC.md`. Strongly recommended when available. If only the intent ID is given with no context, ask the user for the specific source. **Do not fabricate a source.**

### Minimal feedback contract

```yaml
source: SPEC-002
target: INT-001
target_item: INT-001/C-01      # optional
problem: >
  Existing constraint conflicts with the required behavior.
evidence:
  - INT-001/C-01
  - SPEC-002/REQ-003
requested_resolution: >
  Clarify the scope of the existing constraint.
```

Not all fields are required for every feedback. A short natural-language message with an intent ID is acceptable when the context is clear.

### Processing

1. Identify source and target.
2. Load the target `INTENT.md`. Load the source artifact by path; do not assume its contents.
3. If only an intent ID is given with no source content or context, ask the user for the specific source. Do not invent feedback.
4. Assess whether the feedback describes a real problem.
5. Determine the **ownership level**:
   - **Intent problem** — user goal ambiguity, conflicting user goals, conflicting user constraints, decisions to revisit, facts that invalidate the original user goal. **Handle here.**
   - **Spec problem** — incomplete system behavior, missing acceptance criteria, missing functional requirements. **Route to Spec.**
   - **Architecture problem** — unclear module ownership, missing cross-module capability, conflicting dependencies, unclear public contract ownership. **Route to Architecture.**
   - **Module / Implementation problem** — wrong implementation, algorithm bugs, DB design issues, code/spec mismatch. **Route back to source** for the implementer to fix.
6. If handled here, surface the proposed intent change and get user authorization before editing. A material change to an `archived` intent still requires `reopen` with confirmation (see §10).
7. If multiple intents share a semantic conflict, route to `/intent-reconcile`. Print the command as text; do not auto-invoke.
8. Record the conclusion in the target intent's `# Relationships and Impact` or `# Resume Notes`. Do not create a separate feedback file.
9. Return a result to the source owner (see format below).

### Result format

Return to the source owner:

- **Status**: `Accepted` · `Rejected` · `Redirected` (to Spec / Architecture / Module) · `Needs Owner Decision`
- **Rationale**: brief reasoning, including which ownership level applies
- **Intent changes**: list of items modified (or "none")
- **Downstream impact**: list of downstream artifacts that may need to re-check
- **Suggested next step**: what the source owner should do

These are not new intent lifecycle states. They are outcomes of a single feedback event.

If the source artifact cannot be modified from this skill (it almost always cannot, since Spec / Architecture / Module are separate Skills), return the result text for the source owner to apply. **Do not claim the source artifact was updated.**

### Archived intent

An `archived` intent can receive feedback. Feedback alone does not trigger `reopen`. Only when the assessment shows authoritative content needs material change, follow the existing `reopen` flow.

## 13. Relationships

### 13.1 `parent`

A child has exactly one parent. Parent is for "this is a sub-goal of X" — a logical ownership relationship. Setting/changing parent requires:

- The target parent must exist.
- Walking up the new parent's ancestors must not include the child (no cycle).
- An intent cannot be its own parent.
- Archived parents are allowed as a parent, but warn.

### 13.2 `related`

A loose "this affects that" link. Multiple related links allowed. Add a related link only when there is a real cross-effect, not just topical similarity.

### 13.3 `impact_scope`

What this intent touches in the project. Examples:

- Modules / files in this repo.
- Public interfaces.
- Related Specs.
- Related other intents (by id).
- Existing user-facing behavior.

`impact_scope` is not the same as `parent` or `related`. It is "what real-world things will move?" Populate it as clarification progresses. Mark unknown entries explicitly rather than fabricating module names.

## 14. INTENT.md Template

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

## 15. Modification Flow (vs Creation)

When the user asks to change an existing intent:

1. Identify which intent. Use `$id` if given; otherwise infer from context (most recently active, or the one the user is currently discussing).
2. **Confirm if the change is material** (touches goal, success criteria, or a confirmed decision). For trivial wording fixes, just edit.
3. Edit in place. Preserve the ID. Add a new entry to `# Decisions` for the change (`YYYY-MM-DD: <what changed> — <why>`).
4. Update `updated` to today.
5. If the change affects other intents (parent, related, or downstream Specs), note this in `# Relationships and Impact` and warn the user.

For an `archived` intent that needs editing, `reopen` first.

## 16. Clarification Method

Read [references/clarification.md](references/clarification.md) for the full algorithm. Summary:

- Model intent as a **frontier** of decisions. Each round, ask all questions whose prerequisites are settled.
- Each question ships with a recommended answer. Word it so "yes" accepts.
- Research is the agent's job. Ask the user only about decisions.
- Hard cap **5 questions per clarification pass** with a `## Deferred` bucket for the rest. Re-validate after every answer; replace contradicted text, do not append.
- After meaningful new info, write back a "stated vs assumed" restatement and confirm.
- Stop when the frontier is empty, the user says stop, or fatigue sets in.

## 17. Research Method

Read [references/research.md](references/research.md). Summary:

- Verify before recording. Cite the URL or repo path. Do not paraphrase repo contents from memory.
- Distinguish user-stated facts from agent-verified facts.
- A research file in `research/<topic>.md` is justified when multiple sources were consulted, sources conflicted, verification involved running code, or the fact is load-bearing for downstream Spec.
- Single-page lookups stay inline. Don't create files for one fact.

## 18. Hand-off

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

## 19. Hard Rules

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
19. **Don't reconcile inline.** When a semantic overlap, shared abstraction, or inherited-constraint conflict is detected, do not run the full reconciliation in this skill. Surface the candidate and point the user to `/intent-reconcile ID1 ID2`. See §20.
20. **User-objective test.** Before creating a child Intent, ask: does the candidate represent a distinct user-valued outcome that the owner can independently prioritize, revise, accept, defer, or remove? If no, do not create a child — the candidate is system behavior (Spec's job) or technical responsibility (Architecture's job). See §21.
21. **Confirm when redirecting new to modify.** When `/intent new` is processed, if the analysis suggests modifying an existing intent, surface the path analysis and wait for explicit user confirmation. Never silently redirect `new` to `modify` of an existing intent.
22. **Technical capabilities are not new intents.** RPC access, DB schema design, API definitions, and specific algorithms are not user goals. They belong to Spec, Architecture, or Module Design. Do not create intents for them.
23. **Material change to archived intent requires reopen.** Material changes (Case B / Case C in §7) to an `archived` intent must follow the `reopen` flow with user confirmation. Case A is exempt.
24. **Stable item IDs are immutable on wording.** Reformatting or rewording an item does not change its `INT-NNN/X-NN` ID. Reassigning an ID to a different meaning is forbidden.
25. **No auto-archive, no auto-reopen, no auto-modify.** Never change intent status or authoritative content without explicit user authorization, even if a downstream feedback suggests it.
26. **Don't claim sync that didn't happen.** If a downstream artifact cannot be modified from this skill (almost always), return a clear result for its owner to apply. Do not claim the artifact was updated.

## 20. Lightweight Reconcile Trigger

During `new`, material `modify`, or `refine`, perform a lightweight semantic check against existing intents. Ask one question:

> Does this change expose a material semantic overlap, shared abstraction, inherited-constraint conflict, or incompatible goal with an existing intent?

**If no** — continue the normal flow.

**If yes** — surface the candidate intent(s) and the reason in one or two sentences. Suggest the user run `/intent-reconcile <new-id> <existing-id>` to compare. Print the command as text; do not pretend to invoke the reconcile skill from this skill. If the reconcile skill is available in the current environment and the user explicitly agrees, the model may call it via the native Skill tool — but only with explicit user authorization to start reconciliation.

Domain similarity (same tech stack, same data source) is not sufficient on its own. Only trigger on a real semantic overlap, conflict, or shared abstraction.

Do not loop. At most one reconcile suggestion per change. Further iterations require explicit user request.

## 21. Intent Boundary and Decomposition

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

## 22. Stable Item IDs

Important goals, constraints, and decisions may be assigned **stable item IDs** so downstream artifacts (Spec, Architecture, Module) can refer to them precisely:

```text
INT-001/G-01  Goal
INT-001/C-01  Constraint
INT-001/D-01  Decision
```

### Rules

- The intent ID (`INT-NNN`) is immutable.
- Item IDs are only assigned to content with real traceability value — important goals, hard constraints, confirmed decisions. Plain explanation, examples, and minor text do not need IDs.
- Assigned IDs **cannot be reassigned** to a different meaning.
- Wording-only edits do not change item IDs. The same `INT-001/C-01` still refers to the same constraint after a paraphrase.
- If the meaning materially changes, preserve the original entry as a historical record (e.g., "D-01 superseded by D-05 on YYYY-MM-DD — original: …") and add the new entry under a new ID. Do not silently reuse the old ID for a different meaning.
- When an item moves to a child intent, record the migration (e.g., "moved to INT-002/C-01 on YYYY-MM-DD" in the parent's `# Resume Notes`, with a reciprocal pointer in the child).
- Do not invent IDs that do not yet exist. Do not retrofit IDs to existing intents in bulk — assign them when a downstream artifact needs to reference them.
- If a downstream reference exists without an item ID, it may fall back to `INT-NNN` + file + section location. Not every intent must use item IDs.

### In `INTENT.md`

Use bold item IDs followed by content, e.g.:

```markdown
# Constraints and Success Criteria

- **C-01**: 历史回测不得使用未来数据。
- **C-02**: 资产净值必须按统一计价基准计算。

# Decisions

- **D-01** (2026-10-08): 支持策略驱动的仓位调整。
```

### Downstream reference format

A Spec or Architecture document can reference by `INT-NNN/C-01` (or `INT-NNN/G-01`, `INT-NNN/D-01`). When this skill sees a downstream change, it can locate the exact item and assess whether the change is material.
