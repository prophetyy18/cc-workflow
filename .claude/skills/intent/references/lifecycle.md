# Intent Lifecycle

How the Intent skill executes the lifecycle operations: creating and
matching, splitting, archiving, reopening, resuming, and handling feedback
on archived intents. The entry point, the invariants, and the command
routing live in `SKILL.md`; this file is the method. Load it when an
operation actually needs one of these procedures — `list`, `show`, and
`tree` never need it.

## 1. Scope

| Operation | Entry point |
|---|---|
| Create or match a new goal | `SKILL.md` §6 · §2 below |
| Modify an existing intent | `SKILL.md` §7 · §4 below |
| Edit a named object under a bounded request | `SKILL.md` §7.2 · §4 below |
| Classify a target (Modify / Child / Independent / Reconcile) | `SKILL.md` §8 — the single authority |
| Create a child intent | `SKILL.md` §7.1 · §3 below |
| Archive | `SKILL.md` §10 · §5 below |
| Reopen or resume | `SKILL.md` §9 · §6 below |
| Feedback on an archived intent | §7 below |

Nothing here adds lifecycle states. `active` and `archived` remain the only
statuses (`SKILL.md` §14, invariant 9).

## 2. Creation and Matching

1. Record the user's raw words as `# Original Intent` before interpreting
   anything.
2. Discover the existing intents: `Glob docs/intents/INT-*/INTENT.md`, then
   read the frontmatter and the `# Clarified Intent` of plausible
   candidates. Match on the **user objective** (the outcome the owner
   wants), not on topic, product area, or technical stack. This sweep is
   proportional (`SKILL.md` §5.1): read the frontmatter of everything, and
   the body only of the intents that could plausibly be the same objective.
3. Classify the target with the one rule in `SKILL.md` §8 — **Modify** /
   **Child** / **Independent** / **Reconcile**. That table is the
   authority; the modify flow uses it too, and there is no second
   boundary test anywhere in this skill.
4. If the request is primarily about a technical capability (RPC access, DB
   schema, API shape, a specific algorithm), do not create an intent for it.
   Capture the user goal behind it and route the capability downstream
   (`SKILL.md` §8.3).
5. Generate the ID for a new intent: highest existing `INT-NNN` plus one,
   zero-padded to three digits. An explicit user-supplied ID is used only
   after confirming it does not collide. Never overwrite an existing ID.
   Re-check the allocated ID with `Glob docs/intents/<id>/INTENT.md`
   immediately before writing — if it appeared in the meantime, take the
   next free number.
6. Create `docs/intents/INT-NNN/INTENT.md` (create `docs/intents/` if
   missing) with `status: active` and the frontmatter fields in
   `references/intent-template.md`. Write `# Original Intent` verbatim — and
   nothing else. The other sections are created when they have real content;
   a section with no content is omitted, not filled with a placeholder.
7. Clarify (see `clarification.md`), then persist after every meaningful
   clarification or research result. Run the semantic consistency check
   (`SKILL.md` §13.4) before handing the intent over.

Explain a **Modify** routing: name the matching objective and the reused ID, so
the user can see that nothing was duplicated. Ask only when the user
explicitly required a separate identity or the choice would change confirmed
product meaning.

## 3. Split and Child Creation

A split is justified by boundaries, never by size. It is the **Child**
outcome of the classification in `SKILL.md` §8, executed inside the modify
flow (§7.1 there); this section is the execution.

1. Load the parent intent, its parent (if any), and directly related
   intents. Check existing children (`Glob` for `parent: <id>`) so a
   duplicate is not created.
2. Apply the **Child test** in `SKILL.md` §8.1 — independent outcome,
   independent decision space, meaningful benefit. If it does not pass, the
   outcome is **Modify**: no new file, no new ID, and the reason is
   explained to the user. A capability with independent technical decisions
   does not qualify.
3. Choose the outcome and record the reason in `# Resume Notes`.

   **Modify** — extend the existing intent. No new file, ID preserved.

   **Create child** — classify the effect on the parent's authoritative
   content:

   | Case | Parent meaning | Parent handling |
   |---|---|---|
   | A — Child without parent change | No new sub-goal, constraint, or decision on the parent | Parent is **not** reopened, even when archived. Child is `active`. Only `# Relationships and Impact` changes. |
   | B — Material change to the parent | Goal, scope, constraints, success criteria, or confirmed decisions added, removed, or materially changed | Reopen an archived parent first, then edit. A new product choice goes to the user (`../../references/cross-layer-coordination.md` §2.5.b) |
   | C — Content moved to the child | A goal, constraint, or decision is relocated | Treated as a material change: reopen first if archived. Keep the original wording in the parent's `# Resume Notes` or a migration map, and make every old pointer still resolve to the new location or to the historical record. |

4. The child gets a fresh ID and `parent: <parent-id>`. The parent keeps its
   overall goal and its global constraints; the child takes only the specific
   sub-goal and its own decisions. Constraint inheritance is by reference,
   not by copy: the child cites the parent's constraint item IDs rather than
   restating them (`SKILL.md` §13, single-authority rule).
5. Apply `../../references/change-impact.md` to the moved or changed items
   and to any downstream artifact that cited them.

Do not split an intent because it is large, spans several domains, or will
produce several Specs. Do not split to tidy the document tree.

## 4. Modification and Authorization

1. Resolve the target intent: the ID or file the user named, else the intent
   under discussion, else the most recently active one.
