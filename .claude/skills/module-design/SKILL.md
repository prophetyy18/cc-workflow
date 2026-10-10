---
name: module-design
description: Design a single module's public contract and internal design from an authoritative Architecture Baseline and the Spec Requirements the module owns. Reuses Cross-layer Coordination for upstream errors and the Independent Reviewer for verification. Delivers a DESIGN.md (and optional machine-readable contracts) that Implementation can execute against. Use when the user wants to start a new module design from Architecture (`/module-design new MOD-foo`), resume a paused design, focus only on the public contract, request a full review, or hand off to Implementation. Triggered by phrases like "design MOD-foo", "把 foo 模块设计一下", "看下 foo 的契约", "foo 可以交给实现了".
allowed-tools: Read, Edit, Write, Glob, Grep, WebFetch, WebSearch, Bash(date*)
---

# Module Design Skill

Produces a single module's authoritative `DESIGN.md` from an authoritative
Architecture Baseline and the Spec Requirements the module owns. The
Skill defines the module's actual public contract (input/output
semantics, state, lifecycle, timing, error semantics, consumer use
conditions), then chooses its internal design (algorithms, data
structures, libraries, test approach), and prepares Implementation
Handoff. Architecture decides *which module owns which capability*;
this Skill decides *what the capability actually does* and *how the
module does it internally*.

## 1. Layer Boundaries

| Layer | Owns | Does not own |
|---|---|---|
| **Intent** | User goals, constraints, confirmed decisions | System behavior, modules, contracts |
| **Spec** | System capabilities, Requirements, invariants, acceptance | Module names, capability naming, API shapes, schemas, algorithms |
| **Architecture** | Module boundaries, capability ownership, **public capability naming and unique Provider assignment**, dependency direction, cross-module invariants | Actual API, schema, function signatures, internal algorithms, internal data structures |
| **Module Design** (this Skill) | **Public contract content** for capabilities this module provides; **internal design** (algorithms, data structures, library choices, test approach) for this module; **DESIGN.md**; optional machine-readable contracts | Module-boundary changes; contract ownership changes; actual code; Spec or Architecture content |
| **Implementation** | Actual code, tests, runtime evidence | Public contract content; module-boundary changes |

**Module Design is the authority for the public contract content of
modules it designs. Architecture is the authority for which module
owns which contract. Implementation works against DESIGN.md.**

## 2. Subcommand Routing

Read `$ARGUMENTS`. First token is the subcommand, the rest is the target.

| Subcommand | Target | Behavior |
|---|---|---|
| (empty) or `help` | — | Show this help |
| `new` | `<module-id>` | Start a new design for an existing module declared in the Baseline |
| `resume` | `<module-id>` | Continue work on an existing design |
| `contract` | `<module-id>` | Focus on the public contract only (Provider contract draft) |
| `review` | `<module-id>` | Run full Independent Review (Trigger A) on the current design |
| `status` | `<module-id>` | Print current state — open fronts, blockers, handoff readiness |
| `handoff` | `<module-id>` | Finalize and prepare Implementation Handoff |

If the subcommand is unknown, do not guess. Show help and stop.

## 3. Natural-Language Operations

| User intent (paraphrased) | Action |
|---|---|
| "design MOD-foo", "把 foo 模块设计一下", "做一下 foo 的设计" | `new` (if Baseline declares foo); `resume` (if DESIGN.md exists) |
| "继续上次 foo 的设计" | `resume` |
| "看下 foo 现在的进度", "foo 状态" | `status` |
| "先只写 foo 的公共契约" | `contract` |
| "审一下 foo 的设计", "review MOD-foo" | `review` |
| "foo 可以交给实现了", "hand off foo" | `handoff` (after completion check + Trigger B verification if material) |
| "确认，继续" / "设计没问题" (after a recent completion proposal) | Persist current state and advance one step — do not prompt a second time |

**Modification is the default, not creation.** A module's
`DESIGN.md` is modified, not duplicated.

## 4. Identity & Storage

**Stable module ID**: `MOD-<name>` (kebab-case slug after `MOD-`).
The Architecture Baseline's Module Responsibility Map is the source of
truth for the ID. Module Design does **not** rename modules — that is
an Architecture change.

**Storage layout** (one directory per module):

```text
docs/modules/
└── MOD-<name>/
    ├── DESIGN.md             (required; authoritative single design file)
    └── contracts/            (optional, only when machine-readable contracts exist)
        └── <capability>.yaml (or .json / .proto; one file per capability max)
```

