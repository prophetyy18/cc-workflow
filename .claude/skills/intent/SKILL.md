---
name: intent
description: Capture, clarify, persist, and evolve user Intent. Turns rough goals into a structured INTENT.md that downstream Spec Agents can read. Use when the user wants to start, modify, resume, link, archive, or review an intent. Also use when the user says "I want to build X", "let's plan Y", "create a new intent for Z", or asks to clarify, scope, or refine an existing intent.
allowed-tools: Read, Edit, Write, Glob, Grep, Bash(date*), Bash(mkdir*), Bash(git*), WebFetch, WebSearch
---

# Intent Skill

Capture user objectives as authoritative `INTENT.md` documents. This file is
the entry point: **when** to act, **what** the result is, and the
**invariants** that always hold. Method lives in the references — load one
only when its trigger fires (§15).

## 1. Identity & Scope

An Intent is an independently meaningful **user objective** — a result the
owner can prioritize, revise, accept, defer, or remove on their own. Not a
technical capability, module, API, algorithm, or implementation task.

Intent owns the user's original intent, the clarified goal / scope /
constraints / decisions, confirmed decisions and verified facts, open
unknowns, intent relationships, change tracking, and a trustworthy basis for
a downstream Spec. It does not own system behavior (Spec), module
responsibility or contracts (Architecture / Module Design), or code
(Implementation), and never designs a solution.

Effort scales with the **uncertainty of user decisions and the risk of the
change**, not technical difficulty: a hard goal whose decisions are settled
needs a short clarification, not a long questionnaire.

## 2. Storage & Stable IDs

Stable ID `INT-NNN` (3-digit) in the `id` frontmatter field, the source of
truth. IDs are immutable — never changed by title, parent, or scope, never
reused.

```text
docs/intents/
├── INT-001/
│   ├── INTENT.md      (required)
│   └── research/      (optional, only when deep research was done)
└── INT-002/
    └── INTENT.md
```

Flat, no nesting for parent/child. Discover with `Glob docs/intents/INT-*/INTENT.md`.
New ID = highest existing + 1, zero-padded. A duplicate ID is never
overwritten — ask the user to disambiguate.

## 3. Command Routing

Read `$ARGUMENTS`; the first token is the subcommand, the rest is the target.
For `new` the target is the whole remaining string; for other subcommands a
single ID or empty.

| Subcommand | Target | Behavior |
|---|---|---|
| (empty) or `help` | — | Show this help |
| `new` | `<title or description>` | Create an intent, then clarify (§6) |
| `list` | — | List all intents grouped by status |
| `show` | `<id>` | Print the full `INTENT.md` |
| `refine` | `<id> [topic]` | Modify, split into a child, or keep (§8) |
| `resume` | `<id>` | Continue work on an existing intent (§9) |
| `archive` | `<id>` | Finalize and mark archived after the completion gate (§10) |
| `reopen` | `<id>` | Re-open an archived intent (§9) |
| `feedback` | `<intent-id> [source]` | Route upstream feedback to its owner (§11) |
| `tree` | — | Show parent / child / related hierarchy |

Unknown subcommand: show help and stop. Do not guess.

## 4. Natural-Language Routing

| User intent | Action |
|---|---|
| "I want to build X", "plan Y" | `new`, or modify the intent that already covers it (§6) |
| "change the goal of INT-001" | Modify in place (§7) |
| "make this a sub-intent of INT-002" | Set `parent` (§12) |
| "link INT-001 and INT-003" | Add to `related` on both (§12) |
| "show me X", "what's the status of INT-002?" | `show` |
| "list everything" | `list` |
| "show the hierarchy" | `tree` |
| "is INT-001 too big?", "把 X 拆成子 Intent" | `refine` (§8) |
| "we're done with X" | `archive` after the completion gate (§10) |
| "确认，继续" / "INT-001 没问题了，继续 Spec" | `archive` + handoff — do not prompt twice (§10, §18) |
| "spec found an issue with INT-001" | `feedback` (§11) |
| "I need to change X but it's archived" | `reopen` (§9) |
| "is Y technically feasible?" | Evidence in `# Evaluation`; unresolved facts in `# Unknowns` |
| "does X still make sense?" | Ask the user — product value and priority are not engineering assessments |

