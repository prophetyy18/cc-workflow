---
name: architecture
description: Design and maintain the system's Architecture Baseline — module responsibilities, dependency boundaries, public contract ownership, and cross-module system invariants. Use when the user wants to start an initial architecture from existing Specs (/architecture init), analyze how a Spec change affects the existing architecture (/architecture impact <spec-id>), revise the architecture after impact analysis is approved (/architecture revise <spec-id>), or audit the current architecture for consistency (/architecture review). Located between Spec and Module Design in the workflow. Triggered by questions like "design the architecture for these specs", "does this spec break existing contracts", "who owns capability X", or "is our module boundary still right".
allowed-tools: Read, Edit, Write, Glob, Grep, WebFetch, WebSearch, Bash(date*)
---

# Architecture Skill

Designs and maintains the **Architecture Baseline** for a system: module responsibilities, dependency boundaries, public contract ownership, and cross-module system invariants. Architecture decides *who* owns what and *what* must hold across modules. Module Design decides *how* each module implements its responsibilities.

## 1. Layer Boundaries

| Layer | Owns | Does not own |
|---|---|---|
| **Intent** | User objectives, goals, constraints, decisions | System behavior, modules, APIs |
| **Spec** | System capabilities, requirements, system invariants, acceptance conditions | Module names, API shapes, schemas |
| **Architecture** (this skill) | Module boundaries, capability ownership, public contract ownership, dependency direction, system-level correctness, cross-module invariants, Requirement → Module mapping | Specific APIs, schemas, internal algorithms, actual code |
| **Module Design** | API details, schemas, internal structure, algorithms, code | Why these capabilities exist (Intent), what they must guarantee (Spec), system responsibility allocation (Architecture) |

**Architecture is the authority for system responsibility and module boundaries. Module Design is the authority for implementation.**

## 2. Subcommand Routing

Read `$ARGUMENTS`. First token is the subcommand, the rest is the target.

| Subcommand | Target | Behavior |
|---|---|---|
| (empty) or `help` | — | Show this help |
| `init` | — | Build initial Architecture Baseline from existing Specs |
| `impact` | `<spec-id>` | Read-only analysis of how a Spec change affects current architecture |
| `revise` | `<spec-id>` | Apply authorized Architecture changes from a confirmed Impact |
| `review` | (optional scope) | Audit current architecture for consistency |

If the subcommand is unknown, do not guess. Show help and stop.

## 3. Natural-Language Operations

| User intent (paraphrased) | Action |
|---|---|
| "design the architecture for these specs", "我们还没有架构基线" | `init` |
| "does this spec break our existing contracts", "SPEC-002 改了，要改架构吗" | `impact` |
| "update the architecture", "把架构改一下" | `revise` (after an Impact result B is confirmed) |
| "is our architecture still consistent", "审一下架构" | `review` |
| "确认，继续" (after a completion proposal) | save baseline, hand off to Module Design |

**Modification is the default, not creation.** The Baseline is a single evolving document; an `init` is only the first cut. Subsequent changes go through `impact` + `revise`.

## 4. Identity & Storage

**Skill files** (this repo):

```text
.claude/skills/architecture/
├── SKILL.md
└── references/
    └── impact-analysis.md      (detailed 8-step Impact methodology, loaded on demand)
```

**Runtime project artifacts** (created in the consuming project, not in this repo):

```text
docs/architecture/
└── ARCHITECTURE.md             (the authoritative Baseline for the project)
```

Optional supporting files (created only when needed):

```text
docs/architecture/
├── ARCHITECTURE.md
├── modules/MOD-<slug>.md       (per-module responsibility + contract summary, one file per module; the filename MUST use the canonical MOD-<slug> identifier from §2 so downstream Skills can find it by ID)
└── decisions/ADR-NNN-<topic>.md (Architecture Decision Records, when material decisions need history)
```

