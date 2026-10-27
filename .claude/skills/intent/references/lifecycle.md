# Intent Lifecycle

How the Intent skill executes the lifecycle operations: creating and
matching, splitting, modifying, archiving, reopening, resuming, and handling
feedback on archived intents. The entry point, the classification rule, the
invariants, and the routing live in `SKILL.md`; this file is the method.
Load it when an operation actually needs one of these procedures — `list`,
`show`, and `tree` never need it.

## 1. Scope

| Operation | Entry point |
|---|---|
| Create or match a new goal | `SKILL.md` §3 (`new`) · §2 below |
| Classify a target (Modify / Child / Independent / Reconcile) | `SKILL.md` §4 — the single authority |
| Create a child intent | `SKILL.md` §4.1 · §3 below |
| Modify an existing intent | `SKILL.md` §3 (`modify`) · §4 below |
| Edit a named object under a bounded request | `SKILL.md` §3 · §4 below |
| Archive | `SKILL.md` §3 (`archive`) · §5 below |
| Reopen or resume | `SKILL.md` §3 (`reopen` / `resume`) · §6 below |
| Feedback, including on an archived intent | `SKILL.md` §3 (`feedback`) · §7 below |

Nothing here adds lifecycle states. `active` and `archived` remain the only
statuses (`SKILL.md` §5, invariant 7).

## 2. Creation and Matching

1. Record the user's raw words as `# Original Intent` before interpreting
   anything.
2. Discover the existing intents: `Glob docs/intents/INT-*/INTENT.md`, then
   read the frontmatter and the `# Clarified Intent` of plausible
   candidates. Match on the **user objective** (the outcome the owner
   wants), not on topic, product area, or technical stack. This sweep is
   proportional (`SKILL.md` §3): read the frontmatter of everything, and the
   body only of the intents that could plausibly be the same objective.
3. Classify the target with the one rule in `SKILL.md` §4. That table is the
   authority; the modify flow uses it too, and there is no second boundary
   test anywhere in this skill.
4. A request that is primarily about a technical capability (RPC access, DB
   schema, API shape, a specific algorithm) is not a user objective
   (`SKILL.md` §1): capture the user goal behind it as **Modify** of the
   covering intent and route the capability downstream.
5. Run the reconcile check (`SKILL.md` §19) — one lightweight semantic check
   against the existing intents.
6. Generate the ID for a new intent (`references/item-ids.md` §2). Never
   overwrite an existing ID. An explicit user-supplied ID is used only after
   confirming it does not collide.
7. Create `docs/intents/INT-NNN/INTENT.md` (create `docs/intents/` if
   missing) with `status: active` and the frontmatter fields in
   `references/intent-template.md` §1. Write `# Original Intent` verbatim —
   and nothing else. The other sections are created when they have real
   content; a section with no content is omitted, not filled with a
   placeholder.
8. Clarify (`references/clarification.md`), then persist after every
   meaningful clarification or research result. Run the semantic consistency
   check (`references/intent-template.md` §7) before handing the intent over.

Explain a **Modify** routing: name the matching objective and the reused ID,
so the user can see that nothing was duplicated. Ask only when the user
explicitly required a separate identity or the choice would change confirmed
product meaning.

## 3. Split and Child Creation

A split is justified by boundaries, never by size. It is the **Child**
outcome of the classification in `SKILL.md` §4; this section is the
execution.

1. Load the parent intent, its parent (if any), and directly related
   intents. Check existing children (`Glob` for `parent: <id>`) so a
   duplicate is not created.
2. Apply the **Child test** (`SKILL.md` §4.1). If it does not pass, the
   outcome is **Modify**: no new file, no new ID, and the reason is explained
   to the user.
3. Choose the outcome and record the reason in `# Resume Notes`.

   **Modify** — extend the existing intent. No new file, ID preserved.

   **Create child** — classify the effect on the parent's authoritative
   content:

   | Case | Parent meaning | Parent handling |
   |---|---|---|
   | A — Child without parent change | No new sub-goal, constraint, or decision on the parent | Parent is **not** reopened, even when archived. Child is `active`. Only `# Relationships and Impact` changes. |
   | B — Material change to the parent | Goal, scope, constraints, success criteria, or confirmed decisions added, removed, or materially changed | Reopen an archived parent first, then edit. A new product choice goes to the user (`../../references/cross-layer-coordination.md` §2.5.b) |
   | C — Content moved to the child | A goal, constraint, or decision is relocated | Treated as a material change: reopen first if archived. Keep the original wording in the parent's `# Resume Notes` or a migration map, and make every old pointer still resolve to the new location or to the historical record. |

