---
name: intent
description: Capture, clarify, persist, and evolve user Intent. Turns a rough request into a minimal INTENT.md — the user's goal, their constraints, the choices they made, and the choices still open — that downstream Spec Agents can read. Use when the user wants to start, modify, split, resume, link, archive, or review an intent. Also use when the user says "I want to build X", "let's plan Y", "create a new intent for Z", or asks to clarify, scope, or change an existing intent.
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

**Intent is the minimal sufficient contract between the user and everything
that follows.** It exists to keep the *meaning* of the user's goal, the
limits they set, the choices they made, and the choices still open intact
across context changes, agent switches, and hand-offs to Spec /
Architecture / Implementation. It is **not** a product specification, a
technical design, an implementation task list, a research report, an API
document, a test set, or a progress report.

Intent owns the user's original words, the desired outcome, the constraints
and boundaries, the decisions actually made, the open product choices, and
the few external facts that decide whether the goal is achievable at all. It
does not own system behavior (Spec), module responsibility or contracts
(Architecture / Module Design), implementation (Implementation), or general
technical research (Research) — and it never designs a solution.

### 1.1 Inclusion test

Put a fact into Intent's authoritative content only when at least one of
these holds:

1. Removing it could let a downstream reader **misunderstand what the user
   actually wants**.
2. Removing it could let a downstream reader **violate a limit the user
   stated**.
3. Removing it could let a downstream reader **make a product choice that is
   the user's to make**.
4. It **cannot** be settled by Spec / Architecture / Configuration on its
   own without changing the meaning of the goal.

If none holds, the content belongs to a downstream layer (§13.3) or nowhere.
Apply the test to the *semantic load* of the content, not to whether it
contains a technical word: "a single-leg fill failure must be handled" is
Intent content; "use `clientOrderId` plus a persistent event log" is not.

Effort scales with the **uncertainty of user decisions and the risk of the
change**, not with technical difficulty or the number of modules involved: a
hard goal whose product decisions are settled needs a short clarification,
not a long questionnaire.

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
| `modify` | `<id> [topic]` | Change an intent: classify the target (§8), then edit in place (§7) |
| `refine` | `<id> [topic]` | Legacy spelling of `modify` — same flow, same classification (§7) |
| `resume` | `<id>` | Continue work on an existing intent (§9) |
| `archive` | `<id>` | Finalize and mark archived after the completion gate (§10) |
| `reopen` | `<id>` | Re-open an archived intent (§9) |
| `feedback` | `<intent-id> [source]` | Route upstream feedback to its owner (§11) |
| `tree` | — | Show parent / child / related hierarchy |

Unknown subcommand: show help and stop. Do not guess.

There is **no separate refine workflow**. `refine` is a legacy spelling of
`modify`; both run the one classification rule (§8) and the one edit path
(§7). Splitting is not a command of its own — it is the **Child** outcome of
that classification, requested in ordinary language.

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
| "is INT-001 too big?" | Answer with a goal-independence assessment (§8.1, §16) — name the outcomes that could be managed separately, if any. Size, technical complexity, and Spec count are not split reasons; change nothing unless the user then asks for a split |
| "把 X 拆成子 Intent", "split INT-001" | Modify flow with the **Child** classification (§8) — create the child, update the relationship, migrate what moved (§7) |
| "we're done with X" | `archive` after the completion gate (§10) |
| "确认，继续" / "INT-001 没问题了，继续 Spec" | `archive` + handoff — do not prompt twice (§10, §18) |
| "spec found an issue with INT-001" | `feedback` (§11) |
| "I need to change X but it's archived" | `reopen` (§9) |
| "add constraint C to INT-001" | Modify in place (§7) — a confirmed constraint lands in `# Constraints and Success Criteria`, not in `# Decisions` |
| "is Y technically feasible?" | Evidence in `# Facts and Research` when it bears on the goal; otherwise Research / Spec. Unresolved facts go to `# Unknowns` (non-blocking) |
| "does X still make sense?" | Ask the user — product value and priority are not engineering assessments |

## 5. Core Workflow

`Discover → Classify → Clarify → Persist → Handoff`

