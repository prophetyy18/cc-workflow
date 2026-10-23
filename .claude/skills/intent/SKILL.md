---
name: intent
description: Capture, clarify, persist, and evolve user Intent. Turns a rough request into a minimal INTENT.md — the user's goal, their constraints, the choices they made, and the choices still open — that downstream Spec Agents can read. Use when the user wants to start, modify, split, resume, link, archive, or review an intent. Also use when the user says "I want to build X", "let's plan Y", "create a new intent for Z", or asks to clarify, scope, or change an existing intent.
allowed-tools: Read, Edit, Write, Glob, Grep, Bash(date*), Bash(mkdir*), Bash(git*), WebFetch, WebSearch
---

# Intent Skill

Capture user objectives as authoritative `INTENT.md` documents. This file is the entry point: **what** an Intent is, **how to route** a request, the **one** classification rule, the invariants, and **when** to load a reference. Every procedure lives in `references/` — load one only when its trigger fires (§6). Section numbers are kept where another skill points at them (§19).

## 1. Identity and Scope

An Intent is an independently meaningful **user objective** — a result the owner can prioritize, revise, accept, defer, or remove on their own. Not a technical capability, module, API, algorithm, or implementation task.

Intent is the minimal sufficient contract between the user and everything that follows: it keeps the *meaning* of the user's goal, the limits they set, the choices they made, and the choices still open intact across context changes, agent switches, and hand-offs. It is not a specification, a design, a task list, a research report, or a progress report. What belongs to Spec, Architecture / Module Design, or Research instead is tabulated in `references/intent-template.md` §5.

### 1.1 Inclusion test

Put a fact into Intent's authoritative content only when at least one of these holds: removing it could let a downstream reader **misunderstand what the user actually wants**, **violate a limit the user stated**, or **make a product choice that is the user's to make**; or it **cannot** be settled by Spec / Architecture / Configuration on its own without changing the meaning of the goal. If none holds, it belongs to a downstream layer or nowhere. Apply the test to the *semantic load*, not to whether the content contains a technical word: "a single-leg fill failure must be handled" is Intent content; "use `clientOrderId` plus a persistent event log" is not. Effort scales with the **uncertainty of user decisions and the risk of the change**.

## 2. Storage and Stable IDs

Intents live in `docs/intents/INT-NNN/INTENT.md` (flat, no nesting); discover them with `Glob docs/intents/INT-*/INTENT.md`. The `id` field holds the stable ID; allocation, immutability, item IDs, and downstream citation are in `references/item-ids.md`.

## 3. Routing

Read `$ARGUMENTS`; the first token is the subcommand, the rest is the target. For `new` the target is the whole remaining string; for other subcommands a single ID or empty. An unknown subcommand shows the help and stops — do not guess.

| Input | Action | Procedure |
|---|---|---|
| `new` · "I want to build X" · "let's plan Y" | Create, then clarify | `references/lifecycle.md` §2 |
| (empty) · `help` | Show this help | — |
| `list` · "show me X" · "show the hierarchy" | Discover only, edit nothing: list grouped by status; print the full `INTENT.md` (an ambiguous partial ID lists candidates and asks); or show parent / child / related — orphans are roots, `related` in parentheses, and cycles, self-parent, or a missing parent are reported as warnings | — |
| `modify` · `refine` · "change the goal of INT-001" · "add constraint C to INT-001" · "拆成子 Intent" | One edit flow: a bounded scoped edit of the named object, otherwise classify (§4) — Modify in place, or Child (§4.1) | `references/lifecycle.md` §3–§4 |
| "make this a sub-intent of INT-002" · "link INT-001 and INT-003" | Set `parent` / `related` | `references/intent-template.md` §6 |
| `resume` · `reopen` · "I need to change X but it's archived" | Continue the open frontier, or re-open an archived intent and modify it | `references/lifecycle.md` §6 |
| `archive` · "we're done with X" · "确认，继续" | Completion gate, then archive | `references/lifecycle.md` §5 |
| `feedback` · "spec found an issue with INT-001" | Route upstream feedback to its owner | `references/lifecycle.md` §7 |
| "is INT-001 too big?" · "does X still make sense?" | Answer with a goal-independence assessment (§4.1); change nothing — product value is the user's call, not an engineering assessment | — |
| "is Y technically feasible?" | Evidence in `# Facts and Research` when it bears on the goal; unresolved facts go to `# Unknowns` | `references/research.md` |

