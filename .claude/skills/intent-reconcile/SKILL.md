---
name: intent-reconcile
description: Reconcile semantic overlap, conflicts, and shared abstractions across two or more intents. Use when the user asks to compare, merge, generalize, or resolve conflicts between intents (e.g., "do INT-001 and INT-002 overlap?", "should I merge these?", "find the common abstraction", "INT-002's constraint conflicts with INT-001"). Also invoked when the intent skill detects material semantic overlap, shared abstraction, or inherited-constraint conflict during new / modify / refine.
allowed-tools: Read, Edit, Write, Glob, Grep, WebFetch, WebSearch, Bash(date*), Bash(git*)
---

# Intent Reconcile Skill

Compare two or more intents and reconcile their semantic overlap, conflicts,
and shared abstractions. Apply the shared impact authorization rule: a
necessary correction that preserves confirmed meaning can proceed under an
authorized goal; a new product choice goes to the user.

## 1. What this skill does

- Reads the relevant `INTENT.md` files and reconstructs each one's meaning (outcome, scope, decisions, constraints, success criteria, facts, unknowns, relationships).
- Identifies semantic relationships: **Equivalent / Specialization / Overlap / Dependency / Conflict / Independent**. A pair can have multiple.
- Runs a first-principles analysis to find the smallest valid common abstraction, distinguishing outcomes that vary by mode or scenario from invariants.
- Evaluates reconciliation options: no-restructure, modify-existing, extract-shared-parent, clarify-scope, or preserve-genuine-conflict.
- Records its reasoning and applies changes within current authorization.

## 2. What this skill does NOT do

- Does not write code, define APIs, or design architecture.
- Does not produce Specs. The Spec skill owns that.
- Does not silently change confirmed product meaning. Use cross-layer §2.5.b.
- Does not recursively invoke itself. Return to the requesting Skill or Main Agent.
- Does not auto-trigger on every intent change. See `intent/SKILL.md` §19 for the lightweight detection rule.

## 3. Invocation

User can invoke directly:

```text
/intent-reconcile INT-001 INT-002
/intent-reconcile INT-001 INT-002 INT-003
```

Or via natural language:

- "do INT-001 and INT-002 overlap?"
- "should I merge these two intents?"
- "find the common abstraction"
- "can these two user outcomes be described by one shared goal?"
- "INT-002's constraint seems to conflict with INT-001"
- "reconcile these intents"

The intent Skill may enter reconciliation when it finds a material semantic
overlap or conflict. The Main Agent uses the native Skill when available;
otherwise it reads and follows this file within its current authorization.
Preserve the original task's return point.

## 4. The 7-step algorithm (summary)

Full algorithm in [references/methodology.md](references/methodology.md). Quick reference:

1. **Reconstruct meaning** — outcome / scope / decisions / constraints / success criteria / facts / unknowns / relationships. Distinguish user-stated from agent-inferred (the latter is labeled `(assumed)` in INTENT.md and should be re-validated here).
2. **Identify relationships** — Equivalent / Specialization / Overlap / Dependency / Conflict / Independent. A pair can have multiple.
3. **First-principles** — what outcome, what varies by mode, what is invariant, is there a smaller common abstraction that covers all valid behaviors.
4. **Evaluate options** — A no-restructure · B modify existing · C extract shared parent · D clarify scope · E preserve genuine conflict.
5. **Validate preservation** — all valid user goals retained · no unauthorized new goals · no broken Spec references · no architecture recommendation smuggled in as user decision.
6. **Decide authorization** — record the recommendation and impact; ask the user only for an unresolved change to confirmed meaning (§2.5.b).
7. **Apply safely** — minimum-scope edits · preserve IDs · maintain relationships · log changes · reopen archived intents where required.

## 5. Output format

```text
## Reconcile Report: INT-001 + INT-002

### Per-intent summary
- INT-001: <one-sentence outcome, scope, hard constraints>
- INT-002: <one-sentence outcome, scope, hard constraints>

### Semantic relationships detected
- <relationship>: <justification>
- (a pair can have multiple)

### First-principles finding
- Shared outcome: <…>
- What varies: <…>
- What is invariant: <…>
- Smallest valid common abstraction: <… or "none — keep them separate">

### Recommendation
- <Option A | B | C | D | E>: <what to do, why>

### Preservation check
- All valid user goals retained?: yes / no + notes
- Existing Spec references affected?: yes / no + list
- Other intents affected?: yes / no + list
- Authorized behavior at risk?: yes / no + notes

### Open questions for the user
- <unresolved items>
```

For an authorized correction, apply minimum-scope edits and return to the
original work. If a product choice remains open, report the exact alternatives
and keep the affected authority open.

## 6. Boundaries with Spec and Architecture

This skill expresses shared outcomes in user language (for example, "users
need to reach the same result in both modes"). Spec derives the system
guarantees from those outcomes. This skill does **not**:

- Name specific mechanisms (Callback, Hook, Queue, Event Bus, etc.).
- Define module boundaries, public contract schemas, or API ownership.
- Edit Specs. If a Spec has already been written against the affected intents, flag it for review; do not silently alter it.
- Treat an architecture recommendation as a confirmed user decision.

When the analysis surfaces a downstream architectural impact, record the **needed capability** and **impact**, not the implementation.

## 7. Hard rules

1. **Authorize by impact.** Apply cross-layer §2.5.b; material wording may be a necessary correction, while any change to confirmed product meaning requires a user decision.
2. **Preserve authorized behavior.** A constraint, decision, or behavior the user confirmed is binding until they change it. Do not silently drop or weaken it.
3. **Distinguish stated from inferred.** When reconstructing intent meaning, label anything the agent inferred as "(assumed)".
4. **No architecture.** Shared abilities are expressed in intent language, not as API names or module layouts.
5. **No recursive auto-trigger.** Return control to the requesting Skill or Main Agent; it resumes the original goal when prerequisites close.
6. **Preserve traceability.** When moving or merging content, log in `# Resume Notes` and `# Relationships and Impact`. Existing Spec references must still resolve.
7. **Domain similarity is not enough.** Two intents sharing a tech stack or data source are not necessarily a reconcile candidate.
8. **Archived intents follow the reopen rule.** Reopen before editing authoritative content, using impact-based authorization.
9. **Reconciliation is not Spec.** Flag affected Specs for review; do not silently change them.
10. **Lightweight by default.** If the candidates only need a `related` link, suggest that. Do not run the full algorithm.