| Operation | Steps actually run |
|---|---|
| `list` | Discover only — frontmatter of every intent; print `id`, `title`, `status`, `parent`, `related` (count), `updated`, `active` first |
| `show` | Discover only — print the file, edit nothing; an ambiguous partial ID lists candidates and asks |
| `tree` | Discover only — walk `parent` / `related`; orphans are roots, `related` in parentheses, cycles / self-parent / missing parent reported as warnings |
| `new` | Discover → Classify (§8) → Clarify → Persist |
| `modify` | Discover → Classify (§8) → Apply (§7) → Persist |
| `resume` | Discover → Persist, continuing the open frontier |
| `archive` | Discover → Completion gate → Persist → Handoff |
| `feedback` | Discover → Classify (ownership level) → Persist the outcome |

## 6. Creating an Intent

1. Capture `# Original Intent` from the user's raw input — verbatim, with no
   agent interpretation added.
2. Discover existing intents and classify the target with the **one**
   classification rule (§8): **Modify** · **Child** · **Independent** ·
   **Reconcile**. The same rule governs the modify flow (§7) — never
   re-derive a second test here. Ask only when two plausible paths change
   confirmed product meaning or the requested identity. Same product or
   system does not mean same intent.
3. **Technical capabilities are not independent intents** (§8.3): RPC
   access, DB schema design, API definitions, and specific algorithms are
   not user goals. If the user wants a capability to support their goal,
   capture the goal and let downstream choose the means.
4. **One goal per independent outcome** (§8). If the request mixes two
   business models that the user may not have noticed — e.g. "keep my
   position size unchanged" and "open a new delta-neutral pair" — record the
   request as stated and ask which outcome is meant. Do not merge, average,
   or silently pick one.
5. Create the file and frontmatter (§2, §13). Write `# Original Intent`
   only; other sections appear as content is confirmed. Never create a
   section as a placeholder for later.
6. Clarify (`references/clarification.md`) — ask only the questions whose
   answers change the goal, the scope, a key constraint, or a product
   choice (§13.1). Persist after every meaningful clarification or research
   result; never batch to the end.
7. Before handing over, run the semantic consistency check (§13.4).

Explain a Modify routing by naming the matched objective and the reused ID.

Procedure: `references/lifecycle.md` §2.

## 7. Modifying an Intent

This is the single flow for every change to an existing intent, and the
only entry point for a split. There is no separate refinement workflow.

1. Resolve the target (given ID, else the intent under discussion, else the
   most recently active one).
2. **Classify the target** with the one classification rule (§8) —
   **Modify** (edit in place) · **Child** (create a child, §7.1) ·
   **Independent** (a separate top-level intent) · **Reconcile** (§19). The
   creation flow (§6) uses the same rule; there is no second boundary
   algorithm.
3. Classify the change by impact
   (`../../references/cross-layer-coordination.md` §2.5.b).
4. Edit in place: preserve the intent ID and every stable item ID (§17),
   update `updated`, and record the effect on other intents or downstream
   Specs in `# Relationships and Impact` while warning the user.

**Record the change where it belongs — exactly once:**

| What changed | Where it goes |
|---|---|
| The desired outcome | `# Clarified Intent` (a new goal item, old one kept as history) |
| A limit or exclusion | `# Constraints and Success Criteria` |
| A choice the user made | `# Decisions`, with date and provenance label |
| An open product choice | `# Unknowns` (blocking or non-blocking) |
| An external fact | `# Facts and Research` |

A user-stated limit is **not** also a Decision, and a Decision is **not**
also restated as a Constraint. Duplicating one fact in two places is what
creates two authoritative records that can drift apart.

A necessary correction determined by confirmed sources uses the current
authorization; a new product choice goes to the user. An archived target is
reopened first (§9). Run the semantic consistency check (§13.4) after the
edit.

### 7.1 When the user asks to split

An explicit request to split ("拆成子 Intent", "split INT-001") is not a
separate command — it is the **Child** outcome of the classification in
§8, executed inside this flow.

1. Apply the **Child test** (§8.1) to the proposed sub-goal. If it does not
   pass, say so and keep one intent — no file is created, no ID is issued.
   Size, technical complexity, and the number of downstream Specs are never
   reasons to split (§16). If the user then insists on the split anyway,
   record that instruction as a confirmed user decision (§13.5) and carry
   the split out — the structure is the user's call, not the agent's.
2. If it passes, create the child: fresh ID, `parent: <parent-id>`, the
   parent's global constraints inherited by reference rather than copied,
   and the parent's `# Relationships and Impact` updated.
3. Migrate what moved: keep the original wording as history in the parent's
   `# Resume Notes` or a migration map, and make every old pointer still
   resolve (`references/item-ids.md` §5).
4. Classify the effect on the parent's authoritative content — no parent
   meaning change (the parent is not reopened, even when archived) ·
   material change to the parent (reopen first) · content moved to the
   child (reopen first, keep the original wording as history).
