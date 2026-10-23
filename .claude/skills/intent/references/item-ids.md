# Stable Item IDs

The single authority for stable item IDs inside an Intent. `SKILL.md` §17
introduces the format; this file governs assignment, immutability,
migration, and downstream citation. Load it when assigning, renaming,
moving, superseding, or citing an item ID — not for prose edits that touch
no item.

## 1. Format

```text
INT-001/G-01  Goal
INT-001/C-01  Constraint
INT-001/S-01  Success criterion
INT-001/D-01  Decision
```

The prefix is always the owning intent ID. The kind letter is fixed: `G`
goal, `C` constraint, `S` success criterion, `D` decision. The number is
sequential within that kind inside that intent, zero-padded to two digits.

## 2. When to Assign

Assign an ID only to content with real traceability value:

- a confirmed goal the downstream layers must satisfy;
- a hard constraint that must not be weakened;
- a success criterion that decides acceptance;
- a confirmed decision whose reasoning matters later.

Plain explanation, examples, and minor text do not need IDs. Do not invent
IDs that do not exist yet, and do not retrofit IDs across existing intents
in bulk — assign them when a downstream artifact needs to reference them.
Not every intent uses item IDs.

## 3. Immutability

- The intent ID (`INT-NNN`) is immutable: never re-numbered, never reused
  (`SKILL.md` §2).
- An assigned item ID is never reassigned to a different meaning.
- A wording-only edit keeps the ID. The same `INT-001/C-01` still refers to
  the same constraint after a paraphrase or reformatting.
- IDs are never recycled after deletion: a removed item keeps its ID in the
  history so old references still resolve.

## 4. Superseding

When the meaning of an item materially changes:

1. Keep the original entry as a historical record, for example
   `- **D-01** (2026-10-08): <original> — superseded by D-05 on 2026-10-20.`
2. Add the new content under a **new** ID.
3. Do not silently reuse the old ID for the new meaning.

A phrasing change that preserves the meaning is not a supersession — keep
the ID and update the text.

## 5. Migration Between Intents

When an item moves to a child intent, or is split across intents:

- Record the migration in the source intent's `# Resume Notes`, for example
  `moved to INT-002/C-01 on 2026-10-20`.
- Add a reciprocal pointer in the receiving intent.
- Keep the original entry resolvable: the old location still points at the
  new location or at the historical record, so a downstream artifact citing
  `INT-001/C-01` still finds the content (`lifecycle.md` §3).
- A moved item keeps its kind and number when it stays the same constraint
  or decision; a genuinely different constraint needs a new ID.

## 6. Downstream Citation

A Spec, Architecture, Module, or Implementation document cites an Intent item
as `INT-NNN/X-NN` — for example `INT-001/C-01` or `INT-001/G-01`. The
downstream document names the intent it consumed (`source_intents`), so an
Intent change can be located and assessed.

If a downstream reference has no item ID, it may fall back to `INT-NNN` plus
the file and section location. When that reference is edited, add a precise
citation to the owning document.

The Intent skill never edits a downstream artifact to add or fix an item ID;
it returns the correction for that layer's owner (`SKILL.md` §14,
invariant 7).

## 7. In `INTENT.md`

Use a bold item ID followed by the content:

```markdown
# Constraints and Success Criteria

## Hard Constraints

- **C-01**: 历史回测不得使用未来数据。
- **C-02**: 资产净值必须按统一计价基准计算。

## Success Criteria

- **S-01**: 同一数据集的回测结果可复现。

# Decisions

## Confirmed Decisions

- **D-01** (2026-10-08): 支持策略驱动的仓位调整。
```

The item ID sits inside the canonical section that owns the content. The
`# Spec Input` handoff map cites those IDs; it does not copy the text
(`SKILL.md` §13).