## 5. Core Workflow

`Discover → Classify → Clarify → Persist → Evaluate → Handoff`

| Operation | Steps actually run |
|---|---|
| `list` | Discover only — frontmatter of every intent; print `id`, `title`, `status`, `parent`, `related` (count), `updated`, `active` first |
| `show` | Discover only — print the file, edit nothing; an ambiguous partial ID lists candidates and asks |
| `tree` | Discover only — walk `parent` / `related`; orphans are roots, `related` in parentheses, cycles / self-parent / missing parent reported as warnings |
| `new` | Discover → Classify (existing vs. new) → Clarify → Persist |
| `refine` | Discover → Classify (modify / child / keep) → Persist |
| `resume` | Discover → Persist, continuing the open frontier |
| `archive` | Discover → Evaluate (completion gate) → Persist → Handoff |
| `feedback` | Discover → Classify (ownership level) → Persist the outcome |

## 6. Creating an Intent

1. Capture `# Original Intent` from the user's raw input — verbatim.
2. Discover existing intents and classify: **Modify** (same user objective —
   keep the ID) · **Child** (a user-valued sub-goal with its own outcome and
   priority, §16) · **Independent** (a separate objective, subordinate to
   nothing) · **Reconcile** (material semantic overlap, shared abstraction,
   or constraint conflict, §19). Ask only when two plausible paths change
   confirmed product meaning or the requested identity. Same product or
   system does not mean same intent.
3. **Technical capabilities are not independent intents.** RPC access, DB
   schema design, API definitions, and specific algorithms are not user
   goals: surface that and route to Spec / Architecture / Module Design. If
   the user wants a capability to support their goal, capture the goal and
   let downstream choose the means.
4. Create the file and frontmatter (§2, §13), clarify, and persist after
   every meaningful clarification or research result — never batch to the
   end. Explain a Modify routing by naming the matched objective and the
   reused ID.

Procedure: `references/lifecycle.md` §2.

## 7. Modifying an Intent

Resolve the target (given ID, else the intent under discussion, else the
most recently active one), classify the change by impact
(`../../references/cross-layer-coordination.md` §2.5.b), then edit in place:
preserve the intent ID and every stable item ID (§17), append the change to
`# Decisions` with date and reason, update `updated`, and record the effect
on other intents or downstream Specs in `# Relationships and Impact` while
warning the user. A necessary correction determined by confirmed sources
uses the current authorization; a new product choice goes to the user. An
archived target is reopened first (§9).

Procedure: `references/lifecycle.md` §4.

## 8. Refining and Splitting (`refine`)

Refinement is **boundary-driven, not size-driven**. A split is justified
only when the candidate sub-goal has an **independent outcome** the owner
can manage on its own (§16), an **independent decision space**, and a
**meaningful benefit** for clarification, boundaries, context, or
traceability.

Outcomes: **Modify** (no new file, ID preserved) · **Create child** (explain
the independently valuable outcome) · **Keep** (explain why no split is
needed). If a sub-intent already covers the topic, surface it instead of
duplicating. Do not split a large but clear intent just because it is large,
cross-domain, or will produce multiple Specs.

A child creation is classified by its effect on the parent's authoritative
content — no parent meaning change (the parent is not reopened, even when
archived) · material change to the parent (reopen first) · content moved to
the child (reopen first, keep the original wording as history, migrate
references so old pointers still resolve).

Procedure: `references/lifecycle.md` §3.

## 9. Resuming and Reopening

`resume` — apply `../../references/change-impact.md` to changed Goal /
Constraint / Decision items and their cited downstream items (old `final` /
PASS evidence stays scoped to its old basis), read `# Resume Notes` for the
last position, read `# Decisions` first and **do not re-ask answered
questions**, continue the open frontier, then record affected IDs, owner,
and next action in `# Resume Notes`.

`reopen` — apply `../../references/cross-layer-coordination.md` §2.5.b: an
authorized goal covers a necessary correction that preserves confirmed user
meaning; ask only if the confirmed goal or a key constraint would change.
Set `status: active`, update `updated`, note why in `# Resume Notes`, then
record changed item IDs, affected Spec references, uncertain links, and the
next owner/action per `../../references/change-impact.md`. Do not infer
impact from the intent filename alone. An explicit request to change an
archived intent authorizes reopen-and-modify; stop and confirm if the change
goes beyond what the user asked for.