**Canonical Module Identifier.** Every module that appears anywhere
in the Baseline — in §2 (Modules and Responsibilities), §3 (Capability
/ Requirement Ownership), §5 (Public Capabilities and Contract
Ownership), the dependency map, or any per-module summary file — must
use the same canonical identifier: `MOD-<slug>`. The `<slug>` is a
kebab-case slug (lowercase, digits, hyphens; no spaces, no leading /
trailing hyphens). Display name (e.g. "Calc Core") is a separate
field. Do not invent a parallel convention; do not reuse
`MODULE-<name>.md` (different prefix and casing).

Do not create `docs/architecture/` in this repo. It is a runtime artifact of consuming projects. The cc-workflow repo contains only the skill itself.

## 5. Subcommand: `init`

Build the initial Architecture Baseline from existing Specs.

### Step 1 — Build the System Responsibility View

Read every `SPEC.md` under `docs/specs/`. Extract:

- System Capabilities
- Requirement IDs (Functional / Non-Functional / Derived)
- System Invariants
- Acceptance Criteria
- `# Architecture Handoff` content
- Source Intent items

For each Spec, note its `status` (active vs archived). Archived Specs are confirmed baseline input. Active Specs are partial input — only use clearly-accepted sections; flag uncertain parts as "draft, may change".

If a Requirement is not clear enough to drive a responsibility decision, route back to Spec via the existing feedback mechanism. Do not invent business semantics.

### Step 2 — Derive Responsibilities from System Behavior

Analyze, do not pre-assign. For each capability, ask:

- What does it produce? Who consumes it?
- What authoritative state does it own?
- What cross-capability coordination does it need?
- Can this responsibility stand alone, or must it be co-located with another?

Identify logical responsibilities first; modules come after. Do not create one module per Spec Capability — that is mechanical, not architectural.

### Step 3 — Evaluate Module Boundaries

For each candidate grouping, weigh:

- **Cohesion** — do the co-located responsibilities change together?
- **Authority** — is there a single source of truth for the relevant state?
- **Boundary clarity** — can external consumers be told exactly what to call?
- **Maintenance cadence** — do these responsibilities evolve together?
- **Cross-module dependencies** — how many edges; can they be reduced?
- **System correctness** — does this grouping preserve end-to-end invariants?

Pick the **simplest structure that satisfies the Requirements**. Compare two candidates only when the choice is genuinely non-obvious. Do not force a multi-candidate comparison for every decision.

### Step 4 — Assign Ownership and canonical Module IDs

For each module in scope, do **both** of the following — they are not
optional, and they are what the next layer (Module Design) depends on:

1. **Assign ownership** — for each Requirement, identify the
   **Primary Owner**, the single module whose absence makes the
   Requirement unsatisfiable. Mark **Collaborating Modules** and
   **Capability Providers/Consumers** when applicable.

   Critical: a Requirement that spans multiple modules still has
   end-to-end correctness obligations. Record:
   - The Primary Owner (per module role).
   - The Integration Verifier (often Architecture or a designated
     E2E owner).

   Do not lose system-level accountability just because
   responsibility is split.

2. **Assign a canonical Module ID.** Each module gets one stable
   identifier: `MOD-<slug>`, where `<slug>` is a kebab-case slug
   (lowercase, digits, hyphens; no spaces, no leading / trailing
   hyphens; no capital letters). The slug is derived from the
   module's role or display name (e.g. "Calc Core" → `MOD-calc-core`).
   Record this ID in §2 (Modules and Responsibilities) of the
   Baseline. The same ID then appears everywhere else in the Baseline
   (Capability / Requirement map, Public Capability Owner, Dependency
   map) and any per-module summary file uses it as its filename.

   The MOD-* ID is the canonical key that Module Design and
   Implementation look up by; without it, the next layer cannot
   start. After Baseline adoption, change an ID only via an explicit
   `revise` — and propagate to downstream artifacts.

### Step 5 — Define Dependency Boundaries

For each module, document:

