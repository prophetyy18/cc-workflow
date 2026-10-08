# Semantic Reconciliation Methodology

The 7-step algorithm used by the `intent-reconcile` skill. Read on demand when invoked. Each step produces intermediate output that feeds the next.

## Step 1 — Reconstruct Intent Meaning

For each input intent, read the full `INTENT.md` and extract:

- **Intended outcome** — the result the user wants.
- **Scope** — what is in / out.
- **Confirmed decisions** — from `# Decisions`.
- **Constraints** — from `# Constraints and Success Criteria`.
- **Success criteria** — measurable goals.
- **Relevant facts** — from `# Facts and Research`.
- **Unknowns** — from `# Unknowns`.
- **Relationships** — `parent`, `related`, `impact_scope`.
- **Existing Spec dependencies** — Specs that cite this intent (search downstream artifacts for the intent ID).

Distinguish user-stated content from agent-inferred. The latter is labeled `(assumed)` in INTENT.md and should be re-validated in this step, not blindly accepted.

Pay special attention to the **actual scope** of each constraint. A constraint phrased as "passive strategies do not rebalance" applies to passive strategies, not the entire system. If the original wording is ambiguous, keep the ambiguity and flag it for the user — do not narrow or broaden it on the agent's preference.

## Step 2 — Identify Semantic Relationships

A pair can have multiple relationships. Record all that apply.

| Relationship | Definition |
|---|---|
| **Equivalent** | Same outcome, different expression. |
| **Specialization** | One is a specific case of a more general goal. |
| **Overlap** | Share some goals or behaviors, but each has independent content. |
| **Dependency** | One needs the other to deliver some capability. |
| **Conflict** | Two requirements cannot both hold under the same scope and conditions. |
| **Independent** | No material semantic relation; topical similarity alone does not count. |

These are analysis results for the report. They are not lifecycle states and do not need to be persisted in `INTENT.md` frontmatter.

## Step 3 — First-principles Analysis

For any detected overlap or conflict, ask:

1. What outcome is each intent actually trying to achieve?
2. What business behaviors are essential to both?
3. What conditions, rules, or scenarios cause the differences?
4. Which constraints hold under any scenario?
5. Which constraints only hold under a specific mode or scenario?
6. Is there a more general concept that explains both?
7. Does unifying reduce real conceptual duplication and conflict?
8. Does unifying damage any original goal or introduce scope creep?

Prefer the **smallest sufficient common abstraction** that covers all currently-valid behaviors. Do not invent abstractness for its own sake. A unification that drops a specific scenario's behavior is not a valid unification.

## Step 4 — Evaluate Reconciliation Options

| Option | Use when |
|---|---|
| **A — No restructure** | Surface similarity only, or constraints apply to different conditions. Add a `related` link if useful. |
| **B — Modify existing** | A parent (or one of the pair) intent's concept can be reasonably generalized while keeping its identity. Preserve its ID. |
| **C — Extract shared parent** | Original intents have clear independent identity, but a shared upper goal genuinely unifies maintenance. Do not extract a parent just for tidy structure. |
| **D — Clarify scope** | Apparent conflict is actually a global constraint that's too broad. Narrow it to the correct scenario. |
| **E — Preserve genuine conflict** | Goals are genuinely incompatible. Surface the trade-off to the user. Do not silently override either side. |

Pick the **smallest valid option**. If A is sufficient, do not jump to C.

## Step 5 — Validate Preservation

Before proposing a restructure, verify:

- All still-valid user goals retained.
- Important original behaviors retained.
- Success criteria preserved.
- No confirmed limit dropped.
- No unauthorized new goal introduced.
- No intent's identity silently changed.
- No other related intent affected adversely.
- No existing Spec reference broken.
- No architecture recommendation smuggled in as a confirmed user decision.

A general statement that loses a specific scenario's behavior is **not** a valid generalization. If a scenario's behavior would be lost, retain it as an explicit constraint or acceptance criterion in the appropriate place.

## Step 6 — Propose

Produce the report (see SKILL.md §5). The recommendation must include:

1. Shared goals found.
2. Real conflicts or duplications.
3. Proposed common concept.
4. How each intent should change.
5. How original goals and decisions are preserved.
6. Which intents / Specs are impacted.
7. Open questions for the user.

If the proposal is material, **wait for explicit user confirmation** before editing.

## Step 7 — Apply Safely

After authorization:

- Edit only the minimum necessary scope.
- Preserve existing intent IDs.
- Maintain valid `parent` / `related` relationships (no cycles, no missing refs).
- For an `archived` intent needing material change, follow the existing reopen rule first.
- Update `# Clarified Intent`, `# Constraints and Success Criteria`, `# Decisions`, `# Relationships and Impact`, `# Spec Input` as affected.
- Do not touch unrelated research records.
- Do not delete the original user wording from `# Original Intent`.
- Log material changes in `# Resume Notes` (old meaning, new meaning, why).
- Preserve references to existing stable item IDs, or record a migration map.
- Check for dangling references, cycles, semantic conflicts.

Git preserves history. Do not build a separate version system.

If editing multiple intents, form a complete change plan before executing. If a partial failure occurs, **stop and report**; do not leave a half-applied contradictory state. Do not silently override unrelated work in the user's working tree.