`DESIGN.md` is the authoritative single source of design content for a
module. Optional machine-readable files under `contracts/` exist only
when a Consumers / Implementations workflow benefits (typed API
generation, schema diffing, etc.). Do not duplicate the same content in
both DESIGN.md and contracts/.

If the consuming project already defines its own module layout
(monorepo with `packages/<name>/`, language-specific `src/<name>/`,
etc.), follow that project convention. State the chosen path in `# Resume
Notes` so a later resume can locate the files. Do not invent a parallel
layout just because this Skill prefers `docs/modules/`.

Do not create `docs/modules/` in this repo — that is a runtime
artifact of consuming projects.

## 5. Subcommand: `new <module-id>`

### Entry check — confirm before stopping

Before declaring the target "doesn't exist", normalize the user's
identifier and surface actual evidence:

1. Normalize `<module-id>`: trim whitespace, case-fold, strip an
   optional `MOD-` prefix. Try `MOD-<slug>` first, then `<slug>`
   alone, then case-folded variants. A user who said "foo" or
   "Foo" or "mod-foo" is asking for the same module as `MOD-foo`.
2. Look up the candidate in the Baseline's Module Responsibility
   Map (and, when present, in
   `docs/architecture/modules/MOD-<name>.md`).
3. Resolve ambiguities (more than one match) by listing the
   candidates and asking the user — do not silently pick one.
4. If still no match: present the Baseline's known module list as
   evidence and ask the user to confirm or correct. Do not invent
   a module. Do not stop with "module not found" alone — that
   leaves the user without a path forward.

If the Baseline is absent (Route A state per `spec/SKILL.md` §19),
surface the missing Baseline as the primary blocker. Independently
report Architecture Skill invocability:

- If the Architecture Skill is invocable from the current
  environment, the Main Agent should `/architecture init` itself —
  do not push the user to type the command. Once a Baseline exists,
  return to this `new`.
- If the Architecture Skill is not invocable, report the
  unavailability explicitly and surface the manual command. Do not
  pretend to invoke it.

If a single existing entry match is found, proceed. The legacy
"the module must appear in the Baseline" check still applies — if
the user has explicitly asked for an ad-hoc module not yet in the
Baseline, require explicit confirmation of the ID and minimal
boundary context, record that decision in `# Resume Notes`, and
note that the Baseline should be amended (a separate `architecture`
concern).

### Step 1 — Load upstream basis

### Step 1 — Load upstream basis

Read in order:

1. The Architecture Baseline — Module Responsibility Map, Public
   Capability / Contract Index entry for this module, Dependency Map,
   System Invariants the module participates in.
2. The Source Spec(s) — Requirements the Baseline assigns to this
   module (Primary Owner + Collaborators); the Spec's System Invariants
   and Acceptance.
3. Any module summary file (`docs/architecture/modules/MOD-<name>.md`)
   that pre-exists from Architecture.
4. Known Consumers' actual use — search the consumer-side code for
   references to this capability; treat absence as `Unknown`, not as
   "no constraint".

If the Baseline is silent on the Public Capability / Contract Index
entry, the requirements chain, or the integration owner — surface
Missing Information; do not invent ownership. Route to Architecture
via the Cross-layer Coordination feedback contract
(`cross-layer-coordination.md` §3).

### Step 2 — Public Contract First

For every Public Capability this module is the unique Provider of,
write the contract fields. Cover only what real Consumers + the Spec
actually need; do not pad. Field categories:

- **Input semantics, types, units** — what is accepted; what edge
  inputs are valid; how unit / locale handling is documented.
- **Output semantics, types, units** — what is produced; what
  consumers can rely on.
- **State changes** — which authoritative state the call mutates;
  who else may observe the change.
- **Timing / ordering** — sync or async; happens-before relationships;
  monotonic-time assumptions.
- **Failure semantics** — which failures propagate (with what types);
  which are absorbed internally; retry / idempotency posture.
- **Correctness constraints** — atomicity, idempotency, no-future-data,
  deterministic-replay, etc. — only when the Baseline or Spec
  requires them.
- **Consumer preconditions** — what a Consumer must ensure before
  calling (e.g., "must have called `init()` first", "must hold
  lease FOO").

For each field, cross-check against:

- The Spec Requirement assigned to this module.
- The Baseline's Public Capability / Contract Index entry.
- Known Consumers' actual use (search the consumer code or contract
  reference where one exists).

When multiple Capabilities are tightly coupled (same Provider, shared
state, shared timing rules), use a single contract file rather than
splitting by Capability unless audiences are genuinely disjoint.