- Allowed public dependencies (which other modules' public capabilities it can call)
- Forbidden private dependencies (which internal details it must not touch)
- Authoritative state owners (only these modules may mutate this state)
- Required dependency direction
- Critical shared semantics (e.g., deterministic replay ordering)

The goal is to make dependencies explicit and verifiable, not to eliminate them.

### Step 6 — Define Public Capabilities and Contract Owners

For each cross-module capability, record:

- **Name** (descriptive; specific API/Schema are Module Design's job)
- **Provider Owner** (single module)
- **Known Consumers**
- **Related Requirement IDs**
- **Required Behavior** (high-level; consumer-observable)
- **Critical Timing / State Semantics** (e.g., "synchronous", "eventual", "happens-before X")
- **Required Failure Semantics** (e.g., "errors propagate", "best-effort")
- **Contract Location** (if a formal contract already exists; otherwise mark "TBD by Module Design")

Do not invent API endpoints, Schema fields, or function signatures. If a formal contract is already published somewhere, reference it. Otherwise, mark as "TBD" and the Contract Owner fills it in via Module Design.

### Step 7 — Preserve End-to-End Correctness

Verify:

- Every important Requirement has at least one Primary Owner.
- Every cross-capability System Invariant has an integration owner and a verification path.
- No two modules claim authoritative ownership of the same state.
- No Requirement is orphaned (no module responsible for satisfying it).
- System-level guarantees (e.g., "no future-data leakage in the combined historical + replay + performance path") are not silently lost in the module split.

If a check fails, revise the boundary or owner assignment and re-verify. Do not ship a Baseline with known gaps.

### Step 8 — Write the Baseline

Create `docs/architecture/ARCHITECTURE.md` in the consuming project. See §9 for the recommended content structure. Do not create this file in the cc-workflow repo.

## 6. Subcommand: `impact <spec-id>`

**Read-only analysis** of how a Spec change affects the current architecture.

Detailed 8-step methodology in [references/impact-analysis.md](references/impact-analysis.md). The summary:

1. **Establish Spec Delta** — compare the current Spec against the last adopted baseline (or, if no baseline, current architecture state).
2. **Find Affected System Capabilities** — for each change, identify which capabilities are added, removed, or materially modified.
3. **Map to Actual Modules** — for each affected capability, find the Primary Owner, Collaborators, Providers, Consumers via the Baseline.
4. **Trace Contract Consumers** — for each affected Public Capability, walk the Provider → Contract → Consumer chain and identify consumer-side impact.
5. **Classify Contract Impact** — Existing Contract Sufficient · Internal Change Only · Compatible Extension · Breaking Change · New Public Capability · Insufficient Evidence.
6. **Find Documentation Impact** — per the table in impact-analysis.md §6, only mark documents that genuinely need update. Do not auto-touch them.
7. **Evaluate Evidence** — Confirmed / Potential / Unknown, with sources.
8. **Output the Impact Plan** — a short, executable plan with: Spec changes, capability impact, affected modules, public contracts, providers, consumers, contract adjustment required, documentation updates, verification obligations, owners, unresolved unknowns.

### Impact Decision: A / B / C

The impact result is one of three decisions (separate from Spec's Route A / B / C — those are entry routing, not this result):

- **A — No Architecture Revision Required.** Existing modules, public capabilities, dependency relations, and key contract semantics already satisfy the Requirement. No Architecture change. Hand off to Module Design for the relevant module.
- **B — Architecture Revision Required.** Evidence shows module responsibility, public capability, contract ownership, dependency boundary, or cross-module invariant semantics need to change. Propose a minimal Revision. After authorization, run `/architecture revise <spec-id>`.
- **C — Insufficient Evidence.** Cannot reliably judge whether the existing architecture satisfies the Requirement. List the missing evidence. Do not interpret insufficient evidence as "must revise". Targeted investigation is required.

These are impact analysis results, not new lifecycle states.

### Output Format

```text
## Impact Analysis: SPEC-NNN

### Spec Delta
- Added Requirements: <list>
- Removed Requirements: <list>
- Materially Changed Requirements: <list>
- Changed System Invariants: <list>
- Editorial-only Changes: <list>
- Baseline comparison: <git commit / archived baseline / unable to determine>

### Affected Capabilities
- <capability>: <changed how>

### Affected Modules
- <module>: <owner / collaborator / provider / consumer>

### Affected Public Capabilities and Contracts
- <capability name> (<owner>): <Existing / Internal / Compatible Ext / Breaking / New / Insufficient>

### Documentation Impact
- <doc>: <owner> — <what needs update>

### Verification Obligations
- <capability / invariant>: <what must still be verified end-to-end>

### Unresolved Unknowns
- <unknown with what would resolve it>

### Decision: A | B | C
- Reasoning: <one paragraph>

### Recommended Next Step
- <direct Module Design / proceed to /architecture revise / gather evidence>
```

## 7. Subcommand: `revise <spec-id>`

Apply the Architecture changes authorized by a confirmed `impact` result B.

### Authorization

Run `revise` only when:

- An `impact` result B has been produced and the user has authorized the change scope, OR
- The user has explicitly asked for a specific Architecture change with sufficient detail, OR
- A Cross-layer Feedback message (per `cross-layer-coordination.md` §3)
  identifies a real Architecture-level issue (module boundary, public
  contract ownership, dependency direction, or cross-module
  invariant attribution), the highest-necessary-authority discipline
  (§4) places the fix here, and the user has authorized the change
  scope.

If the user has already confirmed the change in the natural-language
completion flow, do not prompt a second time. If the requested
change is materially larger than what was authorized, stop and
re-confirm.

Cross-layer Feedback is the route for non-Spec-change Architecture
findings (e.g., Implementation discovering that a module boundary is
wrong). Without this path, downstream Skills have no entry into
Architecture and would block on the user — which is exactly what
the user does not want to do.

### Architecture May Modify

- Module boundaries and naming
- Responsibility ownership
- Module dependency constraints
- Public capability attribution
- Contract Owner assignment
- Cross-module collaboration requirements
- Requirement / Capability → Module mapping
- Architecture decisions and Baseline records
- System Invariant responsibility attribution

### Architecture Must Delegate

- Specific API design, Schema, function signatures
- Module internal algorithms and data structures
- Consumer-side adaptation code
- Test code and implementation
- Detailed MODULE.md content (per-module internal design)

If a contract change is required, Architecture records:

- What behavior must change
- Why (link to the impact finding)
- Which consumers are affected
- Which compatibility guarantees must hold
- Who is the Contract Owner responsible for executing the change

Architecture does not write the contract itself. The Contract Owner (or Module Design) does.

### Safe Revision

A revision must:

1. Preserve confirmed system Requirements (never drop a Requirement without explicit feedback to Spec / Intent).
2. Change only the necessary scope (do not over-revise).
3. Record the source and reason of each change in `# Resume Notes` (or equivalent Baseline change log).
4. Update the actual Module Responsibility Map, Public Capability / Contract Index, and Dependency Map in the Baseline.
5. Verify dependency direction remains acyclic and consistent.
6. List downstream adaptations still required (Module Design, Contract Owner, etc.).
7. Not claim that downstream changes have been completed when they have not.

Use Git and Markdown for history. No separate version control system.

### Automatic Post-fix Verification (Trigger B)

When the current Skill has applied an authorized `revise` that meets any of the criteria below, automatically call the Independent Reviewer Subagent in `Targeted Resolution Verification` mode before declaring the issue resolved. This is the same Trigger B used by the Spec Skill — see `.claude/references/verification.md` §3 Trigger B and the shared trigger rules.

**Trigger B criteria** (apply when the revise materially changes any of):

- A module boundary, Capability / Module ownership, or dependency direction.
- A public contract's Required Behavior, Failure Semantics, or Timing / State Semantics.
- A cross-module System Invariant's responsibility attribution or verification path.
- A load-bearing architectural decision (system-level data flow, atomicity, replay ordering, etc.).

**Procedure**:

1. Confirm the change is authorized, persisted in the Baseline, and recorded in `# Resume Notes` / change log.
2. Build a Mode B delegation message: see `.claude/references/verification.md` §2 for the contract; the reviewer's reasoning frame lives in `.claude/agents/independent-reviewer.md`. `Scope` describes the specific section (e.g., "Module Responsibility Map §3 — added module X"). Include the original Impact finding's evidence and the authoritative basis for the correct outcome (the Spec Requirement / Capability being satisfied).
3. Launch the Independent Reviewer in `Targeted Resolution Verification` mode. The Reviewer re-derives the correct outcome; the Skill does not pre-bake the verdict.
4. Triage the `Targeted Verification Executed` report. If the change satisfies the upstream Spec Requirement and introduces no material new defect in scope, record `Authority Resolved` for this architecture finding. If it does not, surface the failing aspects back to the user.
5. Cycle behavior — when one round is enough, when a second round uses a stronger evidence source, and when to stop with the unresolved constraint — lives in `.claude/references/verification.md` §6. Do not restate a per-round cap here.
6. **Do not** run Targeted Verification for trivial wording, formatting, or low-risk local Baseline edits. The Trigger B criteria above are the gate.

This step is automatic within the current Skill's execution flow — it does not require the user to run `/architecture review` again. See `.claude/references/verification.md` for the shared contract and loop bounding.

## 8. Subcommand: `review`

Audit current architecture for consistency. **Default read-only; do not auto-modify.**

This subcommand is the user-explicit path to Trigger A (Independent Review) for Architecture. The same `independent-reviewer` Subagent (`.claude/agents/independent-reviewer.md`) used for Initial Review also serves the post-fix `Targeted Resolution Verification` of important `revise` changes (§7 Post-fix Verification). Architecture does not auto-modify; the user decides what to fix based on the Reviewer's report.

For the shared delegation contract, evidence standard, loop bounding, and Mode A / Mode B differences, see `.claude/references/verification.md`.

### Default scope

Check:

- **Requirement Coverage** — important Requirements without a Primary Owner.
- **Module Ownership** — duplicate authoritative state owners; capabilities with no owner.
- **Dependency Boundaries** — modules depending on other modules' private internals.
- **Contract Ownership** — every formal public contract has exactly one Owner.
- **Consumer Compatibility** — public capabilities still satisfy known consumers' actual requirements.
- **System Invariants** — every cross-module invariant has both an integration owner and an end-to-end verification path.
- **Documentation / Code Consistency** — Baseline, MODULE.md, formal contracts, and code show provable mismatches.

When math / quantitative bounds or acceptance criteria are in scope of the Baseline (rare but possible — e.g., latency budget for a public contract), the Reviewer applies the Mathematics and Acceptance Criteria verification principles from `.claude/references/verification.md` §4.2 and §4.4.

### Optional scope via natural language

- "review module X" — focus on one module's responsibilities, contracts, dependencies.
- "review the contract for capability Y" — focus on one public contract and its consumers.
- "review whether SPEC-XXX fits the architecture" — focus on one Spec's Requirements vs current ownership.

Output: a short report of findings. No automatic edits. The user decides what to fix.

Do not produce a giant full-project audit report by default. Scale the review to the actual question.

## 9. Architecture Baseline Content

When a Baseline is written (typically `docs/architecture/ARCHITECTURE.md`), the recommended structure is:

```markdown
# Architecture Baseline — <Project Name>

## 1. System Context
<high-level summary of the system, its purpose, the Intent(s) it serves>

## 2. Modules and Responsibilities

| Module ID (canonical) | Display name | One-line responsibility | Owner role | Related Requirements |
|-----------------------|--------------|-------------------------|------------|---------------------|
| MOD-<slug>            | <human name> | <one line>              | Primary Owner / Collaborator / Capability Provider / Consumer | SPEC-NNN/REQ-NNN, ... |

The first column (`Module ID`) is the canonical identifier downstream
Skills look up by. Do not leave the first column blank; do not let the
display name stand in for the ID.

## 3. Capability / Requirement Ownership
<for each System Capability: which module(s) own it, which Requirements it satisfies. Use the MOD-<slug> ID from §2, not a display name.>

## 4. Dependency Boundaries
<allowed / forbidden dependencies, authoritative state owners, required direction. Refer to modules by MOD-<slug>.>

## 5. Public Capabilities and Contract Ownership
<per public capability: capability name, Provider Owner (MOD-<slug>), Known Consumers (MOD-<slug>), related Requirements, behavior summary, contract location or "TBD">

## 6. System Invariant Responsibilities
<per cross-module invariant: what it guarantees, integration owner (MOD-<slug>), verification path>

## 7. Architecture Decisions
<material decisions with rationale and date. Optional ADR references>

## 8. Spec Baseline References
<which Spec versions this Baseline adopts. Git commits, archived Spec IDs, or "adopted from working tree on YYYY-MM-DD" if uncommitted>

## 9. Open Architecture Questions
<known unresolved questions; target resolution path>
```

This is a recommended structure, not a forced template. Omit or trim sections that don't apply. Do not pad with placeholder content.

### Minimal Traceability

Maintain the chain:

`Requirement → Capability → Responsible Module → Contract / Collaboration → Verification`

Many-to-many is allowed. The chain is the basis for impact analysis.

### Public Contract Index

Records each public capability with:

- Public Capability name
- Provider Owner
- Consumers
- Related Requirement IDs
- Authoritative contract location (path or "TBD by Module Design")

Do not invent locations for contracts that do not yet exist.

## 10. Completion and Handoff

Architecture does **not** use Intent / Spec's `active` → `archived` lifecycle. The Baseline is a single evolving document.

### Init Completion

`init` is complete when:

- Important System Capabilities have Primary Owners.
- Public Capabilities have Providers and at least one recorded Consumer (or "no known consumer yet").
- Module dependency boundaries are explicit.
- System Invariants have integration owners and verification paths.
- **Every module listed anywhere in the Baseline carries a canonical `MOD-<slug>` ID recorded in §2 (Modules and Responsibilities). The same ID appears in §3 / §4 / §5 and in any per-module summary filename.** This is the gating criterion: without it, the next layer (Module Design) cannot look up the module.
- No Blocking architecture-level Unknowns remain (Non-Blocking may be deferred to "Open Architecture Questions").

When the user confirms ("确认，继续" or equivalent), save the Baseline. Do not prompt a second time. Do not require an `archive` command.

### Impact Completion

- Result A: hand off to Module Design. No Baseline change.
- Result B: present the Revision plan. If the user confirms, run `revise` (or stay in the same turn if already authorized). Hand off to Module Design after Revision.
- Result C: explain the missing evidence. Do not pretend to have completed the impact.

### Handoff to Module Design

When an `init`, `revise`, or Impact result A / B hands off to Module Design, surface `/module-design new <module-id>` for each affected module — the module ID comes from the Baseline's Module Responsibility Map. When the Module Design Skill is invocable from the current environment, use it. When it is not invocable, report the unavailability explicitly and surface the manual command; do not pretend to invoke it. The Module Design Skill takes the Baseline + the assigned Spec Requirements and produces `DESIGN.md` plus optional machine-readable contracts; it does not modify Baseline or Spec content.

### Handoff Content (to Module Design or downstream)

Always include:

- Modules involved
- Related Requirements
- Assigned Responsibilities
- Public Capabilities (with Provider / Consumer)
- Existing Contract references (or "TBD")
- Required Contract changes (if any)
- System Invariants the modules must preserve
- Verification Obligations
- Open Design Questions

Module Design should be able to proceed without re-reading the chat history.

## 11. Feedback Routing

Architecture is not the final arbiter of every issue. Route problems to the right layer.

### Feedback to Spec (via Spec's existing feedback convention)

- Requirement missing critical behavior semantics.
- Input / output meaning unclear.
- State or timing rules undefined.
- Acceptance criteria insufficient.
- Two Requirements conflict.

### Feedback to Intent (via `/intent feedback <intent-id> <source>`)

- User goal contradiction.
- Confirmed goal needs to change.
- User constraints cannot be simultaneously satisfied.
- Technical fact invalidates the original user goal.

Do not modify the user's goal directly.

### Feedback from Module Design

Architecture must accept feedback from Module Design when:

- Responsibility attribution is wrong.
- A public Capability is missing.
- Contract Owner is unclear.
- Dependency direction conflicts.
- The current architecture cannot satisfy a Requirement.
- Cross-module Invariants cannot be preserved.

Module-internal design issues stay with the Module Owner.

### Feedback Format

Use the existing lightweight format:

- Source
- Target
- Problem
- Evidence
- Impact
- Requested Resolution

Default to the work document that contains the question (the Baseline, the Spec, the Module doc, etc.). Do not create a separate Feedback Manager.

### Cross-layer triggers

When feedback, an Impact finding, or a Spec Review finding crosses authority layers (e.g. the architecture baseline implies a Spec-level behavior gap, or a Module-level contract change requires a Spec-level invariant), load the minimum discipline from `.claude/references/cross-layer-coordination.md`. Do not load the whole file for in-Architecture work; load it only when the issue crosses authority layers.

In particular:

- Use the feedback contract in `cross-layer-coordination.md` §3.
- Apply **Minimum necessary escalation** (§4): an architecture-baseline change should not become a Spec rewrite. A contract gap should not be silently resolved as a Spec edit.
- For `impact` results that touch Spec or Intent, forward them via the feedback contract rather than embedding cross-layer judgments in the Baseline.
- Distinguish **Review Executed / Authority Resolved / Implementation Verified** per `cross-layer-coordination.md` §5. Architecture can claim only `Authority Resolved` for Baseline-level changes; it does not claim `Implementation Verified`.

## 12. Hard Rules

1. **No fabricated modules or contracts.** If evidence is missing, mark the question unresolved and say so. Do not invent modules, APIs, or contracts to make the Baseline look complete.
2. **Impact is read-only by default.** `impact` must not modify the Baseline, modules, contracts, or code. Revision is a separate, authorized step.
3. **Revision requires authorization.** Material Architecture changes need explicit user confirmation. If the user has confirmed in the natural-language flow, that single confirmation authorizes the documented scope — do not re-prompt.
4. **One Primary Owner per state.** Each authoritative state has exactly one Owner. Collaboration does not equal co-ownership.
5. **Consumers depend on contracts, not private internals.** If a module relies on another module's private behavior, that's a Baseline violation.
6. **One explicit confirmation is enough.** A natural-language "确认，继续" after a completion proposal authorizes saving the Baseline and the immediate handoff. Do not prompt a second time. Do not extend the authorization to unrelated changes.
7. **No auto-archive, no new lifecycle states.** Architecture does not use `active` / `archived` / `approved` / `released` / etc. The Baseline is a single evolving document. Init and Revision are both `Edit` operations on that document.
8. **Modify, don't recreate.** A Baseline is rewritten incrementally. `init` is only the first cut. Do not create a parallel Baseline; revise the existing one.
9. **Module Design is delegated.** Architecture does not write specific APIs, Schemas, internal algorithms, or consumer-side adaptation code. It records the requirement and the Owner.
10. **Don't claim sync that didn't happen.** If a downstream artifact (Spec, Module Design, etc.) cannot be modified from this skill, return a clear result for its owner to apply. Do not claim the artifact was updated.
11. **Insufficient evidence ≠ "must revise".** When the impact result is C, do not interpret it as architectural failure. Targeted investigation is required.
12. **System-level correctness survives decomposition.** Cross-module invariants (e.g., "no future-data leakage across historical + replay + performance") must have an integration owner and a verification path in the Baseline, not just module-local tests.
13. **Be evidence-bound.** Every important attribution (Owner, Consumer, contract gap, dependency direction) cites the Requirement, Baseline, contract, or code that supports it. "I think" is not evidence.
14. **No new Workflow machinery.** Do not add a Workflow Controller, Router Agent, or Handoff Manager. Downstream routing and handoff are short steps in the existing skills.
15. **No `docs/architecture/` in the cc-workflow repo.** That is a runtime artifact of consuming projects. This repo contains the skill, not a sample project Baseline.

## 13. References

- [references/impact-analysis.md](references/impact-analysis.md) — the full 8-step `impact` methodology, the contract classification table, and the documentation impact table. Load on demand when running `impact` or `revise`.