Procedure: `references/lifecycle.md` §6.

## 10. Archiving

1. Render the final summary: clarified intent, constraints, decisions, facts,
   unknowns, spec input.
2. **Authorization.** Apply `../../references/cross-layer-coordination.md`
   §2.5.b. A confirmed stage or an instruction to complete this goal covers
   archive once the checks pass. One explicit confirmation ("确认，继续") is
   enough — do not ask again, and do not extend that authorization to
   unrelated intents, Specs, architecture decisions, or code.
3. **Completion check** — required for the command and the natural-language
   flow, read against the saved document, not the summary:

   | Check | Pass condition |
   |---|---|
   | Goal | The original and clarified goals still describe the same thing |
   | Sequence | The confirmed operation order in `# Clarified Intent` is intact and reachable from the real starting state (`../../references/cross-layer-coordination.md` §8) |
   | Confirmed content | User-confirmed constraints and decisions are present and current |
   | Unknowns | No Blocking unknown remains — an unresolved *product choice* blocks; a recorded non-blocking unknown does not |
   | Evidence | Load-bearing facts carry a source and verification date; the traceable record of decisions and relationships is intact |
   | Currency | No `_TBD_` or stale claim is left in the current account; corrections recorded with their reason in `# Resume Notes` |
   | Feedback | Feedback received for this intent is recorded with its status — accepted is not downstream synchronization |

   Complex or high-risk intents (money, security, core data correctness,
   multi-step user path) run a deeper check. Routine cleanup needs no second
   confirmation; a changed user goal or product decision does. If the path,
   outcome, or authoritative meaning is still unclear, name the specific gap
   and keep the intent active — never pass an Intent gap downstream as if it
   were complete.
4. **Archive does not require downstream Spec to be complete.** The intent is
   ready when the user confirmed goal, scope, and decisions; Spec,
   Architecture, and Module work may follow in parallel or later. A later
   downstream finding routes back through `feedback`, which may lead to
   `reopen`; that is not automatic.
5. When authorized and the checks pass: set `status: archived`, update
   `updated`, append a short `# Resume Notes` entry, tell the user that
   `reopen` and `feedback` remain available, and hand off (§18).

Procedure and the full check list: `references/lifecycle.md` §5.

## 11. Feedback Routing

Receive feedback from Spec, Architecture, Module Design, or Implementation and
route it to the owner that can fix it.

1. Identify source and target; load the target `INTENT.md` and the source
   artifact by path. Never fabricate a source: if only an intent ID is given,
   inspect recorded feedback, Resume Notes, and relevant Git changes first,
   and ask only if the source stays unidentifiable.
2. Assess the problem, then pick the **ownership level**:

   | Level | Symptom | Route |
   |---|---|---|
   | Intent | User goal ambiguity, conflicting user goals or constraints, a decision to revisit, a fact that invalidates the original user goal | Handle here |
   | Spec | Incomplete system behavior, missing acceptance criteria or functional requirements | Route to Spec |
   | Architecture | Unclear module ownership, missing cross-module capability, conflicting dependencies, unclear contract ownership | Route to Architecture |
   | Module / Implementation | Wrong implementation, algorithm bugs, DB design, code/spec mismatch | Route back to the source |
3. Handled here: repair an internal contradiction determined by confirmed
   sources under the current authorization; a new product choice goes to the
   user; a material change to an archived intent uses `reopen` (§9). Several
   intents sharing a semantic conflict go to `/intent-reconcile` (§19) under
   the authorized goal, preserving the return point.
4. Record the conclusion in `# Relationships and Impact` or `# Resume Notes` —
   no separate feedback file, no second relationship database.
5. Return to the source owner: source, target, problem, evidence, requested
   resolution, then **Status** (`Accepted` · `Rejected` · `Redirected` ·
   `Needs Owner Decision`), **Rationale**, **Intent changes**, **Downstream
   impact**, **Suggested next step**. These are outcomes of one feedback
   event, not lifecycle states. A short natural-language message with an
   intent ID is acceptable when the context is clear. The source artifact
   usually cannot be modified from this skill — return the result text for
   its owner to apply. **Do not claim the source artifact was updated.**