4. The child gets a fresh ID and `parent: <parent-id>` (`references/item-ids.md`
   §2). The parent keeps its overall goal and its global constraints; the
   child takes only the specific sub-goal and its own decisions. Constraint
   inheritance is by reference, not by copy: the child cites the parent's
   constraint item IDs rather than restating them
   (`references/intent-template.md` §2).
5. Apply `../../references/change-impact.md` to the moved or changed items
   and to any downstream artifact that cited them.

**What the proposed separation is really about.** Route it by its nature:
if the user objective stays the same, keep the Intent intact and let Spec
decompose system behavior; module ownership goes to Architecture, while APIs,
data storage, and algorithms go to Module Design. When uncertain, compare
alternative structures and explain which user objectives would actually become
independently manageable.

**What does not trigger a reconcile here.** A requested parent/child split is
the Child outcome of `SKILL.md` §4.1, not a reconcile case
(`SKILL.md` §19). An inconsistency inside one document is a consistency
issue (`references/intent-template.md` §7), fixed in place.

## 4. Modification and Authorization

1. Resolve the target intent: the ID or file the user named, else the intent
   under discussion, else the most recently active one.
2. **Scoped direct edit?** If the user named the object and asked for a
   bounded change to it, edit that object under the current authorization,
   skip the repository sweep and the reconcile check, and escalate only on
   the four conditions below. Steps 5–7 then apply to that edit; the
   consistency check (step 7) and the archived target (step 8) still apply.

   **Escalate out of the scoped path only when the change:**

   1. introduces a **separate user objective** — then classify (`SKILL.md` §4);
   2. **contradicts** a confirmed goal, constraint, or decision — then the
      conflict goes to the user (`../../references/cross-layer-coordination.md`
      §2.5.b);
   3. changes a **relationship** or another intent's authoritative content —
      then apply `../../references/change-impact.md`;
   4. needs a **product choice** that is the user's to make.

   Do not sweep the other intents, restructure sections that were not
   mentioned, open a clarification round, or start a research task.
3. Otherwise classify the target with the one rule in `SKILL.md` §4, and run
   the reconcile check (`SKILL.md` §19) unless the edit is scoped to one
   object.
4. Classify the change by impact
   (`../../references/cross-layer-coordination.md` §2.5.b) and apply that
   rule: a necessary correction that preserves confirmed user meaning is
   applied under the current authorization; a change to confirmed product
   meaning goes to the user. Investigate a compliant solution before asking.
5. Apply the edit in place. Preserve the intent ID and every stable item ID
   (`references/item-ids.md`).
6. Record the change **once**, in the section that owns its meaning
   (`references/intent-template.md` §2). Update the `updated` field, and
   record the effect on other intents or downstream Specs in
   `# Relationships and Impact` while warning the user.
7. Run the semantic consistency check (`references/intent-template.md` §7).
8. If the target is archived, use `reopen` (§6) first.

A **wording-only** change stops after step 6: it does not trigger a
downstream re-review. A **semantic** change to a goal, constraint, or
decision continues into `../../references/change-impact.md`, scoped to the
changed items.

## 5. Archive Completion Gate

The gate is read against the saved document, not against a summary of it.
Authorization to complete the goal covers the archive once the checks pass;
it does not waive the checks.

1. **Authorization.** Apply `../../references/cross-layer-coordination.md`
   §2.5.b. A confirmed stage or an instruction to complete this goal covers
   the archive once the checks pass. One explicit confirmation ("确认，继续")
   is enough — do not ask again, and do not extend that authorization to
   unrelated intents, Specs, architecture decisions, or code.
2. **Completion check** — required for the command and for the
   natural-language flow:

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

3. **Deeper check for complex or high-risk intents** — money and financial
   calculation, security and permission boundaries, core data correctness
   (state reconstruction, replay, NAV, idempotency), a multi-step user path
   whose order is necessary to the goal, or a change that materially moves a
   downstream contract.
4. Run the semantic consistency check (`references/intent-template.md` §7).
   An unresolved blocking ambiguity keeps the intent `active`.
5. If the path, outcome, or authoritative meaning is still unclear, name
   the specific gap and keep the intent `active`. Do not pass an Intent gap
   downstream as if it were complete.
6. **Archive does not require downstream Spec to be complete.** The intent is
   ready when the user confirmed goal, scope, and decisions; Spec,
   Architecture, and Module work may follow in parallel or later. A later
   downstream finding routes back through `feedback` (§7), which may lead to
   `reopen`; that is not automatic.