5. Apply `../../references/change-impact.md` to the moved or changed items
   and to any downstream artifact that cited them.

If a sub-intent already covers the topic, surface it instead of
duplicating.

Procedure: `references/lifecycle.md` §3 (child creation) and §4 (the edit).

## 8. Target Classification — the Single Authority

Every flow that can create or change an intent classifies the **target**
with this one rule: `new` (§6) and `modify` (§7) both land here. There is
no second boundary test anywhere in this skill.

| Class | Test | Result |
|---|---|---|
| **Modify** | Same user objective, wider or narrower scope | Edit in place, keep the ID |
| **Child** | A distinct user-valued sub-goal inside the parent objective, with an independent outcome, an independent decision space, and a real benefit from separate management | New ID, `parent` set, relationship and history updated (§7.1) |
| **Independent** | A separate user objective, subordinate to nothing | New top-level intent |
| **Reconcile** | Material semantic overlap, shared abstraction, or inherited-constraint conflict with an existing intent | `/intent-reconcile` (§19) |

A class is chosen by the **user objective** — never by topic, product area,
technical stack, document size, or the number of Specs the intent will
produce.

**Reconcile** is the only class that reaches another skill, and it reaches
`/intent-reconcile` for overlap, conflict, or shared abstraction **between
two or more intents**. An ordinary parent/child split is not a reconcile
case — it is the Child outcome executed in this skill (§7.1).

### 8.1 The Child test

Create a child Intent only when **all three** hold:

1. **Independent outcome** — the owner can prioritize, revise, accept,
   defer, or remove the sub-goal on its own.
2. **Independent decision space** — it carries its own key decisions,
   facts, unknowns, or trade-offs.
3. **Meaningful benefit** — separate management improves clarity, decision
   boundaries, context, or traceability.

A capability with independent technical decisions does not qualify. Neither
does size: a large, cross-domain intent with a clear goal stays one intent
(§16).

### 8.2 One goal per independent outcome

A goal is an outcome the user wants, not a module or a screen. If a
request mixes two business models that the user may not have noticed — e.g.
"keep my position size unchanged" and "open a new delta-neutral pair" —
record the request as stated and ask which outcome is meant. Do not merge,
average, or silently pick one.

### 8.3 Requests that are not a class of their own

A request about a technical capability (RPC access, DB schema, API shape, a
specific algorithm) is not a user objective. Capture the user goal behind
it as **Modify** of the covering intent, and route the capability to Spec /
Architecture / Module Design. A separate intent is created only for a user
objective.

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

1. Render the final summary: the goals, constraints, decisions, open
   questions, and the facts that bear on them.
2. **Authorization.** Apply `../../references/cross-layer-coordination.md`
   §2.5.b. A confirmed stage or an instruction to complete this goal covers
   archive once the checks pass. One explicit confirmation ("确认，继续") is
   enough — do not ask again, and do not extend that authorization to
   unrelated intents, Specs, architecture decisions, or code.
3. **Completion check** — required for the command and the natural-language
   flow, read against the saved document, not the summary:

   | Check | Pass condition |
   |---|---|
   | Goal | The goals in `# Clarified Intent` still describe the same thing the user asked for in `# Original Intent` |
   | Sequence | The confirmed user-visible order, when the goal has one, is intact and reachable from the real starting state (`../../references/cross-layer-coordination.md` §8) |
   | Constraints | User-stated limits and exclusions are present and current |
   | Decisions | Confirmed choices are present, labeled by who made them, and consistent with the goals |
   | Open questions | No blocking product choice remains — an unresolved *product choice* blocks; a recorded non-blocking unknown does not |
   | Evidence | The facts that bear on the goal carry a source and a verification date; the traceable record of decisions and relationships is intact |
   | Currency | No placeholder or stale claim is left in the current account; corrections recorded with their reason in `# Resume Notes` |
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
   `updated`, append a short Resume Notes entry (create the section if it
   does not exist yet), tell the user that `reopen` and `feedback` remain
   available, and hand off (§18).

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
4. Record the conclusion in `# Relationships and Impact` or `# Resume Notes`
   (create the section if it does not exist yet) — no separate feedback
   file, no second relationship database.
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

## 13. INTENT.md Contract

### 13.1 Sections

The section names and order are a **compatibility surface**: Spec,
Architecture, Implementation and Intent-Reconcile read INTENT.md by these
headings. Keep the names. What changes is what goes inside them, and how
many of them exist.