Cross-layer detail — feedback contract, minimum escalation, closure
semantics — belongs to `../../references/cross-layer-coordination.md` §3, §4,
§5; load it only when the issue crosses authority layers.

Intent normally does **not** delegate to the Independent Reviewer: its
authoritative content is the user's stated goals and decisions, not a
verifiable system artifact. Self-check plus the user's confirmation is the
standard. A Targeted Resolution Verification
(`../../references/verification.md` §3) applies only when the change has
material downstream correctness implications, an authorized fix materially
changes a downstream requirement, constraint, invariant, public contract, or
load-bearing decision, and that Trigger B fires.

## 12. Relationships

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

## 13. INTENT.md Structure

The section names and order are fixed by `references/intent-template.md`
(downstream readers rely on them): `# Original Intent` · `# Clarified
Intent` · `# Constraints and Success Criteria` · `# Decisions` · `# Facts and
Research` · `# Unknowns` · `# Evaluation` · `# Relationships and Impact` ·
`# Spec Input` · `# Resume Notes`.

**One fact or decision has exactly one authoritative location.** The
canonical homes are `# Clarified Intent`, `# Constraints and Success
Criteria`, `# Decisions`, `# Facts and Research`, and `# Unknowns`. `# Spec
Input` is a handoff map that points at those sections by item ID instead of
copying them. Omit a subsection with no applicable content; never invent data
to fill the shape. Item IDs are optional (§17).

Field-level template, the single-authority table, and the placement notes
(`## Assumptions to Confirm`, engineering-only `# Evaluation`, `_TBD_`
handling) are in `references/intent-template.md` — load it when creating a
new `INTENT.md` or restructuring an existing one.

## 14. Core Invariants

| # | Invariant |
|---|---|
| 1 | **Confirmed meaning is the user's.** Never silently change a confirmed goal, constraint, decision, or the confirmed operation order. Within an authorized goal the owning layer fixes its own contradictions; that is not a second approval round. |
| 2 | **Modify before creating.** If the objective is the same, modify the existing intent and preserve its ID. Creation is the exception. |
| 3 | **A child needs independent user value** the owner can manage on its own (§16). |
| 4 | **IDs are immutable.** The intent ID is never re-numbered or reused, and a stable item ID is never reassigned to a different meaning (§17). |
| 5 | **Separate what is known from what is assumed.** Verified facts carry a source and date; unverified claims live in `# Unknowns`; agent inference is labeled `(assumed)`. A user's claim is a fact about what the user said, not a fact about the world. |
| 6 | **Keep history.** Material edits, splits, and migrations are recorded with date, old meaning, new meaning, and reason; superseded items stay traceable; downstream pointers still resolve. |
| 7 | **Stay inside the layer.** Intent does not write Specs, contracts, module designs, or code, and does not modify another layer's artifact; it returns a result for that layer's owner to apply. |
| 8 | **Never claim work that did not happen.** No claiming a downstream artifact was updated, synced, or verified when it was not. Accepted feedback is not downstream synchronization. |
| 9 | **Archive is not downstream completion.** An Intent may be archived while Spec, Architecture, and Module work are pending, and archive still requires its own completion check (§10). |
| 10 | **The user sequence stays at user level.** Intent records the ordered user-visible steps and the confirmed order; UI detail, error handling, and system state transitions belong to Spec (§18). |

## 15. Reference Loading

Load a reference only when its trigger fires. Do not read unrelated
references, and do not re-read an unchanged file in the same context.

| Reference | Load it when | Do not load it for |
|---|---|---|
| `references/clarification.md` | A user decision is unresolved and must be asked, or a clarification round resumes | `list`, `show`, `tree`; editorial edits |
| `references/research.md` | A fact must be established, a claim verified, or conflicting sources reconciled | Decisions the user owns; `list`, `show` |
| `references/lifecycle.md` | Creating, matching, splitting, archiving, reopening, or resuming an intent | `list`, `show`, `tree`; plain feedback triage |
| `references/intent-template.md` | Creating a new `INTENT.md` or restructuring an existing one | `list`, `show`; small content edits |
| `references/item-ids.md` | Assigning, renaming, moving, or citing a stable item ID | Prose edits that touch no item ID |
| `../../references/cross-layer-coordination.md` | Work or feedback crosses an authority layer, or an ownership / authorization question arises | In-Intent work that stays in this layer |
| `../../references/change-impact.md` | A changed item may affect a downstream artifact, contract, or evidence | Content that provably does not move downstream |
| `../../references/verification.md` | A formal independent-verification trigger fires, or a review result must be triaged | Ordinary capture and routine archive |