`refine` is a legacy spelling of `modify`, not a second workflow: it resolves to `modify` before anything else happens and runs the same classification and the same edit path. Splitting is not a command of its own — it is the **Child** outcome of the classification, requested in ordinary language.

Discovery is **proportional to the operation**: `list` reads only the frontmatter of every intent; `show` and `tree` read the frontmatter plus the requested `INTENT.md`; a scoped direct edit reads only its target; `modify` and `resume` additionally read the target's `parent`, `related`, and children. Never sweep the rest of `docs/intents/` on the way.

## 4. Target Classification — the Single Authority

Every flow that can create or change an intent classifies the **target** with this one rule: `new` and `modify` both land here. There is no second boundary test anywhere in this skill.

| Class | Test | Result |
|---|---|---|
| **Modify** | Same user objective, wider or narrower scope | Edit in place, keep the ID |
| **Child** | A distinct user-valued sub-goal inside the parent objective, with an independent outcome, an independent decision space, and a real benefit from separate management | New ID, `parent` set, relationship and history updated |
| **Independent** | A separate user objective, subordinate to nothing | New top-level intent |
| **Reconcile** | Material semantic overlap, shared abstraction, or inherited-constraint conflict with an existing intent | `/intent-reconcile` (§19) |

A class is chosen by the **user objective** — never by topic, product area, technical stack, document size, or the number of Specs the intent will produce. One goal per independent outcome: a request that mixes two business models is recorded as stated and the user is asked which outcome is meant (`references/clarification.md` §7).

Classification answers one question: **is this the same object, a sub-goal, a separate objective, or a conflict?** It is not a ritual every request must pass through: when the user already named the object and the change is bounded, the answer is **Modify** and the edit proceeds; classify only when the edit escalates (`references/lifecycle.md` §4).

**Reconcile** is the only class that reaches another skill: it reaches `/intent-reconcile` for overlap, conflict, or shared abstraction **between two or more intents**. An ordinary parent/child split is not a reconcile case — it is the Child outcome executed in this skill.

### 4.1 The Child test

Create a child Intent only when **all three** hold:

1. **Independent outcome** — the owner can prioritize, revise, accept, defer, or remove the sub-goal on its own.
2. **Independent decision space** — it carries its own key decisions, facts, unknowns, or trade-offs.
3. **Meaningful benefit** — separate management improves clarity, decision boundaries, context, or traceability.

A capability with independent technical decisions does not qualify. Neither does size: a large, cross-domain intent with a clear goal stays one intent. Never split because the capability is technically separable, the module can be built or tested alone, the feature needs substantial research, the system spans several domains, the parent will produce several Specs, or the document has become large.

## 5. Core Invariants

| # | Invariant |
|---|---|
| 1 | **Confirmed meaning is the user's.** Never silently change a confirmed goal, constraint, decision, or the confirmed operation order; a product choice that belongs to the user goes to the user (`../../references/cross-layer-coordination.md` §2.5.b), even when the agent has a recommendation. Within an authorized goal the owning layer fixes its own contradictions — that is not a second approval round. |
| 2 | **Modify before creating.** If the objective is the same, modify the existing intent and preserve its ID. Creation is the exception. |
| 3 | **IDs are immutable.** The intent ID is never re-numbered or reused, and a stable item ID is never reassigned to a different meaning (`references/item-ids.md`). |
| 4 | **Separate what is known from what is assumed.** Verified facts carry a source and date; unverified claims live in `# Unknowns`; agent inference is labeled `(assumed)` and never appears as a confirmed decision. A user's claim is a fact about what the user said, not a fact about the world. |
| 5 | **Keep history.** Material edits, splits, and migrations are recorded with date, old meaning, new meaning, and reason; superseded items stay traceable; downstream pointers still resolve. |
| 6 | **Stay inside the layer.** Intent does not write Specs, contracts, module designs, or code, and does not modify another layer's artifact; it returns a result for that layer's owner to apply. Never claim work that did not happen: accepted feedback is not downstream synchronization. |
| 7 | **Archive is not downstream completion.** An Intent may be archived while Spec, Architecture, and Module work are pending, and archive still requires its own completion check (`references/lifecycle.md` §5). |
| 8 | **One authoritative location.** One business meaning has one home — never restate a goal, a constraint, or a decision in a second section; point at it instead. |
| 9 | **Intent stays minimal.** Content enters the authoritative sections only through the inclusion test (§1.1). A longer document is not a better document, and an expectation ("make money", "be fast") is never a per-instance system guarantee. |
| 10 | **A named, bounded edit is executed, not re-planned.** When the user points at an object and asks for a bounded change to it, that object is edited under the current authorization — not a sweep of the repository, a restructuring of untouched sections, a clarification round, or a reconcile. |