| Section | When | Authoritative for |
|---|---|---|
| `# Original Intent` | always | The user's own words, verbatim |
| `# Clarified Intent` | always | The desired outcome and its success evidence; the user-visible flow when the goal has an ordered path |
| `# Constraints and Success Criteria` | always | Limits, boundaries, exclusions; success criteria that are not attached to a goal |
| `# Decisions` | when a choice was made | Choices the user made, each labeled by who made it (§13.5); agent inferences stay in their own subsection and are never counted as decisions |
| `# Facts and Research` | optional | External facts that bear on the goal's feasibility or on a user decision |
| `# Unknowns` | optional | Undecided product choices, split into blocking and non-blocking |
| `# Evaluation` | optional | Engineering feasibility and engineering risk only |
| `# Relationships and Impact` | optional | Parent / child / related, impact scope |
| `# Spec Input` | optional | Handoff pointers plus what the Spec Agent must not decide |
| `# Resume Notes` | optional | Position, next owner, next action |

A section with no real content is **omitted**, not filled with a
placeholder. Only `# Original Intent` is written when the file is created.
The ten-section shape is no longer the default output: a simple request
yields three short sections; a rich request fills what it actually needs.
**Document length follows the number of independent product decisions, not
the number of modules, Specs, or API surfaces involved.**

### 13.2 Rules of single authority

- A goal is stated **once**. Constraints, decisions, and the handoff map
  point at it; they do not restate it.
- Success evidence belongs to **its goal**. A separate success-criterion
  entry exists only when the criterion spans goals.
- A user-stated limit is not repeated as a Decision, and a Decision is not
  repeated as a Constraint.
- `# Spec Input` never copies content — it points at item IDs and names the
  choices the Spec Agent must return to the user.
- Item IDs are optional, and only for content a downstream layer must cite
  (§17).

### 13.3 Layer ownership

| Layer | Decides | Never pulled into Intent |
|---|---|---|
| **Intent** | why the user wants it, what result they want, what must not change, which product choices are still the user's, how the user knows it worked | — |
| **Spec** | observable system behavior, states and error paths, inputs and outputs, functional requirements, acceptance | system behavior and acceptance |
| **Architecture / Module Design** | module responsibility, interfaces, data and persistence, algorithms, technical dependencies | design and mechanisms |
| **Research** | external fact verification, feasibility evidence, dynamic parameter snapshots, sources and their limits | general technical research |

Cross-layer background may be repeated briefly, but the authoritative
definition lives in exactly one place. The test is whether the content
carries the **meaning of the user's goal** — not whether it happens to
contain a technical term.

### 13.4 Semantic consistency check

Run it before saving a new or changed Intent, and again at archive. It is a
check, not a deliverable — do not produce a review report for it.

1. **Fidelity** — does any statement contradict `# Original Intent`?
2. **Provenance** — is an inference written as confirmed fact? Is any
   `(assumed)` item sitting in `# Decisions` as a confirmed choice?
3. **Constraint provenance** — is a limit present that the user never
   stated, with ordinary engineering practice promoted to a hard constraint?
4. **Coherence** — do the goals and the constraints contradict each other?
5. **Expectation vs. guarantee** — is an outcome the system cannot promise
   (profit, price, uptime, third-party behavior) written as a system
   guarantee?
6. **No duplication** — are there two entries with the same meaning?
7. **Layer discipline** — has a design decision been made early?
8. **Ambiguity** — does a key term in a goal still have two readings that
   would change the goal?

Fix what is wrong in the document and keep the history. If a fix would
change a meaning the user confirmed, ask the user instead of editing.

### 13.5 Decision provenance

Every entry in `# Decisions` says who made it:

| Label | Meaning |
|---|---|
| `USER-STATED` | The user said it outright. It usually also appears as a Goal or a Constraint — do not copy it there again. |
| `CONFIRMED` | The user explicitly confirmed it after a clarification. |
| `INFERRED` | The agent inferred it. Inference is not authorization; it never appears as a confirmed decision. |
| `UNRESOLVED` | A product choice still open. It lives in `# Unknowns` as blocking and is not repeated in `# Decisions`. |

Field-level template and placement notes: `references/intent-template.md` —
load it when creating a new `INTENT.md` or restructuring an existing one.

## 14. Core Invariants