If a rule requires one of these files, read it before acting on that rule.
Never reconstruct a protocol from memory because its reference is not loaded —
load it, or state that the capability is unavailable and keep the return
point.

## 16. Intent Boundary

Three layers: **User objective** — a result the owner wants and can
independently prioritize, revise, accept, defer, or remove; this is what an
Intent captures. **System capability** — behavior required to fulfill one or
more user objectives; belongs to Spec. **Technical responsibility** —
architecture, module, interface, implementation; belongs to Architecture /
Module Design.

Create a child Intent only when it represents a distinct user-valued outcome
within the parent objective, the owner can manage its scope or priority
separately, and separate management improves clarity, evolution, or
traceability.

Do **not** create a child Intent merely because the capability has
independent technical decisions, the module can be implemented or tested
independently, the feature requires substantial research, the system spans
multiple domains or technologies, the parent produces multiple Specs, or the
document has become large.

Route a proposed separation by what it is really about: **system behavior** →
keep it in the Intent and let Spec decompose capabilities; **module
ownership, APIs, data storage, or algorithms** → defer to Architecture or
Module Design. When uncertain, compare alternative structures and explain
which user objectives would actually become independently manageable.

## 17. Stable Item IDs

Important goals, constraints, success criteria, and decisions may carry a
stable item ID so downstream artifacts can cite them exactly:

```text
INT-001/G-01  Goal
INT-001/C-01  Constraint
INT-001/S-01  Success criterion
INT-001/D-01  Decision
```

The intent ID is immutable, an assigned ID is never reassigned to a
different meaning, a wording-only edit keeps the ID, and a material change
adds a new ID while the old entry stays as history. `references/item-ids.md`
is the authority for assignment, migration, and downstream citation.

## 18. Hand-off

The skill never writes code or designs solutions. Its output is the
`INTENT.md`. A downstream Spec with no prior conversation context must find,
through `# Spec Input` and the sections it points at: the user's goal and
why, success criteria and hard constraints, confirmed decisions and their
dates, verified facts and their sources, remaining unknowns, impact scope
and relationships, and what the Spec Agent is **not** allowed to decide. A
downstream Spec cites the intents it consumes by ID, so a later intent change
can be detected.

**An Intent may produce zero, one, or many Specs.** `# Spec Input` is the
contract each consuming Spec reads — write it without one specific Spec in
mind. Intent hierarchy does not determine Spec decomposition: a large
cross-domain Intent can feed several Specs without being split into children.

`# Clarified Intent` states the user's **operation sequence from a real
starting point**: what the user knows and provides at the start, who supplies
each input, the confirmed order of operations, and what the user observes
when it works. Keep it at that level — detailed UI behavior, error and
failure handling, and system state transitions belong to Spec — but do not
drop a step or blur the order when a downstream reader could otherwise
misread the core flow. The shared rule is
`../../references/cross-layer-coordination.md` §8.

## 19. Reconcile Trigger

During `new`, a material modification, or `refine`, run one lightweight
semantic check against existing intents:

> Does this change expose a material semantic overlap, shared abstraction,
> inherited-constraint conflict, or incompatible goal with an existing intent?

**No** → continue the normal flow. **Yes** → name the candidate intents and
the reason, then use `/intent-reconcile` under the authorized goal; if
invocation is unavailable, follow that Skill's file when the tools permit,
otherwise record the missing capability and the return point. Reconciliation
that changes confirmed product meaning needs a user decision
(`../../references/cross-layer-coordination.md` §2.5.b).

Domain similarity — same tech stack, same data source — is not sufficient on
its own. Do not loop: at most one reconcile suggestion per change; further
iterations require an explicit user request.