7. When authorized and the checks pass: set `status: archived`, update
   `updated`, append a short `# Resume Notes` entry (create the section if it
   does not exist yet), tell the user that `reopen` and `feedback` remain
   available, and hand off (`SKILL.md` §7).

Routine editorial cleanup inside the authorized scope needs no second
confirmation. A changed user goal or a new product decision does.

## 6. Reopen and Resume

**Reopen** — the single edit path for an archived intent, used for material
changes and for routine corrections alike. The difference is the
authorization dimension, not the lifecycle shape.

1. Classify by impact with the rule of §4 step 4
   (`../../references/cross-layer-coordination.md` §2.5.b): a necessary
   correction that preserves confirmed meaning uses the authorized goal; a
   change to confirmed meaning needs a user decision.
2. Set `status: active`, update `updated`, note why in `# Resume Notes`.
3. Apply the edit (see §4). Preserve IDs.
4. Apply `../../references/change-impact.md` over the changed items: record
   changed item IDs, affected downstream references, uncertain links, and the
   next owner and action. Old downstream `final` / PASS evidence stays scoped
   to the basis it checked. Do not infer impact from the intent filename
   alone.
5. An explicit request to change an archived intent authorizes
   reopen-and-modify; stop and confirm if the change goes beyond what the
   user asked for.
6. If the gate of §5 can no longer pass, keep the intent `active` and record
   the failing condition and the resume position instead of writing a
   completion claim.

**Resume** — continue an active intent where the last session stopped.

1. Load the intent and read `# Resume Notes` for the saved position.
2. Apply `../../references/change-impact.md` to any changed Goal / Constraint
   / Decision and to the downstream items that cite them.
3. Read `# Decisions` before asking anything — answered questions are not
   asked again.
4. Continue the open frontier: unresolved decisions are clarified
   (`references/clarification.md`), unresolved facts are researched
   (`references/research.md`).
5. Record the affected IDs, the owner, and the next action in
   `# Resume Notes`.

## 7. Feedback

Feedback arrives from Spec, Architecture, Module Design, or Implementation
and must reach the owner that can fix it. An archived intent can receive
feedback; feedback alone does **not** trigger `reopen`.

1. Identify source and target; load the target `INTENT.md` and the source
   artifact by path. Never fabricate a source: if only an intent ID is
   given, inspect recorded feedback, Resume Notes, and relevant Git changes
   first, and ask only if the source stays unidentifiable.
2. Assess the problem, then pick the **ownership level**:

   | Level | Symptom | Route |
   |---|---|---|
   | Intent | User goal ambiguity, conflicting user goals or constraints, a decision to revisit, a fact that invalidates the original user goal | Handle here |
   | Spec | Incomplete system behavior, missing acceptance criteria or functional requirements | Route to Spec |
   | Architecture | Unclear module ownership, missing cross-module capability, conflicting dependencies, unclear contract ownership | Route to Architecture |
   | Module / Implementation | Wrong implementation, algorithm bugs, DB design, code/spec mismatch | Route back to the source |

3. Handled here: repair an internal contradiction determined by confirmed
   sources under the current authorization; a new product choice goes to the
   user; a material change to an archived intent uses `reopen` (§6). Several
   intents sharing a semantic conflict go to `/intent-reconcile`
   (`SKILL.md` §19) under the authorized goal, preserving the return point.
4. Record the conclusion in `# Relationships and Impact` or `# Resume Notes`
   (create the section if it does not exist yet) — no separate feedback
   file, no second relationship database.
5. Return to the source owner using the feedback contract in
   `../../references/cross-layer-coordination.md` §3, §4, and §5 — source,
   target, problem, evidence, requested resolution, **Status** (`Accepted` ·
   `Rejected` · `Redirected` · `Needs Owner Decision`), **Rationale**,
   **Intent changes**, **Downstream impact**, **Suggested next step**. These
   are outcomes of one feedback event, not lifecycle states. A short
   natural-language message with an intent ID is acceptable when the context
   is clear. The source artifact usually cannot be modified from this skill —
   return the result text for its owner to apply, and never claim the source
   artifact was updated.
6. Intent normally does **not** delegate to the Independent Reviewer: its
   authoritative content is the user's stated goals and decisions, not a
   verifiable system artifact. Self-check plus the user's confirmation is the
   standard. A Targeted Resolution Verification
   (`../../references/verification.md` §3) applies only when the change has
   material downstream correctness implications, an authorized fix materially
   changes a downstream requirement, constraint, invariant, public contract,
   or load-bearing decision, and that Trigger B fires.
