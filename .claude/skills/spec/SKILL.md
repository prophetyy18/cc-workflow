---
name: spec
description: Convert clarified user Intent into complete, verifiable, traceable system requirements. Use when the user wants to define what the system must do (functional + non-functional + cross-capability correctness), create a SPEC from an Intent, review requirement coverage, or check for ambiguity and risks. Located between Intent and Architecture in the workflow. Triggered by questions like "spec out INT-001", "what does the system need to do?", "review SPEC-002", "is INT-001 covered?", or "create requirements for …".
allowed-tools: Read, Edit, Write, Glob, Grep, WebFetch, WebSearch, Bash(date*)
---

# Spec Skill

Transforms a clarified user Intent into **complete, verifiable, traceable system requirements**. Spec is the authoritative layer for "what the system must guarantee" — it does not design how. Architecture decides module ownership and contracts; Module Design decides implementation.

## 1. Layer Boundaries

| Layer | Owns | Does not own |
|---|---|---|
| **Intent** | User objectives, goals, constraints, confirmed decisions, success conditions | System behavior, modules, APIs |
| **Spec** (this skill) | System capabilities, functional & non-functional requirements, system invariants, cross-capability correctness, acceptance conditions | Module names, API shapes, schemas, algorithms, storage choices |
| **Architecture** | Module boundaries, capability ownership, public contracts, dependency direction | Specific APIs beyond the contract, internal implementation |
| **Module Design** | API details, schemas, algorithms, internal structure | Why these capabilities exist (Intent's job) |

**Spec describes what the system must guarantee. It does not decide how.**

## 2. Subcommand Routing

Read `$ARGUMENTS`. First token is the subcommand, the rest is the target.

| Subcommand | Target | Behavior |
|---|---|---|
| (empty) or `help` | — | Show this help |
| `<intent-id>` (bare) | intent id | Primary entry: read intent, run risk review, propose Spec scope, ask user to confirm before creating |
| `new` | `<intent-id> [scope]` | Create a new Spec for an intent (optionally scoped) |
| `list` | — | List all Specs grouped by status |
| `show` | `<spec-id>` | Print the full `SPEC.md` |
| `resume` | `<spec-id>` | Continue work on an existing Spec |
| `review` | `<spec-id>` | Run risk / completeness / traceability / conflict check |
| `coverage` | `<intent-id>` | Analyze how well an Intent's goals are covered by existing Specs |
| `archive` | `<spec-id>` | Finalize Spec (after user confirmation) |
| `reopen` | `<spec-id>` | Re-open an archived Spec (warns about downstream impact) |

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
| "archive SPEC-001", "we're done with this" | `archive` (after confirmation) |
| "确认，继续" / "SPEC-001 没问题了" (after a recent completion proposal) | `archive` + Downstream Routing — do not prompt a second time |
| "I need to change SPEC-001 but it's archived" | `reopen` (after confirmation) |

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
6. Present a brief proposal: "I propose to create SPEC-NNN for capability X, with sub-Specs for Y and Z. Existing SPEC-XXX already covers W."
7. **Wait for user confirmation**, then proceed to `new` or `resume`.

Do not silently create a Spec. The user must confirm scope before any SPEC.md is written.

## 6. Subcommand: `new <intent-id> [scope]`

Create a new Spec.

1. Re-run the risk review. If Blocking Unknowns exist, surface them — do not silently fill in assumptions.
2. Read the source intent again. Identify the scope: which capabilities this Spec will cover.
3. If `[scope]` is given, narrow to that. If not, infer the smallest useful scope and present it for confirmation.
4. **Check existing Specs**:
   - Does an existing Spec already cover part of this scope? If yes, surface — modify existing first, don't duplicate.
   - If split is appropriate, propose a primary Spec and optionally cross-Spec invariants.
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

Example for an "Uniswap v4 LP backtest platform" intent:

```text
- Historical chain data acquisition + availability
- Historical pool & LP state reconstruction
- Strategy decision + position operation replay
- Fee / inventory / NAV / risk evaluation
- Strategy comparison + interactive research
```

This map is **not** a fixed template. Derive from the actual intent. Don't pad with speculative capabilities. Don't list technical implementation details (e.g., "PostgreSQL schema" — that's Architecture).

The map can live in the Spec's `# Scope and Sources` or `# System Capabilities` section. No separate capability graph database.

## 8. Spec Decomposition

One Spec per independent, verifiable system behavior or behavior group. Not per module, per code directory, per intent, or per API.

Split when:

- Behavior boundary is clear and self-contained.
- Each side can have its own acceptance criteria.
- Different change/maintenance cadence.
- Splitting makes the system easier to understand and verify.
- Splitting does NOT lose system-level invariants.

Do not split just because:

- The capability touches two modules.
- There are two technical options.
- There are two sets of APIs.
- The requirement doc is long.
- It needs many tests.

Heavily-coupled capabilities belong in the same Spec. Cross-Spec invariants must be explicitly captured in both Specs and a shared invariant section.

**One Intent → many Specs. Many Intents → one Spec.** This is normal. The `source_intents` field lists all that apply.

## 9. Subcommand: `list`

1. `Glob docs/specs/SPEC-*/SPEC.md`.
2. Read frontmatter of each.
3. Print a compact table. `active` first, then `archived`. Columns: `id`, `title`, `status`, `source_intents` (count), `updated`.

## 10. Subcommand: `show <spec-id>`

Print the full `SPEC.md`. No editing. If ID is ambiguous, list candidates.

## 11. Subcommand: `resume <spec-id>`

1. Load `SPEC.md`.
2. Read `# Resume Notes` to see where the last session left off.
3. Read `# Decisions` first. Do not re-ask answered questions.
4. Continue clarification or research from the open frontier.
5. Update `# Resume Notes` at the end.

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

<cross-capability / cross-Spec correctness constraints that must always hold. Examples: "no future-data leakage", "unified NAV calculation", "deterministic replay".>

# Acceptance and Verification

<how to verify each Requirement / invariant. Three levels when useful:
- **Capability Verification** — does this Spec meet its own Requirements?
- **Contract Verification** — do other Specs / modules honor their inter-Spec contracts?
- **System Verification** — do the combined capabilities still meet the original user goal?>

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

## 14. Subcommand: `review <spec-id>`

Run a structured review of a Spec. The default execution delegates to the read-only `independent-reviewer` subagent (defined in `.claude/agents/independent-reviewer.md`) in a fresh context, so the review does not inherit the author's reasoning. This Skill owns the **independent triage**, the user-decision loop, and the resolution path; the Reviewer owns the evidence-based findings.

**Trigger policy.** Delegate to the Independent Reviewer when:

- The user runs `/spec review <spec-id>` explicitly, OR
- A Spec is about to be archived and the Spec touches money / assets / security / core data correctness / public contracts.

For trivial wording edits and pure typo fixes, the current Skill may perform a fast Self-check without delegating. Default to delegation; do not skip it just because the Spec looks small.

### 14.1 Delegation procedure

1. **Confirm the target.** Resolve `<spec-id>` (must exist; load `docs/specs/<spec-id>/SPEC.md`).
2. **Locate authoritative sources.** Read `source_intents` from the target's frontmatter; load each source Intent's `INTENT.md`. Read any Specs cited as related in `# Scope and Sources`. Note their `status`.
3. **Load the Review Criteria.** Read [references/review.md](references/review.md#2-spec-review-spec-review-spec-id) so the Reviewer knows the criteria, and so this Skill can interpret findings.
4. **Build a neutral delegation message.** See the template in [references/review.md §2.1](references/review.md#21-delegation-message-template). The message must contain: Review Type, Target, Authoritative Sources, Review Criteria, Scope, Method, Output, Permissions. **Do not** include author conclusions such as "this Spec looks correct" or pre-baked judgments about facts.
5. **Launch the Independent Reviewer.** Use the Agent tool with `subagent_type: "independent-reviewer"` and the neutral delegation message as the prompt. This starts a **non-fork subagent** with read-only access (no Edit / Write / Bash) and no persistent memory. Verify the call succeeded.
6. **Receive the report.** The Reviewer returns a structured Markdown report (see `.claude/agents/independent-reviewer.md` §3).
7. **Independent Triage.** This Skill does **not** rubber-stamp the Reviewer's recommendations. For each finding, run the Triage procedure in [references/review.md §2.7](references/review.md#27-triage-procedure). For cross-layer issues, load the cross-layer rules from `.claude/references/cross-layer-coordination.md`.
8. **Resolution paths.** Each triaged finding produces a resolution path owned by the **highest necessary** authority whose content must change. Most findings will be triaged to: Accept (modify Spec wording), Reject (with evidence), Request evidence, Redirect (to Spec / Architecture / Module / Implementation / Verification / User), or already covered by an existing downstream guarantee. **Do not** route every finding to Spec.
9. **Closure language discipline.** Record only `Review Executed` after this Skill finishes. Do not record `Authority Resolved` until the actual authoritative content has been changed (or formally rejected). Do not record `Implementation Verified` — that belongs to Verification. See [references/review.md §2.7.4](references/review.md#274-closure-language-discipline).
10. **No auto-edit.** This Skill does not auto-modify any authoritative file. All material edits wait for user authorization.

### 14.2 If the Independent Reviewer cannot be spawned

- If the Agent tool returns an error or no fresh-context subagent is available, **report that Independent Review was not executed** and offer:
  1. A Self-check using this Skill's own review criteria (clearly labeled "Self-check, not Independent Review"), OR
  2. A manual review based on [references/review.md](references/review.md#2-spec-review-spec-review-spec-id).
- Do **not** present a Self-check as an Independent Review.

### 14.3 Reviewer reasoning frame

The Reviewer uses a **Derive → Locate** reasoning frame: derive what the authoritative sources require (Necessary Conditions, Design Choices, Unverified Assumptions), then locate where the target Spec misses, weakens, or contradicts a Necessary Condition. See [references/review.md §2.2](references/review.md#22-the-phases-the-reviewer-executes) and `.claude/agents/independent-reviewer.md` §3–§4. This Skill adds the independent triage in [references/review.md §2.7](references/review.md#27-triage-procedure) (Resolve + Validate).

### 14.4 Output: a structured findings report

No automatic edits; the user decides what to change. The report format and severity rules live in `.claude/agents/independent-reviewer.md` §3.

### 14.5 Reviewer boundary

The Reviewer does not modify any authoritative content (`INTENT.md` / `SPEC.md` / `ARCHITECTURE.md` / `MODULE.md` / contracts / code), does not approve or archive the Spec, and does not trigger the next phase. See `.claude/agents/independent-reviewer.md` §0 (IS NOT) for the full boundary. Findings that point at another layer come back to this Skill, which routes them via `# Unknowns and Upstream Feedback` and the existing cross-layer feedback contract.

## 15. Subcommand: `coverage <intent-id>`

Check how well an Intent's important content is covered by existing Specs.

1. Load `INTENT.md`. Extract: goals (from `# Clarified Intent`), hard constraints (from `# Constraints and Success Criteria`), confirmed decisions (from `# Decisions`).
2. For each, search Specs that cite this intent. Read the relevant Requirements.
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
3. **Confirmation rule.** When called as a slash command, confirm with the user explicitly. When called via the natural-language completion flow (the user just said "确认，继续" / "SPEC-001 没问题了" / "需求已经确定" in response to a recent completion proposal), reuse that confirmation — do not prompt a second time. If the response is ambiguous, ask for clarification rather than assume.
4. **Completion check before archive.** For the natural-language flow, verify: saved, no Blocking Unknown, important Requirements have sources and acceptance, traceability valid, no major upstream conflict. If a Blocking issue exists, surface it and stop — do not silently archive. Non-Blocking issues are recorded in `# Unknowns and Upstream Feedback` and do not block.
5. Spec can be archived when its Requirements are sufficiently defined for downstream. Architecture / Module Design can proceed in parallel or later.
6. On confirmation: set `status: archived`, update `updated`. Append a note to `# Resume Notes`.
7. **Downstream Routing (post-archive).** After successful archive, run the routing check (§19) and surface the recommendation to the user. The routing is informational — the user decides whether to follow.

## 17. Subcommand: `reopen <spec-id>`

1. Confirm with the user. Warn that any downstream Architecture / Module Design / Implementation may have been written against the archived version.
2. Set `status: active`, update `updated`.
3. Append a note to `# Resume Notes` explaining why it was reopened.

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

After successful archive, the Spec skill performs a **lightweight downstream routing check**. The check is informational — the user decides whether to follow the recommendation. Spec only proposes the route; it does not make Architecture decisions.

### 19.1 Routing inputs

Routing makes two **independent** checks before deciding.

**Skill Availability** — Whether the Architecture Skill is invocable from the current Claude Code environment. Skills may come from project-level `.claude/skills/`, user-level skills, or other supported sources. **A Skill file existing on disk is not the same as the Skill being invocable in this run.** A separate Skill directory by itself does not imply any project Baseline.

**Baseline Availability** — Whether the current business project has an authoritative Architecture Baseline. The Baseline is a *project* artifact, distinct from any Skill.

Canonical search order for the current project's Baseline:

1. `docs/architecture/ARCHITECTURE.md` (preferred convention).
2. A project-explicit authoritative path the project has adopted (for example, a top-level `ARCHITECTURE.md`). Use it only when the project has clearly chosen that path.
3. Any formal successor the project explicitly names.

An empty directory, a missing file, or a near-empty stub is **Baseline absent**. The following are **not** valid Baseline evidence, regardless of filename or directory name:

- `.claude/skills/architecture/SKILL.md` and its references (this is the Skill's own documentation).
- The Architecture Skill install directory and any file inside it.
- Generic framework documentation, third-party templates, or unrelated sample projects.
- Documents not authored as the project's authoritative Baseline.

Other routing inputs (always project-scoped):

- The archived `SPEC.md`, especially `# Architecture Handoff` and `# Requirements`.
- Module / contract documentation that legitimately follows from the project's Baseline (not Skill files).
- Cross-references to other Specs that share capabilities.

### 19.2 Three routes

**Route A — Architecture Init**

Apply when:

- No trustworthy Architecture Baseline exists for the current business project (Baseline Availability = absent).

This is the **only** trigger for Route A. Any "new capability without a module Owner" or "applicability of an existing Baseline unclear" is **not** a Route A trigger — see Route B.

Important clarifications — none of these alone establish a Baseline:

- The Architecture Skill is installed or invocable from this environment.
- `.claude/skills/architecture/SKILL.md` exists on disk.
- An architecture-shaped directory exists but is empty.
- A file with a similar filename exists in an unrelated location.

Skill Availability is **independent** of this route: a Baseline can be absent whether or not the Skill is invocable.

Recommendation: surface `/architecture init` as the next step.

- If the Architecture Skill is invocable from the current environment, use it.
- If the Architecture Skill is not invocable from the current environment, report the unavailability explicitly and surface the manual command. Preserve the Handoff — do not claim the invocation succeeded.

**Route B — Architecture Impact**

Apply when **any** of:

- A trustworthy Baseline exists, but a new system capability has no clear module Owner. **(Baseline present + new capability lacks Owner → Route B, not Route A. Reinitialization is not justified by a coverage gap alone.)**
- An existing public contract may be insufficient for a new Requirement.
- The Spec may change module ownership, dependency direction, or authoritative state attribution.
- The Spec may change public contract semantics.
- Cross-module system invariants may be affected.
- There is not enough evidence to conclude the existing architecture absorbs the change.
- The Baseline's applicability to the current Spec is uncertain and needs targeted verification.

When a Baseline exists but is partial or applicability is uncertain, evaluate the gap before recommending reinitialization. Targeted Impact (or even Module Design) is usually cheaper than `init`. Only Architecture itself decides whether a Revision is actually needed (its impact result A / B / C).

**Insufficient evidence means we need to check, not that revision is required.**

Recommendation: surface `/architecture impact SPEC-NNN` as the next step.

- If the Architecture Skill is invocable from the current environment, use it.
- If the Architecture Skill is not invocable, report the unavailability explicitly and surface the manual command.

**Route C — Direct Module Design**

Apply when **all** of:

- A trustworthy Architecture Baseline exists for the current project.
- The capabilities needed have clear responsibility Owners.
- Required public contracts exist and are sufficient.
- The Spec does not change module boundaries, contract ownership, or key cross-module semantics.
- The remaining work is module-internal design or implementation.

**Route C requires real evidence** — a trustworthy Baseline that names the affected Owners and shows the contracts hold. Do not conclude Route C from filename similarity, directory presence, or Skill availability.

When the routing evidence itself is incomplete (Baseline exists but Owner / contract status unclear), do not guess Route C. Surface `Insufficient evidence` and propose `/architecture impact SPEC-NNN` or targeted verification.

Recommendation: proceed directly to Module Design for the relevant module. No new Architecture work required. Skill invocability is not required to recommend Route C — it changes only who performs the Module Design, not the routing verdict.

### 19.3 Routing evidence

The routing conclusion must cite the minimum evidence:

- The relevant Spec Requirements.
- Required system capabilities.
- Existing architecture evidence (or its explicit absence).
- Whether a module owner already exists.
- Whether a public contract gap is detected.
- The recommended next step and its reasoning.

If architecture documents are missing, do **not** invent module or contract claims to make the routing look cleaner.

### 19.4 Scope

Spec only proposes the route. It must NOT directly modify:

- Module responsibility.
- Public contracts.
- Architecture baseline.
- Module Design.

If a downstream Architecture or Module Design step concludes the existing baseline is wrong, that conclusion comes from those layers, not from Spec.

### 19.5 No extra router skill

Downstream Routing is a small step in Spec's existing Hand-off, not a separate Workflow Controller, Router Agent, or Handoff Manager.

### 19.6 Skill availability is not fixed

Do not encode a hardcoded implementation status for the Architecture Skill into this SKILL.md. Skill Availability is a runtime property, judged per invocation, and can change between runs and environments.

Each invocation must independently judge:

- Whether the Architecture Skill is invocable from the **current** Claude Code environment.
- Whether the current business project has a trustworthy Architecture Baseline.

The two checks are independent. The combined cases resolve as:

| Skill Available | Baseline | Routing |
|---|---|---|
| Yes | Absent | Route A (Init); the Skill's invocability does not imply a Baseline exists. |
| Yes | Sufficient | Route C possible; Skill may be invoked for confirmatory Impact if desired. |
| Yes | Present, new capability lacks Owner | Route B (special case; do not invoke Init just because of a coverage gap). |
| Yes | Present but applicability uncertain | Route B (Impact) or targeted verification. |
| Yes | Only Skill files exist | Route A — Skill documentation is not a Baseline. |
| Yes | Only an empty architecture directory exists | Route A — empty directory is Baseline absent. |
| No  | Absent | Route A is required in principle, but the Skill is not invocable from this environment; report unavailability and surface the manual command. |
| No  | Sufficient | Route C is still the right routing conclusion. Skill invocability changes only who performs Module Design, not the routing verdict. |

Rules:

- Judge Skill Availability from the **current** environment, not from a memorized development phase.
- Do not write any historical development state (e.g. "skill not yet implemented") into the routing rules.
- When the Skill is unavailable, report it explicitly. Do not claim the call succeeded.
- Baseline existence is a separate question from Skill installation.

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

If the spec skill is not invokable from this environment, record the feedback in `# Unknowns and Upstream Feedback` and surface the manual command for the user. Do not print a command and claim it was executed.

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
10. **No auto-archive, no auto-reopen, no auto-modify.** Material changes to authoritative content always require user authorization.
11. **Archive independent of downstream.** Spec can be archived before Architecture / Module Design is done.
12. **Material archived change → reopen.** Material changes to archived Specs follow the reopen flow.
13. **Lightweight by default.** Don't add approval workflows, multi-stage states, or extra lifecycle beyond `active` / `archived`.
14. **Do not invent Architecture.** If no architecture exists, leave module ownership open. Do not fabricate module names.
15. **When in doubt, classify as Architecture question.** Don't try to settle module / contract questions from Spec.
16. **Classify load-bearing facts.** For every load-bearing factual claim that supports a Requirement, classify as Verified / Supported / Unverified. Do not silently rely on unverified claims — record them in `# Unknowns and Upstream Feedback` with the required evidence and acceptance obligation, or block the Requirement until resolved. See [references/fact-verification.md](references/fact-verification.md).
17. **Documentation ≠ empirical evidence.** Runtime availability, data completeness, performance, and reconstruction accuracy cannot be closed as Verified from documentation alone. They require observation or measurement, or an explicit acceptance obligation on a downstream stage.
18. **One explicit confirmation is enough.** When the user has explicitly confirmed the current stage's completion ("确认，继续" / "需求已经确定" / "SPEC-001 没问题了"), that single confirmation authorizes the corresponding archive and the immediate handoff (including the post-archive Downstream Routing). Do not prompt a second time to "are you sure?". Do not extend the authorization to unrelated Specs or unrequested changes.
19. **Completion check before natural-language archive.** A natural-language completion confirmation is not a license to skip the completion check. The check (saved, no Blocking Unknown, important Requirements sourced, traceability valid, no major upstream conflict) still runs. Blocking issues stop the archive; the user must resolve them before re-confirming.
20. **Don't claim sync that didn't happen.** If a downstream artifact (Architecture, Module Design, or another Spec) cannot be modified from this skill, return a clear result for its owner to apply. Do not claim the artifact was updated.
21. **Routing is a recommendation, not a decision.** Spec proposes Route A / B / C based on available evidence. It does not modify architecture, modules, or contracts. If the Architecture Skill is not invocable from the current environment, surface the manual command — do not pretend to invoke it.