| # | Invariant |
|---|---|
| 1 | **Confirmed meaning is the user's.** Never silently change a confirmed goal, constraint, decision, or the confirmed operation order. Within an authorized goal the owning layer fixes its own contradictions; that is not a second approval round. |
| 2 | **Modify before creating.** If the objective is the same, modify the existing intent and preserve its ID. Creation is the exception. |
| 3 | **A child needs independent user value** the owner can manage on its own (§8.1). |
| 4 | **IDs are immutable.** The intent ID is never re-numbered or reused, and a stable item ID is never reassigned to a different meaning (§17). |
| 5 | **Separate what is known from what is assumed.** Verified facts carry a source and date; unverified claims live in `# Unknowns`; agent inference is labeled `(assumed)` and never appears as a confirmed decision. A user's claim is a fact about what the user said, not a fact about the world. |
| 6 | **Keep history.** Material edits, splits, and migrations are recorded with date, old meaning, new meaning, and reason; superseded items stay traceable; downstream pointers still resolve. |
| 7 | **Stay inside the layer.** Intent does not write Specs, contracts, module designs, or code, and does not modify another layer's artifact; it returns a result for that layer's owner to apply. |
| 8 | **Never claim work that did not happen.** No claiming a downstream artifact was updated, synced, or verified when it was not. Accepted feedback is not downstream synchronization. |
| 9 | **Archive is not downstream completion.** An Intent may be archived while Spec, Architecture, and Module work are pending, and archive still requires its own completion check (§10). |
| 10 | **The user sequence stays at user level.** Intent records the ordered user-visible steps and the confirmed order; UI detail, error handling, and system state transitions belong to Spec (§18). |
| 11 | **One authoritative location.** One business meaning has one home. Never restate a goal, a constraint, or a decision in a second section; point at it instead. |
| 12 | **Intent stays minimal.** Content enters the authoritative sections only through the inclusion test (§1.1). A longer document is not a better document. |
| 13 | **An expectation is not a guarantee.** A user hope ("make money", "be fast") is a desired outcome, never a per-instance system guarantee or an acceptance the system can be held to. |
| 14 | **Never decide for the user.** A product choice that belongs to the user goes to the user (`../../references/cross-layer-coordination.md` §2.5.b), even when the agent has a recommendation. |

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
Module Design. Which content belongs to which layer is tabulated in §13.3.

Create a child Intent only when it represents a distinct user-valued outcome
within the parent objective that the owner can manage on its own — the
**Child test** in §8.1 is the authority; do not restate its conditions
here.

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

A success criterion usually lives with its goal; it gets its own section
only when it spans goals (§13.2).

The intent ID is immutable, an assigned ID is never reassigned to a
different meaning, a wording-only edit keeps the ID, and a material change
adds a new ID while the old entry stays as history. `references/item-ids.md`
is the authority for assignment, migration, and downstream citation.

## 18. Hand-off

The skill never writes code or designs solutions. Its output is the
`INTENT.md`.

**A downstream Spec reads INTENT.md itself.** The authoritative content —
the goal and why, the constraints, the confirmed decisions and their dates,
the success evidence, the facts that bear on the goal, and the remaining
open choices — is already in the document. The Spec Agent cites the item
IDs it consumes (`INT-001/G-01`, `INT-001/C-01`), so a later Intent change
can be detected.

`# Spec Input` is therefore **optional and short**. When it exists it is a
handoff map, not a second copy:

- the goals and constraints the Spec must satisfy, by item ID;
- the choices the Spec Agent is **not** allowed to make — the product
  decisions that are still the user's, and the blocking questions it must
  return rather than settle;
- the impact scope, when it is known.

It never restates a goal, a constraint, or a decision in prose. A Spec that
can find the content in the Intent does not need it.

**An Intent may produce zero, one, or many Specs.** Write the handoff
without one specific Spec in mind. Intent hierarchy does not determine Spec
decomposition: a large cross-domain Intent can feed several Specs without
being split into children.

`# Clarified Intent` states the user's **operation sequence from a real
starting point**: what the user knows and provides at the start, who supplies
each input, the confirmed order of operations, and what the user observes
when it works. Keep it at that level — detailed UI behavior, error and
failure handling, and system state transitions belong to Spec — but do not
drop a step or blur the order when a downstream reader could otherwise
misread the core flow. The shared rule is
`../../references/cross-layer-coordination.md` §8.

## 19. Reconcile Trigger

During `new` and any material modification (`modify`), run one lightweight
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

A requested parent/child split is **not** a reconcile case. It is the
**Child** outcome of §8.1, handled by this skill; `/intent-reconcile` owns
overlap, conflict, and shared abstraction between two or more intents.
