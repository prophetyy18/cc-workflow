---
name: spec
description: Convert clarified user Intent into complete, verifiable, traceable system requirements. Use when the user wants to define what the system must do (functional + non-functional + cross-capability correctness), create a SPEC from an Intent, review requirement coverage, or check for ambiguity and risks. Located between Intent and Architecture in the workflow. Triggered by questions like "spec out INT-001", "what does the system need to do?", "review SPEC-002", "is INT-001 covered?", or "create requirements for …".
allowed-tools: Read, Edit, Write, Glob, Grep, WebFetch, WebSearch, Bash(date*), Bash(git*)
---

# Spec Skill

Transforms a clarified user Intent into **complete, verifiable, traceable system requirements**. Spec is the authoritative layer for "what the system must guarantee" — it does not design how. Architecture decides module and public capability ownership; Module Design defines the owned public contract content and internal design.

## 1. Layer Boundaries

| Layer | Owns | Does not own |
|---|---|---|
| **Intent** | User objectives, goals, constraints, confirmed decisions, success conditions | System behavior, modules, APIs |
| **Spec** (this skill) | System capabilities, functional & non-functional requirements, system invariants, cross-capability correctness, acceptance conditions | Module names, API shapes, schemas, algorithms, storage choices |
| **Architecture** | Module boundaries, capability and public contract ownership, required cross-module semantics, dependency direction | Concrete API / schema fields and internal implementation |
| **Module Design** | Provider-owned public contract content, API details, schemas, algorithms, internal structure | Module or contract ownership; why these capabilities exist |

**Spec describes what the system must guarantee. It does not decide how.**

## 2. Subcommand Routing

Read `$ARGUMENTS`. First token is the subcommand, the rest is the target.

| Subcommand | Target | Behavior |
|---|---|---|
| (empty) or `help` | — | Show this help |
| `<intent-id>` (bare) | intent id | Primary entry: read intent, run risk review, determine Spec scope |
| `new` | `<intent-id> [scope]` | Create a new Spec for an intent (optionally scoped) |
| `list` | — | List all Specs grouped by status |
| `show` | `<spec-id>` | Print the full `SPEC.md` |
| `resume` | `<spec-id>` | Continue work on an existing Spec |
| `review` | `<spec-id>` | Run risk / completeness / traceability / conflict check |
| `coverage` | `<intent-id>` | Analyze how well an Intent's goals are covered by existing Specs |
| `archive` | `<spec-id>` | Finalize Spec after its completion gate |
| `reopen` | `<spec-id>` | Re-open an archived Spec with impact analysis |

If the subcommand is unknown, do not guess. Show help and stop.

## 3. Natural-Language Operations

| User intent (paraphrased) | Action |
|---|---|
| "spec INT-001", "what does the system need to do?" | bare entry → propose Spec |
| "new spec for INT-001 with scope X" | `new` |
| "list specs", "what specs do we have?" | `list` |
| "show me SPEC-001" | `show` |
| "review SPEC-001", "check this spec" | `review` |
| "is INT-001 covered?", "what's the coverage?" | `coverage` |
| "archive SPEC-001", "we're done with this" | `archive` after the completion gate |
| "确认，继续" / "SPEC-001 没问题了" (after a recent completion proposal) | `archive` + Downstream Routing — do not prompt a second time |
| "I need to change SPEC-001 but it's archived" | `reopen` with impact and authorization check |

**Modification is the default, not creation.** A Spec for the same capability is modified, not duplicated.

## 4. Identity & Storage

Stable Spec ID: `SPEC-NNN` (3-digit zero-padded). Immutable. Re-numbering is not supported.

Storage layout (flat, parallel to `docs/intents/`):

```text
docs/specs/
├── SPEC-001/
│   ├── SPEC.md
│   └── research/             (optional, only when deep research was done)
└── SPEC-002/
    └── SPEC.md
```