2. **Scoped direct edit?** If the user named the object and asked for a
   bounded change to it, take `SKILL.md` §7.2: edit that object under the
   current authorization, skip the repository sweep and the reconcile check,
   and escalate only on the four conditions listed there. Steps 4–6 below
   then apply to that edit; the consistency check (step 7) and the archived
   target (step 8) still apply.
3. Otherwise classify the target with the one rule in `SKILL.md` §8 —
   **Modify** (edit in place) · **Child** (create a child, §3 below) ·
   **Independent** (a separate top-level intent) · **Reconcile**
   (`SKILL.md` §19). The creation flow uses the same rule; do not derive a
   second one here.
4. Classify the change by impact
   (`../../references/cross-layer-coordination.md` §2.5.b):
   - **Necessary correction** — the confirmed upstream sources determine the
     answer and confirmed meaning is preserved. Apply it under the current
     authorization and record it.
   - **Product change** — the result would change confirmed product meaning,
     order, scope, a key constraint, or compatibility. Ask the user.
   Investigate a compliant solution before asking.
5. Apply the edit in place. Preserve the intent ID and every stable item ID
   (`item-ids.md`).
6. Record the change **once**, in the section that owns its meaning
   (`SKILL.md` §7): a new outcome goes to `# Clarified Intent`, a new limit
   to `# Constraints and Success Criteria`, a choice the user made to
   `# Decisions`, an open choice to `# Unknowns`, an external fact to
   `# Facts and Research`. Update the `updated` field, and record the effect
   on other intents or downstream Specs in `# Relationships and Impact`.
7. Run the semantic consistency check (`SKILL.md` §13.4).
8. If the target is archived, use `reopen` (§6) first.

A **wording-only** change stops after step 6: it does not trigger a
downstream re-review. A **semantic** change to a goal, constraint, or
decision continues into `../../references/change-impact.md`, scoped to the
changed items.

## 5. Archive Completion Gate

The gate is read against the saved document, not against a summary of it.
Authorization to complete the goal covers the archive once the checks pass;
it does not waive the checks.

1. Read the saved `INTENT.md` against `# Original Intent`.
2. Verify:
   - the goals still express the same objective as the original request, and
     the confirmed user-visible order, when the goal has one, is intact;
   - user-stated constraints are present and current, and the confirmed
     decisions are consistent with the goals;
   - no blocking product choice remains in `# Unknowns`. A user-owned choice
     that is still open blocks. A known, recorded, non-blocking unknown does
     not;
   - the facts that bear on the goal carry a source and a verification date;
     confirmed decisions and relationships are traceable;
   - the current account has no placeholder and no stale scope claim.
     Correct what is stale and record the reason in `# Resume Notes`.
     Historical decisions stay traceable;
   - feedback received for this intent is recorded with its status. Accepted
     feedback is not evidence that the downstream artifact was updated.
3. Run the semantic consistency check (`SKILL.md` §13.4). An unresolved
   blocking ambiguity keeps the intent `active`.
4. Deepen the check for complex or high-risk intents — money and financial
   calculation, security and permission boundaries, core data correctness
   (state reconstruction, replay, NAV, idempotency), a multi-step user path
   whose order is necessary to the goal, or a change that materially moves a
   downstream contract.
5. If the path, outcome, or authoritative meaning is still unclear, name
   the specific gap and keep the intent `active`. Do not pass an Intent gap
   downstream as if it were complete.
6. When the checks pass and the authorization covers it: set
   `status: archived`, update `updated`, append a `# Resume Notes` entry,
   then hand off (`SKILL.md` §18).

Routine editorial cleanup inside the authorized scope needs no second
confirmation. A changed user goal or a new product decision does.

## 6. Reopen and Resume

**Reopen** — the single edit path for an archived intent, used for material
changes and for routine corrections alike. The difference is the
authorization dimension, not the lifecycle shape.

1. Classify by impact (`../../references/cross-layer-coordination.md`
   §2.5.b): a necessary correction that preserves confirmed meaning uses the
   authorized goal; a change to confirmed meaning needs a user decision.
2. Set `status: active`, update `updated`, note why in `# Resume Notes`.
3. Apply the edit (see §4). Preserve IDs.
4. Run `../../references/change-impact.md` over the changed items: record
   changed item IDs, affected downstream references, uncertain links, and the
   next owner and action. Old downstream `final` / PASS evidence stays scoped
   to the basis it checked.
5. If the gate of §5 can no longer pass, keep the intent `active` and record
   the failing condition and the resume position instead of writing a
   completion claim.

**Resume** — continue an active intent where the last session stopped.

1. Load the intent and read `# Resume Notes` for the saved position.
2. Apply `../../references/change-impact.md` to any changed Goal / Constraint
   / Decision and to the downstream items that cite them.
3. Read `# Decisions` before asking anything — answered questions are not
   asked again.
4. Continue the open frontier: unresolved decisions are clarified
   (`clarification.md`), unresolved facts are researched (`research.md`).
5. Record the affected IDs, the owner, and the next action in
   `# Resume Notes`.

## 7. Feedback on an Archived Intent

An archived intent can receive feedback. Feedback alone does **not** trigger
`reopen`.

1. Identify source and target, and load the source artifact by path. Never
   invent a source.
2. Assess the problem and its ownership level (`SKILL.md` §11).
3. If the assessment shows that only authoritative Intent content must
   change materially, use `reopen` (§6) before editing. If the archived
   content is correct and the problem belongs to another layer, return the
   result to that layer's owner and leave the intent archived.
4. Record the outcome and the routing in `# Relationships and Impact` or
   `# Resume Notes` — the archive state does not stop the record from being
   current.
