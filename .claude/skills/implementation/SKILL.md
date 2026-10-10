---
name: implementation
description: Realize a finalized DESIGN.md as runnable code, tests, and verification evidence. Reads only the authoritative public contract (DESIGN.md + contracts/*) and writes code, tests, and run-time evidence under the module's impl/. Reuses Cross-layer Coordination for upstream errors and the Independent Reviewer for verification. Use when the user wants to start implementation from a finalized design (`/implementation new MOD-foo`), resume work, run tests, request review, or hand off to delivery. Triggered by phrases like "implement MOD-foo", "实现 foo", "build MOD-foo", "run MOD-foo tests", "verify foo".
allowed-tools: Read, Edit, Write, Glob, Grep, WebFetch, WebSearch, Bash(date*), Bash(test*), Bash(python3*), Bash(pytest*), Bash(go test*), Bash(npm test*)
---

# Implementation Skill

Realizes a finalized `DESIGN.md` as runnable code, tests, and
verification evidence. The Main Agent runs this Skill — Implementation
does not introduce a new Subagent. The Skill uses the project's
existing tools (test runner, package layout, dependencies) and reads
only the authoritative public contract (`DESIGN.md` § Provided Public
Contracts plus `contracts/*.yaml`). It discovers upstream errors
through runtime evidence and routes corrections through the existing
Cross-layer Coordination.

## 1. Layer Boundaries

| Layer | Owns | Does not own |
|---|---|---|
| **Intent** | User goals, constraints, decisions | System behavior, modules, contracts |
| **Spec** | System capabilities, Requirements, invariants, acceptance | Module names, capability naming, code |
| **Architecture** | Module boundaries, capability ownership, dependency direction, cross-module invariants | API, schema, internal algorithms, code |
| **Module Design** | Public contract content (Provider side), internal design, DESIGN.md, contracts/ | Code, tests, runtime, adopted Baseline, archived Spec |
| **Implementation** (this Skill) | Code, tests, runtime evidence, internal test fixtures (own files only) | Public contract content, module boundary changes, adopted Baseline, archived Spec |

**Implementation is the authority for runtime behavior. Module Design
is the authority for what the runtime must satisfy. Architecture is
the authority for which module does what.**

## 2. Subcommand Routing

Read `$ARGUMENTS`. First token is the subcommand, the rest is the target.

| Subcommand | Target | Behavior |
|---|---|---|
| (empty) or `help` | — | Show this help |
| `new` | `<module-id>` | Start implementation for a finalized `DESIGN.md` |
| `resume` | `<module-id>` | Continue an in-progress implementation |
| `test` | `<module-id>` (optionally `test <glob>` for one file) | Run all / specified tests and report outcomes |
| `verify` | `<module-id>` | Trigger A — full Independent Review of code + tests |
| `status` | `<module-id>` | Print current state, test outcomes, blockers |
| `handoff` | `<module-id>` | Finalize; run Targeted Verification (Trigger B) if material changes since last verify |

If the subcommand is unknown, do not guess. Show help and stop.

## 3. Natural-Language Operations

| User intent (paraphrased) | Action |
|---|---|
| "implement MOD-foo", "把 foo 实现了", "build MOD-foo" | `new` (if `DESIGN.md` is `final`); `resume` (if `draft`) |
| "跑一下 MOD-foo 的测试", "test foo" | `test` |
| "审一下 foo 的实现", "verify foo" | `verify` |
| "看下 foo 进度", "status foo" | `status` |
| "foo 完成了", "hand off foo" | `handoff` (after Completion Check §13) |

**Modification is the default, not creation.** A module's `impl/` is
modified, not duplicated.

## 4. Identity & Storage

Implementation is per-module; one module's `impl/` lives next to its
`DESIGN.md`:

```text
docs/modules/MOD-<name>/
├── DESIGN.md                  (Module Design's output; read-only for this Skill)
├── contracts/                 (Module Design's optional public contracts; read-only)
└── impl/                      (this Skill's output)
    ├── src/                   (or flat package; follow project convention)
    └── tests/                 (or `test_*.py` flat; follow project convention)
```

If the consuming project uses a different layout (e.g., monorepo
with `packages/<name>/`), follow the project convention. Do not
invent a parallel layout. Implementation does NOT create a top-level
`src/` or `tests/` if the consuming project already defines where
modules live.

## 5. Subcommand: `new <module-id>`

Run `new` only when:

- `DESIGN.md` for `<module-id>` exists with `status: final`, OR the
  user has explicitly asked to start from `draft` (record the
  divergence in `# Resume Notes`).
- The Provider's public contract is reachable (`DESIGN.md` § Provided
  Public Contracts and / or `contracts/*.yaml`).

If `DESIGN.md` is missing or stuck at `draft`, surface the blocker
and point at `/module-design resume <module-id>` (or `new`). Do not
invent Requirements or contracts.

### Step 1 — Read upstream

Read in order:

1. `docs/modules/MOD-<name>/DESIGN.md` end-to-end (Goal, Provided
   Public Contracts, Consumed Public Contracts, Internal Design,
   Verification, Unknowns, Resume Notes).
2. Any `contracts/*.yaml` — authoritative when present.
3. The Source Spec REQ-IDs this module owns (from DESIGN's
   `source_spec`) — read each Spec's `# Acceptance and Verification`.
4. The Provider-side public contract dependencies listed in `DESIGN.md`
   § Consumed Public Contracts.

If DESIGN.md is silent on a field the implementation needs, do not
invent. Either fill the Internal Design step consistent with the
Verified Premises rule (§14 Hard Rule 6) or surface as Unknown and
route to Module Design.

### Step 2 — Implement internal code

Write code under `docs/modules/MOD-<name>/impl/`. Follow existing
project conventions when one exists (check `pyproject.toml`,
`package.json`, `go.mod`, etc.). When none exist:

- Pick the simplest layout (flat package + tests).
- Match the language used by other modules in the same project. If
  none, pick a sensible default and document the choice in
  `# Resume Notes` (not in the canonical `Internal Design` section
  unless load-bearing).
- Do NOT introduce heavy frameworks, build systems, or dependency
  managers without explicit user authorization.

Constraints:

- Code produces real observable behavior — no placeholder functions
  returning fixed values, no `pass`, no `TODO: implement` on a path
  the public contract exposes.
- Internal helpers are private to the module; their shape is the
  Implementation's call.
- The Provider's PUBLIC API surface must match `DESIGN.md` and
  `contracts/*.yaml` exactly. Consumers depend only on the public
  surface.

### Step 3 — Write tests

For each assigned Spec Requirement and each public Contract field:

1. Write an observable test that produces a verifiable pass/fail
   signal. The test must not depend on the implementation's own
   bookkeeping — call into the public API from outside the module
   under test.
2. Cover valid input, boundary input, and at least one failure per
   public capability.
3. Where DESIGN includes a verification strategy with specific
   expected outcomes, encode those outcomes in the test — derived
   from the Requirement, not the implementation.

Use the project's existing test framework; if none, prefer a
lightweight standard-library approach (Python `unittest`, Go's
built-in `testing`, etc.). Do not add a heavyweight framework unless
the existing project already uses it.

For Consumer modules, also write an integration test that exercises
the Provider's real public API in a non-trivial flow. Do not stub
Provider when Provider is already implemented.

### Step 4 — Run tests

Run the test suite. Capture the actual command + exit code + summary.
Record outcomes distinctly:

- **PASS** — the test ran and produced an expected pass.
- **FAIL** — the test ran and produced a fail; record the message.
- **NOT RUN** — the test file was not executed (e.g., syntax error in
  another file prevented collection). Record the reason.

A "tests pass" outcome is NOT evidence the implementation is correct
on its own — only that the tests they wrote passed. Re-check the
tests' own coverage against the Public Contract and Spec
Requirements (see `verification.md` §4.4 and §4.6).

### Step 5 — Targeted Verification (Trigger A)

If the implementation satisfies any Trigger A criterion in
`.claude/references/verification.md` §3 (e.g., money / assets /
security / data correctness / public contract), run Independent
Review (Mode A) before announcing `handoff` readiness.

For low-risk modules (pure rendering, dev tooling, test fixtures),
this Skill's Self-check is sufficient. Do not run a full Review for
every trivial change. The Reviewer delegation contract is in
`verification.md` §2; the reasoning frame is in
`.claude/agents/independent-reviewer.md`.

## 6. Subcommand: `resume <module-id>`

`# Resume Notes` for a module lives in the module's `DESIGN.md`
(canonical). This Skill reads and writes there. Do not start a
separate log — a parallel log drifts from the design and from any
later Module Design update.

1. Load the `impl/` tree and `# Resume Notes` from the module's
   `DESIGN.md`.
2. Continue from the open frontier (Step 2 → 5 as needed).
3. After any material change satisfying Trigger B criteria
   (`verification.md` §3 Trigger B), run Targeted Resolution
   Verification (Mode B) before resuming normal flow.
4. Update `# Resume Notes` in `DESIGN.md` with the new resume
   position.

## 7. Subcommand: `test <module-id> [glob]`

Run all tests under the module's `impl/` — or the subset matching the
optional `glob`. Use the project's existing runner; if none, run with
the runner declared in `# Resume Notes` from Step 2. Report outcomes
with the same PASS / FAIL / NOT RUN discipline as Step 4. Do not
silently rename or skip tests.

If the run reveals a runtime regression:

- If the bug is local to the module's code, fix it within this
  Skill's authority.
- If the bug points upstream (Provider contract, Spec REQ,
  Architecture ownership), apply §12 Cross-layer Triggers — do not
  silently rewrite another module's contract or an archived Spec.
- If the bug is in upstream Spec or Architecture Baseline, route via
  `/spec resume` / `/architecture revise` per the established
  feedback contract.

## 8. Subcommand: `verify <module-id>`

Trigger A — full Independent Review of the module's code + tests.
Use the delegation contract from `verification.md` §2 with
`Review Type: Implementation`. Apply the Reviewer's verification
principles (`verification.md` §4) — particularly §4.4 (Acceptance
Criteria), §4.5 (Architecture & Contracts), and §4.6
(Implementation).

Triage the Reviewer's findings in this Skill. If the Reviewer finds
real defects, surface them through normal dev flow (fix + Targeted
Verification). Do not propagate the Reviewer's suggestions
verbatim — this Skill triages with the same Derive → Locate →
Resolve → Validate discipline as Spec's Triage
(`.claude/skills/spec/references/review.md` §2.7).

## 9. Subcommand: `status <module-id>`

Print:

- Implementation completeness — pass/fail per public capability.
- Last test command + result summary.
- Open fronts (uncovered branches, missing boundary tests).
- Cross-layer feedback references.
- Trigger A review status (when applicable).

No edits.

## 10. Subcommand: `handoff <module-id>`

1. Load `impl/`.
2. Run Completion Check (§13).
3. Run Targeted Verification (Mode B) per `verification.md` if any
   material change since the last successful verify.
4. Record handoff state in `# Resume Notes`. Do NOT introduce a new
   lifecycle field. Implementation completion does NOT equal
   `Implementation Verified (Production)` — that belongs to
   downstream delivery verification after staging/production
   evidence.

## 11. Test Methodology (concise)

- **Unit tests** — exercise one module's public API; no other module
  imported via internal path.
- **Integration tests** — exercise cross-module flows via the
  public contracts; real Provider implementations, not stubs.
- **Boundary tests** — explicit edges: empty input, maximum input,
  equal-to-threshold inputs, non-numeric input. Boundaries spelled
  out in the Public Contract or Spec Requirement are tested; other
  boundaries optional.
- **Failure tests** — at least one failing case per public
  capability whose contract lists a failure semantics.
- **Verification derivation** — every expected outcome in a test is
  derived from a Spec Requirement or Contract field, NEVER from the
  implementation's own helper output.

Do NOT write tests that depend on the implementation's own
bookkeeping (e.g., asserts on a private counter). Such tests cannot
catch wrong implementations; the Reviewer will surface them per
`verification.md` §4.4.

## 12. Cross-layer Triggers

When implementation reveals an upstream error (Provider contract
wrong, Spec REQ wrong, Architecture ownership wrong), apply the
existing Cross-layer Coordination. The flow this Skill follows:

```
Discover → Establish Evidence → Locate Authority → Minimal Correction
        → Impact Propagation → Targeted Verify → Resume
```

### Discover

The symptom appears in tests, runtime errors, or Reviewer findings.
State the symptom and the authority level the symptom points to. Do
not normalize the symptom into a local code patch.

### Establish Evidence

Cite the Public Contract field, the Spec REQ-ID, or the Baseline
section that proves the upstream is wrong. Show, do not assert.

### Locate Authority

- Public Contract content wrong → Provider's Module Design (the
  module that owns the contract).
- Spec REQ-ID wrong → Spec Skill (via `modify` + reopen flow).
- Architecture ownership wrong → Architecture Skill (via `impact` +
  `revise` flow).

Apply `cross-layer-coordination.md` §4 (Minimum necessary
escalation).

### Minimal Correction

Edit only the necessary authority. Do not silently rewrite an
archived Spec or an adopted Architecture Baseline — use the existing
reopen / revise mechanisms with user authorization. For a public
contract owned by THIS module, this Skill itself fixes the contract
(rare; almost always involves Module Design first).

### Impact Propagation

Walk the change through actual dependencies (peer modules,
consumers, integration tests). Use existing impact machines
(`/architecture impact` if ownership changed; otherwise re-run
Consumer's tests against the new contract).

### Targeted Verify

After the correction and the local re-implementation, run Targeted
Resolution Verification (Mode B) for material changes per
`verification.md` §3 Trigger B. Bound the loop:
`verification.md` §6 (1 + 1 + 1 cap).

### Resume

Pick up the interrupted Implementation task. Update `# Resume Notes`
with: original task, blocker, correction result, resume position.
In-session, the Main Agent continues the same task without
re-prompting for unrelated permissions; for cross-session, persist
the resume position.

## 13. Completion and Handoff Criteria

Implementation is ready for handoff when:

- `DESIGN.md` is `final` (Provider is the unique publisher of the
  public contract; this Skill did not modify it unless this module
  IS the Provider and the contract edit was authorized).
- Each public capability in `DESIGN.md` § Provided Public Contracts
  has at least one observable test.
- Each assigned Spec REQ has an observable test whose expected
  outcome derives from the Spec, not the implementation.
- Test suite is PASS (no FAIL; no NOT RUN left over from initial
  collection issues).
- No Blocking Unknown from `DESIGN.md` § Blocking Unknowns remains
  open against this module.
- Either a Trigger A review returned clean, or Self-check is
  sufficient for low-risk modules.
- A Trigger B verification ran clean for material changes since the
  last verify.

`DESIGN.md` final + `impl/` committed does NOT mean
`Implementation Verified (Production)`. That belongs to downstream
delivery verification after staging/production evidence.

### One explicit confirmation is enough

When the user has explicitly confirmed the current stage's
completion (`确认，继续` / `MOD-foo 没问题了` / `可以发布了`) in
response to a recent completion proposal, that single confirmation
authorizes recording the handoff state in `DESIGN.md # Resume Notes`
and surfacing the next-step pointer (delivery, deployment, etc.).
Do not prompt a second time ("are you sure?") for the same scope.
Do not extend the authorization to other modules, unrequested test
changes, or contract edits.

Reserved confirmations (those that still need a fresh "确认，继续"
from the user) cover material changes to goal, scope, or key
constraints, plus anything that surfaces a previously unknown
trade-off the agent cannot decide alone.

## 14. Hard Rules

1. **Provider owns the contract.** This Skill reads the public
   contract as authoritative; if the contract content is wrong, the
   fix lives at the Provider's Module Design — not in this Skill's
   local code. (Exception: when this module IS the unique Provider
   AND Module Design's contract edit was authorized, this Skill
   re-implements the contract faithfully.)
2. **One `impl/` per module.** Do not split a module's
   implementation across multiple trees or top-level src/
   directories.
3. **Tests before claiming completion.** PASS / FAIL / NOT RUN are
   the only three states; record each. "It should work" is not
   PASS.
4. **Real code, no placeholders on contract-exposed paths.** Do
   not commit placeholder functions returning fixed values, `pass`,
   or `TODO: implement` on a path the public contract exposes.
5. **Tests independent from the implementation's bookkeeping.**
   When the Reviewer surfaces a test that calls into the
   implementation's own helper, fix the test, not the helper's
   callers.
6. **Verified premises.** Load-bearing library / protocol /
   state-machine premises cite a primary source per `CLAUDE.md`
   Search Rules.
7. **Reuse, don't copy.** Cross-layer rules live in
   `cross-layer-coordination.md`; Reviewer rules live in
   `independent-reviewer.md` and `verification.md`. Do not
   duplicate.
8. **Reuse project conventions.** Follow the project's existing
   test framework, package layout, dependency manager. Do not
   introduce a parallel convention just because this Skill runs.
9. **No new Subagent.** This Skill does not introduce new Agents.
   It uses the existing Independent Reviewer and operates within
   the Main Agent.
10. **No parallel lifecycle.** `DESIGN.md` uses `draft | final`.
    Implementation does not introduce `passing / merged / released`
    or other statuses.
11. **Bind the loop.** When applying a corrective change in
    response to upstream feedback, do not start an unbounded Fix →
    Verify cycle. The cap is in `verification.md` §6.
12. **Persist resume position.** Cross-session resume depends on
    `# Resume Notes`.
13. **Lightweight.** Avoid heavyweight frameworks, monorepo
    sprawl, or any "release pipeline" that is not part of the
    project's existing convention.

## 15. References

- `.claude/references/cross-layer-coordination.md`
- `.claude/references/verification.md`
- `.claude/agents/independent-reviewer.md`
- `.claude/skills/module-design/SKILL.md` (`DESIGN.md` source of truth)
- `.claude/skills/architecture/SKILL.md`
- `.claude/skills/spec/SKILL.md`
- `.claude/skills/spec/references/review.md` (§2.7 triage)