The `id` field in frontmatter is the source of truth. Titles, `source_intents`, and other metadata can change.

## 5. Subcommand: bare `/spec <intent-id>` (primary entry)

Use when the user wants to start spec work but hasn't said "new" explicitly.

1. Load `INTENT.md`. Read its `parent` and directly related intents for context.
2. Read any existing Specs that cite this intent. Note their scope.
3. **Risk review** (see [references/review.md](references/review.md#1-risk-review-during-intake)):
   - User goal clarity, constraint compatibility, fact verification, unprovable assumptions, infeasible core requirements, high-impact risks, Blocking Unknowns.
   - For load-bearing factual claims, also follow [references/fact-verification.md](references/fact-verification.md): classify as Verified / Supported / Unverified; defer or resolve before closing the Spec.
4. **Capability discovery** (see §7): map the intent to system capabilities.
5. **Spec decomposition decision**: one Spec, or several? Or does a related Spec already exist?
6. Record the scope and its source Intent items; reuse an existing Spec when it owns the same capability.
7. Proceed to `new` or `resume` under the user's Spec or whole-goal instruction. Apply cross-layer §2.5.b if decomposition exposes a material product choice. A routine capability boundary does not require another approval round.

## 6. Subcommand: `new <intent-id> [scope]`

Create a new Spec.

1. Re-run the risk review. If Blocking Unknowns exist, surface them — do not silently fill in assumptions.
2. Read the source intent again. Identify the scope: which capabilities this Spec will cover.
3. If `[scope]` is given, narrow to that. Otherwise infer the smallest useful scope from the Intent and existing Specs; ask only if plausible choices change confirmed product scope (§2.5.b).
4. **Check existing Specs**:
   - Does an existing Spec already cover part of this scope? If yes, surface — modify existing first, don't duplicate.
   - If the §8 split test passes, choose the owning Spec for each behavior
     and define any required cross-Spec invariant once with participating
     Specs citing it.
5. **Generate Spec ID**: scan `docs/specs/SPEC-*/SPEC.md`, find max `SPEC-NNN`, take next.
6. Create `docs/specs/SPEC-NNN/SPEC.md` with `status: active`. Create `docs/specs/` if missing.
7. Fill frontmatter (`id`, `title`, `status`, `source_intents`, `created`, `updated`).
8. Write each section per the template (§12). Use `_TBD_` for sections that don't apply yet.
9. Persist after every meaningful change.

Duplicate ID is never overwritten. If collision, ask the user to disambiguate.

## 7. System Capability Discovery

**Always derive system capabilities from user goals before thinking about modules.**

For a large intent, present a concise capability map before writing Requirements. Each capability should answer:

- What system outcome does it produce?
- Which user goal does it serve?
- Does it depend on or coordinate with other capabilities?
- Is it already covered by an existing Spec?
- Does it have key Unknowns?

This map is **not** a fixed template. Derive from the actual intent. Don't pad with speculative capabilities. Don't list technical implementation details (e.g., "PostgreSQL schema" — that's Architecture).

The map can live in the Spec's `# Scope and Sources` or `# System Capabilities` section. No separate capability graph database.

## 8. Spec Decomposition

One Spec per independent, verifiable system behavior or behavior group. Not per module, per code directory, per intent, or per API. First check existing Specs: extend the Spec that already owns the behavior instead of creating a duplicate.

Split only when **both** conditions hold:

- The behaviors have a clear boundary; each side can be described without silently changing the other side's guarantee.
- Each side has its own observable acceptance conditions.

Different change cadence and easier review can favor a split after both conditions hold; neither alone justifies one. Keep heavily coupled behavior together. Before splitting, identify any guarantee that only holds when the sides compose, choose one authoritative Spec item and stable ID for its definition, and make every participating Spec cite it with its own participation and system-verification obligation. Do not copy competing definitions of the same invariant.

Do not split just because:

- The capability touches two modules.
- There are two technical options.
- There are two sets of APIs.
- The requirement doc is long.
- It needs many tests.

**One Intent → many Specs. Many Intents → one Spec.** This is normal. The `source_intents` field lists all that apply.

## 9. Subcommand: `list`

1. `Glob docs/specs/SPEC-*/SPEC.md`.
2. Read frontmatter of each.
3. Print a compact table. `active` first, then `archived`. Columns: `id`, `title`, `status`, `source_intents` (count), `updated`.

## 10. Subcommand: `show <spec-id>`

Print the full `SPEC.md`. No editing. If ID is ambiguous, list candidates.

## 11. Subcommand: `resume <spec-id>`

1. Load `SPEC.md`.
2. Check Git and apply `../../references/change-impact.md` to changed
   source Intent items, REQ/INV IDs, acceptance and contract semantics.
   Record affected downstream owners and evidence, not just file names.
3. Read `# Resume Notes` to see where the last session left off.
4. Read `# Decisions` first. Do not re-ask answered questions.
5. Continue clarification or research from the open frontier.
6. Update `# Resume Notes` with the open impact chain and next action.

## 12. SPEC.md Template

```markdown
---
id: SPEC-NNN
title: <system capability or behavior>
status: active
source_intents:
  - INT-NNN
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# Scope and Sources

<which Intent(s) this Spec consumes; the user goal it serves; which other Specs it relates to or depends on.>

# System Capabilities

<concrete system behaviors this Spec requires. Each should be testable. No module names, no API shapes.>

# Requirements

## Functional

- **REQ-001** (source INT-001/G-01): <behavior with preconditions, trigger, input, expected behavior, state change, output, edge cases, failure>
- **REQ-002**: <...>

## Non-Functional

- **REQ-N01** (source INT-001/C-01): <correctness / integrity / reproducibility / security / performance / observability / recoverability — only what applies>

## Derived

<Requirements derived from existing user constraints to guarantee system correctness, with reasoning. Mark "(derived — justification: ...)" inline.>

# System Invariants and Dependencies

<cross-capability / cross-Spec correctness constraints that must always hold. Define each invariant once with a stable ID in its authoritative Spec; participating Specs cite that ID and state their participation and system-verification obligation. Examples: "no future-data leakage", "unified NAV calculation", "deterministic replay".>

# Acceptance and Verification

<how to verify each Requirement / invariant. Three levels when useful:
- **Capability Verification** — does this Spec meet its own Requirements?
- **Contract Verification** — do other Specs / modules honor their inter-Spec contracts?
- **System Verification** — do the combined capabilities still meet the original user goal? System Verification must include the full user sequence from the real starting state, classified per `verification.md` §4.7. Component / unit tests and mocks alone are not System Verification.>

# Architecture Handoff

<what Architecture must decide. Required capabilities, required contract semantics, but not actual API names or module names. Items left open: "Architecture must assign capability X to a module", "Architecture must provide a contract for behavior Y".>

# Unknowns and Upstream Feedback

- **Unknown**: <what is unknown, why it matters, how to resolve>
- **Feedback to Intent**: <if a user goal is ambiguous, contradictory, or infeasible, route via `/intent feedback <intent-id> <source>`>
- **Feedback to Architecture**: <if a module / contract concern arises, note here for the Architecture layer; do not silently change Intent>

# Resume Notes

<short status: last action, what's next, key open questions.>
```

**Omit or trim sections that don't apply.** Empty sections are fine. **Do not pad with fake content** to make the document look complete. Use `_TBD_` for sections genuinely pending.

## 13. Requirements Method

See [references/requirements.md](references/requirements.md) for:

- What makes a Requirement testable
- Functional vs Non-functional vs Derived categories
- How to assign Requirement IDs (`SPEC-NNN/REQ-NNN`)
- What to source from Intent (item IDs, file+section, etc.)
- How to identify cross-capability invariants

### 13.1 End-to-end user sequence (anchor to shared rule)

Check coverage in both directions against the source Intent's
`# Clarified Intent`: each in-scope user-visible transition needs a
Requirement or explicit System Verification obligation (name the
owning Spec for out-of-scope steps), and each user-facing
Requirement needs a source goal or transition. A list
of fields or features is not proof that the next action is
reachable from the preceding state. Technical and Derived
Requirements may instead trace to a constraint or correctness
need. Apply `cross-layer-coordination.md` §8.

## 14. Subcommand: `review <spec-id>`

Run a structured review of a Spec. The default execution delegates to the read-only `independent-reviewer` subagent (defined in `.claude/agents/independent-reviewer.md`) in a fresh context, so the review does not inherit the author's reasoning. This Skill owns the **independent triage**, the user-decision loop, the **automatic post-fix verification**, and the resolution path; the Reviewer owns the evidence-based findings.

**Trigger policy.** An explicit `/spec review` runs Mode A. For
automatic Mode A/B/C triggers, use `.claude/references/verification.md`
§3; for loop bounding, use §6. Trivial wording edits use a Self-check.

### 14.1 Delegation procedure

1. **Confirm the target.** Resolve `<spec-id>` (must exist; load `docs/specs/<spec-id>/SPEC.md`).
2. **Locate authoritative sources.** Read `source_intents` from the target's frontmatter; load each source Intent's `INTENT.md`. Read any Specs cited as related in `# Scope and Sources`. Note their `status`.
3. **Load the Review Criteria.** Read [references/review.md](references/review.md#2-spec-review-spec-review-spec-id) so the Reviewer knows the criteria, and so this Skill can interpret findings.
4. **Build a neutral delegation message.** See the template in [references/review.md §2.1](references/review.md#21-delegation-message-template). The message must contain: **Review Type, Review Mode** (`Independent Review` for Trigger A; `Targeted Resolution Verification` for Trigger B), **Target**, **Authoritative Sources**, **Review Criteria**, **Scope**, **Method**, **Output**, **Permissions**. For Trigger B, also include the original finding evidence, the authoritative basis for the correct outcome, and an explicit request to re-derive. **Do not** include author conclusions such as "this Spec looks correct", "the fix is sound — please confirm", or pre-baked judgments about facts.
5. **Launch the Independent Reviewer.** Use the Agent tool with `subagent_type: "independent-reviewer"` and the neutral delegation message as the prompt. This starts a **non-fork subagent** with read-only access (no Edit / Write / Bash) and no persistent memory. Verify the call succeeded. If the call fails (see §14.2), report honestly; do not fake a review.
6. **Receive the report.** The Reviewer returns a structured Markdown report (see `.claude/agents/independent-reviewer.md` §3). The report includes the Mode that produced it; preserve that label.
7. **Independent Triage.** This Skill does **not** rubber-stamp the Reviewer's recommendations. For each finding, run the Triage procedure in [references/review.md §2.7](references/review.md#27-triage-procedure). For cross-layer issues, load the cross-layer rules from `.claude/references/cross-layer-coordination.md`.
8. **Resolution paths.** Each triaged finding produces a resolution path owned by the **highest necessary** authority whose content must change. Most findings will be triaged to: Accept (modify Spec wording), Reject (with evidence), Request evidence, Redirect (to Spec / Architecture / Module / Implementation / Verification / User), or already covered by an existing downstream guarantee. **Do not** route every finding to Spec.
9. **Closure language discipline.** Record `Review Executed` (Mode A) or `Targeted Verification Executed` (Mode B) after this Skill finishes. Do not record `Authority Resolved` until the actual authoritative content has been changed (or formally rejected). Do not record `Implementation Verified` — that belongs to Verification. See [references/review.md §2.7.4](references/review.md#274-closure-language-discipline) and `.claude/references/verification.md` §7.
10. **Review is read-only; authorized resolution is not.** The Reviewer and triage do not edit. The Spec owner applies corrections covered by the current task authorization under cross-layer §2.5.b, then obtains applicable post-fix verification. A change to confirmed product meaning still needs a user decision.
11. **Post-fix verification (Trigger B).** When an Accept verdict has been authorized and the Spec edit has been applied, evaluate whether the fix meets the Trigger B criteria in `.claude/references/verification.md` §3. If yes, delegate a follow-up `Targeted Resolution Verification` to a fresh Independent Reviewer with the same scoped basis — do not rely on the Triage verdict alone to claim the issue is closed. See §14.6 for the procedure.

### 14.2 If the Independent Reviewer cannot be spawned

Use `verification.md` §6.3.a: preserve the scoped basis and return point,
diagnose and retry at most once, then keep any required Independent Review
open. Self-check can aid diagnosis but cannot substitute for that gate.

### 14.3 Reviewer reasoning frame

The Reviewer uses a **Derive → Locate** reasoning frame: derive what the authoritative sources require (Necessary Conditions, Design Choices, Unverified Assumptions), then locate where the target Spec misses, weakens, or contradicts a Necessary Condition. See [references/review.md §2.2](references/review.md#22-the-phases-the-reviewer-executes) and `.claude/agents/independent-reviewer.md` §3–§4. This Skill adds the independent triage in [references/review.md §2.7](references/review.md#27-triage-procedure) (Resolve + Validate).

### 14.4 Output: a structured findings report

For a standalone review, report findings. Under an already authorized repair
or whole-goal continuation, the owning Skill triages and applies necessary
corrections using cross-layer §2.5.b; ordinary suggestions do not expand the
task. The report format lives in `.claude/agents/independent-reviewer.md` §3.

### 14.5 Reviewer boundary

The Reviewer does not modify any authoritative content (`INTENT.md` / `SPEC.md` / `ARCHITECTURE.md` / `MODULE.md` / contracts / code), does not approve or archive the Spec, and does not trigger the next phase. See `.claude/agents/independent-reviewer.md` §0 (IS NOT) for the full boundary. Findings that point at another layer come back to this Skill, which routes them via `# Unknowns and Upstream Feedback` and the existing cross-layer feedback contract.

### 14.6 Automatic Post-fix Verification (Trigger B)

Apply `verification.md` §3 Trigger B and §6 to the changed Requirement,
invariant or acceptance scope. Give the Reviewer the original finding,
source Intent and changed REQ IDs; triage the returned report under §14.1.
Record `Authority Resolved` only after the necessary finding is actually
closed. Trivial wording changes use the shared self-check rule.

## 15. Subcommand: `coverage <intent-id>`

Check how well an Intent's important content is covered by existing Specs.

1. Load `INTENT.md`. Extract: goals and operation sequence (from `# Clarified Intent`), hard constraints (from `# Constraints and Success Criteria`), confirmed decisions (from `# Decisions`).
2. For each item and sequence transition, search Specs that cite this intent. Read the relevant Requirements and System Verification obligation.
3. Assess **semantic** coverage (not just ID reference):
   - **Covered** — Requirement actually satisfies the goal/constraint/decision.
   - **Partial** — Requirement addresses part of it; gap is named.
   - **Uncovered** — no Requirement addresses it.
   - **Unknown** — Insufficient information; clarify with the user.
4. Output a coverage table per item.
5. Suggest next steps: create new Spec, extend existing Spec, or note as residual gap.

Coverage is about **Requirement definition**, not implementation. It does NOT prove code is correct or tests pass. A large Intent does not need to be split into sub-Intents to achieve coverage.

## 16. Subcommand: `archive <spec-id>`

1. Load `SPEC.md`.
2. Render a final summary: capabilities, Requirements, invariants, acceptance conditions, handoff items.
3. **Authorization rule.** Apply cross-layer §2.5.b. A confirmed stage or
   instruction to complete the goal covers the necessary internal correction
   and archive once the completion checks pass. Ask only for an unresolved
   change to confirmed product meaning or a material trade-off outside that
   scope; archive is not a separate approval round.
4. **Completion check before archive, for both command and natural-language flows.** Verify by reading the actual artifact, not the prose summary:

   - saved;
   - no unresolved Spec prerequisite for the affected scope, regardless of
     its label; apply cross-layer §2.5.c/e, including applicable review and
     actual upstream closure, rather than deleting a Blocking marker;
   - important Requirements have sources and acceptance;
   - the source Intent's user sequence is covered in both directions per §13.1, including the real starting state and the next reachable action; `# Acceptance and Verification` specifies the full path rather than only isolated features;
   - no `_TBD_` or equivalent draft placeholder remains in a current Requirement, acceptance condition, or handoff claim;
   - traceability is valid;
   - no major upstream conflict;
   - cross-document References (e.g. `# Architecture Handoff`, "architecture depends on", "out of scope" lists) match the *current* authoritative state — not historical.

   Handoff obligations that Implementation owns (e.g.
   primary-source verification of a third-party library the Spec
   *named* but did not need to compute) are not Spec
   prerequisites; they are recorded but do not block archive.
   See `cross-layer-coordination.md` §2.5.e for the split.

   If a Blocking Spec-prerequisite issue exists, surface it and
   stop — do not silently archive. Non-Blocking issues are
   recorded in `# Unknowns and Upstream Feedback` and do not block.
5. Spec can be archived when its Requirements are sufficiently defined for downstream. Architecture / Module Design can proceed in parallel or later.
6. When authorized and the checks pass: set `status: archived`, update `updated`. Append a note to `# Resume Notes`.
7. **Downstream Routing (post-archive).** Run §19. Under an authorized
   whole-goal continuation, execute the next ready work after §2.5.c;
   for a standalone Spec request, report the route without extending scope.

## 17. Subcommand: `reopen <spec-id>`

`reopen` is the single edit path for an archived Spec — used for
both material changes and routine corrections. The difference between
them is the dimension of authorization (impact), not the lifecycle
shape.

1. **Determine the dimension** by impact (per
   `cross-layer-coordination.md` §2.5.b).
   - *Product change* — adds / removes / changes a confirmed goal,
     scope, key constraint, or user-visible behavior without a
     pinned upstream answer. Requires a fresh user decision.
   - *Necessary correction* — the confirmed upstream source pins
     the answer, including a contradiction between this Spec and its
     Intent. Use the same reopen and applicable review even if the
     old Spec wording changes materially; the authorized goal covers
     the correction under cross-layer §2.5.b.
2. **Apply the shape**:
   - Set `status: active`, update `updated`.
   - Apply the edit.
   - **Run the applicable completion checks** before closing:
     - Read actual unresolved conditions in `# Unknowns and Upstream
       Feedback`; apply §2.5.c/e regardless of their labels, including
       outstanding required review for this revision.
     - Read every Reference to other authoritative content; if
       any is now stale, reconcile or surface.
     - For material changes, the additional review /
       verification step that the user authorized (impact-
       specific) still produces the evidence the gate expects.
     - The check reads the actual artifact, not the prose
       summary.
   - If the gate fails, *keep `status: active`*; record the
     failing gate, what the artifact says now, and the resume
     position in `# Resume Notes`. Do not write a final
     confirmation until the gate passes.
   - If the gate passes, set `status: archived`, append a
     note to `# Resume Notes` explaining why it was reopened
     and what changed (`T1 fixture corrected from `5.00`
     to `10.00`, consistent with REQ-001 formula` is the kind
     of note a routine correction should write; a material
     change should also record what shifted in scope and
     which downstream layer is affected).
   - For material changes, also warn that downstream
     Architecture / Module Design / Implementation may have
     been written against the prior archived version.
3. **Route downstream** — for both dimensions, route a forward
   feedback to the downstream layers (Architecture / Module
   Design / Implementation) so they re-check dependent content.
   First classify the changed REQ/INV or acceptance item with
   `../../references/change-impact.md`; editorial-only changes end
   after a local reference check. For semantic changes, pass the
   item-level path, affected evidence and owner in the feedback.
   Spec does NOT itself modify Architecture / Module Design /
   Implementation / DESIGN files for either dimension.

## 18. Architecture Handoff

Spec output is the **contract** that Architecture consumes. Architecture will read it without prior conversation context. Therefore Spec must provide:

- Required capabilities — what the system must do.
- Required contract semantics — what guarantees different capabilities must provide to each other.
- System invariants — what must always hold across the system.
- Acceptance obligations — what must be verified end-to-end.
- Open architecture decisions — what Architecture must decide.
- Existing authoritative contracts — reference (do not redefine).

Spec does NOT name specific modules, APIs, schemas, algorithms, or storage choices. If the source Intent contains a technology decision the user made (e.g., "use PostgreSQL"), it may be referenced as **user constraint**, not as Spec content.

When existing architecture / contracts already exist, Spec may reference them but must not redefine or silently override.

## 19. Downstream Routing (post-archive)

After successful archive, perform a **lightweight downstream routing check**.
Spec identifies the route; Architecture owns Architecture decisions. The Main
Agent continues through the appropriate Skill when the broader task is already
authorized, using cross-layer §2.5.c before dependent work.

### 19.1 Routing basis

Read the current project's authoritative Architecture Baseline at
`docs/architecture/ARCHITECTURE.md`, a project-explicit adopted path, or its
named successor. A Skill install directory, empty stub, or unrelated sample
is not a project Baseline. Check Skill invocability separately from Baseline
availability; a file on disk does not prove native invocation is available.
Use the archived Spec's changed REQ/INV items and `# Architecture Handoff` as
the routing input.

### 19.2 Route

| Evidence | Next owning work |
|---|---|
| No trustworthy project Baseline | `/architecture init` (Route A) |
| Baseline exists, but capability ownership, public contract semantics, dependency direction, state authority, or invariant responsibility may be affected or is uncertain | `/architecture impact SPEC-NNN` (Route B) |
| Baseline names the affected owners, and current evidence shows its public capabilities and required semantics still cover the Spec | Module Design for those `MOD-<slug>` IDs (Route C) |

A missing Owner in an existing Baseline is Route B, not reinitialization.
Uncertainty calls for impact analysis, not an assumed Architecture revision.
Spec names the changed requirement semantics, the Baseline evidence or gap,
and the question Architecture must decide. Architecture alone classifies the
impact and revises ownership or public capability boundaries; the Provider's
Module Design owns concrete contract content. Spec does not edit either.

For Route C, cite the existing Owner and applicable capability/contract
semantics rather than inferring sufficiency from a filename. If evidence is
missing, use Route B. Under an authorized whole-goal task, the Main Agent
enters the owning Skill (or follows its file when native invocation is
unavailable), checks cross-layer §2.5.c, and preserves a return point when a
capability is genuinely unavailable. A standalone Spec request reports the
route without executing downstream work.

### 19.3 Handoff record

Record the affected REQ/INV IDs, needed capabilities and semantics, the
Baseline location or absence, the route and its evidence, the owning next
step, and any unresolved question. This is a short handoff in the current
Spec/Resume Notes, not another router artifact or a claim that downstream
work already happened.

## 20. Upstream Feedback

Spec may find problems at any layer. Route them by ownership level:

**Feedback to Intent** (via `/intent feedback <intent-id> <source>`):

- User goal ambiguity, conflict, or contradiction
- Confirmed constraint that conflicts with required system behavior
- Key fact that invalidates the original user goal
- Cross-Intent semantic conflict (route to Reconcile)

**Feedback to Architecture** (recorded in `# Unknowns and Upstream Feedback`, then to Architecture when it exists):

- Missing module responsibility
- Insufficient public contract
- Dependency direction conflict
- Capability ownership unclear

Spec does NOT modify Intent or Architecture. It only describes the problem, the evidence, and the requested resolution.

Record feedback in `# Unknowns and Upstream Feedback`; under an authorized
whole-goal task, the Main Agent enters the owning Skill or reads and follows
it when native invocation is unavailable. Report a genuinely unavailable
capability and preserve the return point. Do not claim an unperformed edit.

## 21. Hard Rules

1. **Spec is system behavior, not architecture.** No module names, no API shapes, no schemas, no storage choices, no specific algorithms.
2. **No code, no implementation.** Spec does not generate code or pseudo-code beyond minimal illustrative examples.
3. **Source traceability is mandatory.** Every Requirement cites a source (Intent item ID or file+section). No orphan Requirements.
4. **Stable Requirement IDs.** `SPEC-NNN/REQ-NNN` does not change on wording edits. Material semantic change requires a new ID with a migration note.
5. **No fabricated facts.** Technical facts must be verified with sources.
6. **No invented IDs.** Do not fabricate Intent item IDs or Requirement IDs.
7. **System-level correctness survives decomposition.** Cross-capability invariants must be captured, not lost.
8. **Coverage is semantic.** "Covered" requires the Requirement to actually satisfy the goal, not just share a name.
9. **Modify, don't create.** A Spec for the same capability is modified, not duplicated.
10. **Authorization follows impact.** Reopen, correction, review and archive needed to complete an already authorized goal may proceed under cross-layer §2.5.b and §2.5.c. Changing confirmed product meaning, scope or key constraints requires a fresh user decision. No status edit bypasses completion checks.
11. **Archive independent of downstream.** Spec can be archived before Architecture / Module Design is done.
12. **Material archived change → reopen.** Material changes to archived Specs follow the reopen flow.
13. **Lightweight by default.** Don't add approval workflows, multi-stage states, or extra lifecycle beyond `active` / `archived`.
14. **Do not invent Architecture.** If no architecture exists, leave module ownership open. Do not fabricate module names.
15. **When in doubt, classify as Architecture question.** Don't try to settle module / contract questions from Spec.
16. **Classify load-bearing facts.** For every load-bearing factual claim that supports a Requirement, classify as Verified / Supported / Unverified. Do not silently rely on unverified claims — record them in `# Unknowns and Upstream Feedback` with the required evidence and acceptance obligation, or block the Requirement until resolved. See [references/fact-verification.md](references/fact-verification.md).
17. **Documentation ≠ empirical evidence.** Runtime availability, data completeness, performance, and reconstruction accuracy cannot be closed as Verified from documentation alone. They require observation or measurement, or an explicit acceptance obligation on a downstream stage.
18. **One explicit confirmation is enough.** When the user has explicitly confirmed the current stage's completion ("确认，继续" / "需求已经确定" / "SPEC-001 没问题了"), that single confirmation authorizes the corresponding archive and the immediate handoff (including the post-archive Downstream Routing). Do not prompt a second time to "are you sure?". Do not extend the authorization to unrelated Specs or unrequested changes.
19. **Completion check before natural-language archive.** Authorization
    does not waive completion checks. The Main Agent resolves internal
    blockers at their owner, then rechecks; only a genuine product decision
    goes to the user, not routine repair or another archive confirmation.
20. **Don't claim sync that didn't happen.** If a downstream artifact (Architecture, Module Design, or another Spec) cannot be modified from this skill, return a clear result for its owner to apply. Do not claim the artifact was updated.
21. **Routing does not transfer authority.** Spec proposes Route A / B / C from evidence; Architecture owns its artifacts. Under an authorized whole-goal task, the Main Agent invokes that Skill or reads and follows it when callable tools permit. Report a genuinely unavailable capability without pretending it ran.