### Step 3 — Internal Design

Public contract content settled first. Then choose internal design
freely:

- Internal components and their responsibilities.
- Data structures and algorithms.
- Library and tool choices (with verification per `CLAUDE.md` Search
  Rules for any load-bearing premise).
- Caching, exception, and resource-management strategy.
- Verification approach (which test layers; E2E / integration /
  property; tooling).

**Do not promote routine internal choices to Architecture or User
decisions.** Do, however:

- Cite a verified primary source for any load-bearing technical
  premise (library behavior, protocol semantics, state-machine edge).
- Re-derive upstream constraints (Spec Requirement + Baseline
  ownership) before locking the design in.
- Reuse existing project conventions where they exist; do not invent a
  parallel convention just because this Skill is running.

### Step 4 — Verification Strategy

`DESIGN.md` must include a verification method that can actually catch
wrong implementations:

- An observable check that distinguishes correct from wrong.
- The expected outcome derived from the Spec Requirement (not from the
  implementation).
- Boundary and failure-mode coverage.
- Independence from the implementation's own bookkeeping (i.e., the
  test should not call into the same helper that produces the
  behavior under test).

A passing test on its own is not a verification method. This is the
Acceptance Criteria verification principle from
`.claude/references/verification.md` §4.4.

### Step 5 — Persist DESIGN.md

Create `docs/modules/MOD-<name>/DESIGN.md` using the template in §10.
Persist after every meaningful change. If machine-readable contracts
exist, write them under `docs/modules/MOD-<name>/contracts/`.

### Step 6 — Targeted Verification (Trigger A)

If the design satisfies any Trigger A criterion in
`.claude/references/verification.md` §3 (e.g., the module owns a
Requirement load-bearing on money / assets / security / data
correctness / public contract), run Independent Review (Mode A)
before announcing the module design is ready.

For less critical modules, this Skill's own Self-check is sufficient.
Do not run a full Review for every trivial module design. The
Reviewer reuse is the same as in `spec/SKILL.md` §14 and
`architecture/SKILL.md` §8 — load
`.claude/references/verification.md` for the delegation contract.

## 6. Subcommand: `resume <module-id>`

1. Load `DESIGN.md` and any `contracts/*` files. Read `# Resume Notes`
   first. Do not re-derive settled decisions.
2. Continue from the open frontier (Step 2 → 6 above as needed).
3. After any material change that meets Trigger B criteria
   (`.claude/references/verification.md` §3), run Targeted Resolution
   Verification (Mode B) before resuming normal flow.
4. Update `# Resume Notes` at the end with the new resume position.

## 7. Subcommand: `contract <module-id>`

Focus only on Step 2 (Public Contract). Useful when the user wants the
contract drafted before internal design is locked. Same authority and
review rules as `new`'s Step 2.

## 8. Subcommand: `review <module-id>`

Run full Independent Review (Mode A) on the current `DESIGN.md`. The
default behavior is to delegate to the `independent-reviewer` Subagent
with a neutral delegation message. Use the delegation contract in
`.claude/references/verification.md` §2 and the delegation template
pattern in `.claude/skills/spec/references/review.md` §2.1 (substitute
`Review Type: Module Design`).

Apply the Reviewer's verification principles
(`.claude/references/verification.md` §4) — particularly:

- §4.5 (Architecture and Contracts) — public contract semantics
  against Spec and Baseline.
- §4.4 (Acceptance Criteria) — can the verification method catch a
  wrong implementation?
- §4.2 (Mathematics) — for any quantitative bound the module
  promises.
- §4.6 (Implementation readiness) — is the DESIGN.md enough for an
  Implementation Agent to proceed without re-reading this Skill's
  chat history?

If the review surfaces upstream errors (Baseline wrong, Spec
Requirement wrong), route them via Cross-layer Coordination, **not**
by silently rewriting this module's `DESIGN.md` to absorb them.

## 9. Subcommand: `status <module-id>`

Print the current state of `DESIGN.md`:

- What's settled (public contract content, internal decisions).
- What's open (which Step / which fields).
- What's blocked (with Cross-layer feedback references).
- Handoff readiness (per §12 completion criteria).

No edits.

## 10. Subcommand: `handoff <module-id>`

1. Load the design.
2. Run the Completion Check (§12).
3. Run Targeted Resolution Verification (Mode B) per
   `.claude/references/verification.md` if any material change since
   the last successful review.
4. On success, finalize `# Resume Notes` with the handoff state and
   prepare Implementation Handoff (§11) content.