## 6. Reference Loading

Load a reference only when its trigger fires. Do not read unrelated references, and do not re-read an unchanged file in the same context.

| Reference | Load it when | Do not load it for |
|---|---|---|
| `references/lifecycle.md` | Creating, matching, splitting, modifying, archiving, reopening, resuming, or triaging feedback | `list`, `show`, `tree`; plain feedback triage |
| `references/clarification.md` | A user decision is unresolved and must be asked, or a clarification round resumes | `list`, `show`, `tree`; editorial edits; a bounded edit that changes no goal, constraint, or product choice |
| `references/research.md` | A fact must be established, a claim verified, or conflicting sources reconciled | Decisions the user owns; `list`, `show` |
| `references/intent-template.md` | Creating a new `INTENT.md` or restructuring an existing one | `list`, `show`; small content edits |
| `references/item-ids.md` | Assigning, renaming, moving, or citing a stable item ID | Prose edits that touch no item ID |
| `../../references/cross-layer-coordination.md` | Work or feedback crosses an authority layer, or an ownership / authorization question arises | In-Intent work that stays in this layer |
| `../../references/change-impact.md` | A changed item may affect a downstream artifact, contract, or evidence | Content that provably does not move downstream |
| `../../references/verification.md` | A formal independent-verification trigger fires, or a review result must be triaged | Ordinary capture and routine archive |

If a rule requires one of these files, read it before acting on that rule — never reconstruct a protocol from memory because its reference is not loaded; load it, or state that the capability is unavailable and keep the return point. `list`, `show`, and `tree` load **no** reference file; a bounded scoped edit loads only what its escalation point names. Reference loading is itself proportional work: load the file the current step needs, not the directory.

## 7. Hand-off

The skill never writes code or designs solutions. Its output is the `INTENT.md`, and a downstream Spec reads it directly — the Spec Agent cites the item IDs it consumes (`INT-001/G-01`), so a later Intent change can be detected.

`# Spec Input` is therefore **optional and short**: a handoff map, never a copy — the goals and constraints the Spec must satisfy by item ID, the product choices it must return to the user rather than settle, and the impact scope when known. An Intent may produce zero, one, or many Specs; hierarchy does not determine Spec decomposition.

When the next stage cannot be invoked — unavailable, out of authorization, or not installed — say so plainly and leave the pointer: the `INTENT.md` path, the item IDs a downstream layer must satisfy, the open product choices it must return, and the impact scope. Never state that a downstream artifact was updated when it was not (invariant 6).

`# Clarified Intent` states the user's **operation sequence from a real starting point** — what the user knows and provides at the start, who supplies each input, the confirmed order, and what the user observes when it works. Keep it at user level: UI detail, error handling, and system state transitions belong to Spec (`../../references/cross-layer-coordination.md` §8), but do not drop a step or blur the order when a downstream reader could otherwise misread the core flow.

## 19. Reconcile Trigger

During `new`, and during any material modification that is **not** a bounded scoped edit, run one lightweight semantic check: does this change expose a material semantic overlap, shared abstraction, inherited-constraint conflict, or incompatible goal with an existing intent?

**No** → continue the normal flow. **Yes** → name the candidate intents and the reason, then use `/intent-reconcile` under the authorized goal; if invocation is unavailable, follow that Skill's file when the tools permit, otherwise record the missing capability and the return point. Reconciliation that changes confirmed product meaning needs a user decision (`../../references/cross-layer-coordination.md` §2.5.b).

Domain similarity — same tech stack, same data source — is not sufficient on its own, and do not loop: at most one reconcile suggestion per change. A requested parent/child split is **not** a reconcile case (§4.1); an inconsistency inside one document is a consistency issue (`references/intent-template.md` §7), fixed in place.