5. Architecture / Implementation Handoff is a contract, not a chat
   transcript. Provide the module-file paths Implementation must
   read; do not require chat history.

## 11. DESIGN.md Template

```markdown
---
module: MOD-<name>
status: draft | final
source_spec:
  - SPEC-NNN
source_architecture:
  - ARCHITECTURE.md §X
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# Module Goal and Upstream Basis

<one paragraph: what this module owns per the Baseline; which Spec
Requirements it satisfies; which Public Capability it provides and
which it consumes. Reference the relevant REQ-IDs and Baseline
sections.>

# Provided Public Contracts

<per provided capability. Reference contracts/<capability>.yaml
when one exists. Only document the fields that real Consumers and the
Spec actually need.>

# Consumed Public Contracts

<per consumed capability: Provider module, capability name, contract
location or pointer.>

# Internal Design and Key Decisions

<one paragraph per material decision. Each material decision cites
its source (verified external fact, Baseline section, Spec REQ-ID)
when load-bearing. Routine internal choices (file naming, helper
extraction) do not need a paragraph.>

# Correctness Guarantees and Verification

<for each assigned Spec Requirement: observable check, expected
result derived from the Requirement (not from the implementation),
boundary and failure-mode coverage. State when the verification
method is independent from the implementation's own bookkeeping.>

# Blocking Unknowns and Implementation Handoff

- **Unknown**: <what is unknown>
  **Why it matters**: <downstream impact>
  **How to resolve**: <specific action>
- Implementation Handoff: <what Implementation must build; which
  test layers; what evidence Implementation must produce; what files
  / modules / tests to add; which Spec REQ-IDs the implementation
  must satisfy.>

# Resume Notes

<short status: last action, what's next, key open questions.>
```

Adjust to actual complexity. Empty sections are fine. Do not pad with
filler to make the file look complete.

## 12. Cross-layer Triggers

When this Skill finds a problem upstream (Baseline wrong, Spec
Requirement wrong, consumer-side use of a contract violates upstream
constraint), apply the existing Cross-layer Coordination. Do **not**
duplicate the discipline here. Load
`.claude/references/cross-layer-coordination.md` only when an issue
crosses an authority boundary.

The flow this Skill follows:

```
Discover → Establish Evidence → Locate Authority → Minimal Correction
        → Impact Propagation → Targeted Verify → Resume
```

### Discover

The blocker surfaces during Step 2–6. State the symptom and the
authority level the symptom points to. Do not normalize the symptom
into a local Spec edit.

### Establish Evidence

Cite the Spec / Baseline / external source that proves the upstream
authority is wrong. Show, do not assert.

### Locate Authority

Identify the smallest authority whose content must change. Most cases
route via the existing `feedback` mechanism
(`/intent feedback`, `/spec` modify-and-resume, or `/architecture
revise`); for cross-layer gaps, follow
`cross-layer-coordination.md` §2 (Identify → Escalate → Resolve →
Propagate) and §4 (Minimum necessary escalation).

### Minimal Correction

Edit only the necessary content at the located authority. Do not
batch unrelated changes. Do not silently rewrite an archived Spec or
an adopted Architecture Baseline — go through the existing reopen /
revise mechanisms with user authorization.

### Impact Propagation

Walk the upstream change through actual dependencies (peer modules,
consumers). Use existing impact machines when available
(`/architecture impact <spec-id>` or
`.claude/skills/architecture/references/impact-analysis.md`). Do not
run a project-wide scan for every correction.

### Targeted Verify

After the upstream correction lands and this Skill applies a material
change as a result, run Targeted Resolution Verification (Mode B)
per `.claude/references/verification.md` §3 Trigger B. Bound the loop:
one initial Targeted Verification; at most one additional corrective
fix + one additional Targeted Verification; beyond that, stop and
report the unresolved constraint.

### Resume

Pick up where Step X was interrupted. Update `# Resume Notes` with:

- The original task (which module, which Step).
- The blocker reason and the located authority.
- The correction result.
- The exact resume position.

Within existing authorization, the Main Agent handles the correction
autonomously and resumes — the user is informed but does not become a
review scheduler.

### Cross-session Resume

For cross-session resume, persist only:

- Current open frontier (which Step / which fields).
- Any blocking upstream issue plus its correction result.
- The exact resume position in `# Resume Notes`.

Do not create a separate task tracker or parallel issue log.

## 13. Completion and Handoff Criteria

A module design is ready for Implementation Handoff when:

- Public contracts are complete for every provided Capability.
- Each assigned Spec Requirement has an observable verification
  method whose expected result derives from the Requirement, not the
  implementation.
- No Blocking Unknown remains. Non-Blocking Unknowns are recorded in
  `# Blocking Unknowns and Implementation Handoff`.
- Either a Targeted Resolution Verification has returned clean for
  material changes, or Self-check is sufficient for low-risk modules.
- Downstream dependencies (other modules' design or implementation)
  are not silently blocked by missing inputs from this module.

`DESIGN.md` plus optional `contracts/*.yaml` IS the contract for
Implementation. The Implementation Agent must be able to proceed
without re-reading this Skill's chat history.

`status: final` means the design is handed off; it does **not** imply
`Implementation Verified` — that belongs to Verification after
runtime evidence.

### One explicit confirmation is enough

When the user has explicitly confirmed the current stage's
completion (`确认，继续` / `设计没问题了` / `MOD-foo 可以交给实现了`)
in response to a recent completion proposal, that single
confirmation authorizes:

- Setting `DESIGN.md status: final` for this module.
- The corresponding Implementation Handoff (`new <module-id>` next).

Do not prompt a second time ("are you sure?") for the same scope.
Do not extend the authorization to unrelated modules, unrequested
Spec edits, or Architecture changes. Material changes to the goal,
scope, or key constraints that surface during a subsequent round
remain user decisions — they are not covered by the prior
confirmation.

A new confirmation is required when:

- The user re-opens the module (`reopen`).
- A subsequent correction changes a Spec REQ or Architecture
  ownership that the prior confirmation did not cover.

## 14. Hard Rules

1. **Provider owns the contract.** Only the unique Provider of a
   Public Capability may author or modify that capability's contract
   content. Consumers file change requests via Cross-layer
   Coordination; they do not silently edit Provider contracts.
2. **One authoritative DESIGN.md per module.** Do not split a
   module's design into parallel DESIGN files. Optional
   `contracts/*` files are fine for machine-readable artifacts but
   must not contradict `DESIGN.md`.
3. **Public contract first.** Step 2 (contract) precedes Step 3
   (internal design). Internal design may iterate freely after the
   contract is settled; contract changes after Step 4 that affect
   Consumers must go through Cross-layer Coordination.
4. **No upstream override.** Do not silently edit a Spec, an
   Architecture Baseline, or another module's contract. Route via the
   feedback contract and let the correct Owner decide. An archived
   Spec or an adopted Architecture Baseline require the existing
   reopen / revise flow with user authorization.
5. **Verified technical premises.** Load-bearing library, protocol,
   or state-machine premises must cite a primary source. Use the
   search rules in `CLAUDE.md`. Unverified premises become Unknowns,
   not assumptions.
6. **No silent business defaults.** Magic numbers, thresholds, and
   library defaults that the user has not chosen do not enter
   `DESIGN.md` without explicit user authorization. Routine internal
   choices (data layout, file naming) do not need user authorization.
7. **Reuse, don't copy.** Cross-layer rules live in
   `cross-layer-coordination.md`; Reviewer rules live in
   `independent-reviewer.md` and `verification.md`. Do not duplicate.
8. **Reuse existing conventions.** When the project already has coding
   conventions, dependency choices, or test patterns, follow them.
   Do not introduce a parallel convention just because this Skill
   runs.
9. **No parallel lifecycle.** `DESIGN.md` uses `draft | final`. No
   new approval states. `final` does not imply `Implementation
   Verified`; that belongs to Verification after runtime evidence.
10. **No new Subagent.** This Skill does not introduce new Agents. It
    reuses the existing Independent Reviewer and operates within the
    Main Agent.
11. **Bind the loop on cross-layer correction.** When applying a
    corrective change in response to upstream feedback, do not start
    an unbounded Fix → Verify cycle. The cap is in
    `.claude/references/verification.md` §6.
12. **Persist the resume position.** Do not assume chat history
    carries state across sessions; persist the open frontier.
13. **Lightweight.** Don't over-table. Don't add decision records
    unless the decision is materially novel and recurring.

## 15. References

- `.claude/references/cross-layer-coordination.md`
- `.claude/references/verification.md`
- `.claude/agents/independent-reviewer.md`
- `.claude/skills/spec/SKILL.md` (§14 review; §19 Routing)
- `.claude/skills/architecture/SKILL.md` (§7 Revise, §8 Review, §10 Handoff)
- `.claude/skills/spec/references/review.md` (§2.1 delegation template)
