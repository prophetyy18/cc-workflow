# Impact Analysis Methodology

The full 8-step methodology for `/architecture impact <spec-id>`. Load on demand. Architecture Impact is **read-only** by default — it produces an Impact Plan, not a Baseline change.

## Goal

For a Spec change, identify:

- What changed semantically (not just textually)
- Which System Capabilities are affected
- Which Modules are affected
- Which Public Capabilities / Contracts are affected
- Which downstream Consumers and Documents are affected
- Whether the existing architecture can absorb the change or needs Revision
- The minimum evidence supporting each claim

The output is a short, executable Impact Plan with a clear **A / B / C** decision. See SKILL.md §6 for the decision definitions.

---

## Step 1 — Establish the Spec Delta

Compare the current Spec against the last adopted architecture baseline. Search:

- `ARCHITECTURE.md` and its `# Spec Baseline References` section
- Git history (`git log` for the Spec file)
- Archived `SPEC.md` snapshots
- `# Resume Notes` mentioning baseline adoption

If a reliable baseline exists, compare:

- **Added Requirements** — new REQ-IDs, or new sections
- **Removed Requirements** — REQ-IDs no longer present
- **Materially Changed Requirements** — same ID, different meaning
- **Changed System Invariants**
- **Changed Timing / State Semantics**
- **Changed Acceptance Obligations**
- **Editorial-only Changes** — wording only, no semantic change

**A stable ID is necessary but not sufficient.** Two Requirements with the same `REQ-001` may have very different meaning. Read the actual content, not just the IDs.

If no reliable baseline exists, say so explicitly and fall back to "current Spec vs current architecture compatibility check". Do not pretend you have a full history.

## Step 2 — Find Affected System Capabilities

For each actual change, ask:

- Does this add new behavior?
- Does this change input / output semantics?
- Does this change state-update rules?
- Does this change cross-capability coordination?
- Does this change critical timing?
- Does this change data-correctness requirements?
- Does this change a System Invariant?

Identify Capability impact first. Module impact comes from the Capability.

## Step 3 — Map to Actual Modules

Using the Baseline's Module Responsibility Map and Public Capability / Contract Index, find for each affected Capability:

- **Primary Owner** — the module that must satisfy the Requirement
- **Collaborating Modules** — modules that participate in the flow
- **Providers** — modules whose public capabilities are consumed
- **Consumers** — modules (or external systems) that depend on the affected behavior

If the Baseline is silent on a Capability, mark it as a Baseline gap and route feedback (see SKILL.md §11).

**Do not guess module responsibility from the module name.** If the Baseline does not name an Owner, the answer is "unknown", not "the module that sounds related".

## Step 4 — Trace Contract Consumers

For each affected Public Capability, walk the chain:

`Requirement Delta → Capability → Provider → Public Contract → Consumers → Integration / System Verification`

For each link, ask:

- Does the current contract still satisfy the Requirement?
- Can the change be implemented inside the Provider (Internal-only)?
- Does the change extend the contract in a backward-compatible way?
- Does the change break existing consumer behavior?
- Does the change require a new Public Capability?
- Which consumers actually depend on the affected part of the contract (not the whole contract)?
- Which integration / E2E verifications need to be updated?

Do not assume "all consumers are affected" if only a subset depends on the affected part. Do not stop at the Provider — consumers matter.

## Step 5 — Classify Contract Impact

For each affected contract, classify:

- **Existing Contract Sufficient** — current contract semantics cover the new Requirement; no change needed.
- **Internal Change Only** — the change is in the Provider's private implementation; public contract and consumers are untouched.
- **Compatible Extension** — the public contract grows (new optional field, new method, new event) without breaking existing consumers.
- **Breaking Change** — the public contract's existing semantics or structure change; existing consumers may break.
- **New Public Capability** — the Requirement cannot be satisfied by any existing contract; a new cross-module capability is required.
- **Insufficient Evidence** — cannot reliably judge; the impact Plan must list what evidence is missing.

These are classification results, not lifecycle states. The actual contract / Schema / API change is still produced by the Contract Owner (usually via Module Design), not by Architecture.

## Step 6 — Find Documentation Impact

For each affected artifact, determine if the document genuinely needs an update, and who owns the update.

| Document | Authoritative Owner | Trigger for update |
|---|---|---|
| `SPEC.md` | Spec | The Spec's own content changed; Architecture cannot edit it. Spec should be informed. |
| `ARCHITECTURE.md` | Architecture | Ownership, dependency, contract attribution, or invariant mapping changed. |
| `MODULE-<name>.md` (per module) | Module Owner | The module's responsibility or contract surface changed. |
| Formal Public Contract | Contract Owner | The contract's behavior or shape changed. |
| Consumer Integration Docs | Relevant Owner | The consumer's integration expectations changed. |
| Contract / Integration Tests | Relevant Implementation Owner | The contract or its consumers changed. |
| E2E / System Verification | System Verification Owner | A cross-module invariant or end-to-end flow changed. |

Architecture Impact may *recommend* updates. It must not auto-edit Spec files, MODULE files, or Contracts. It may directly edit only the Baseline (`ARCHITECTURE.md` and its supporting files) when authorized via `revise`.

Do not pad the impact Plan with a long list of "may need update" entries. Only mark documents that genuinely need to change given the actual Spec delta.

## Step 7 — Evaluate Evidence

For each major claim in the Impact Plan, classify:

- **Confirmed** — backed by a specific Requirement, Baseline section, contract reference, or code path.
- **Potential** — plausible from the architecture's structure but not directly verified (e.g., "the provider module may need to refactor its internal queue").
- **Unknown** — cannot judge without further investigation (e.g., "we do not know which consumer versions are deployed").

Cite the source for every Confirmed claim (e.g., `ARCHITECTURE.md §3`, `SPEC-001/REQ-003`, `MODULE-replay.md §2`).

If a claim cannot be supported, downgrade it to Potential or Unknown — do not leave it as Confirmed by default.

If consumer evidence is incomplete, do not claim to have found all consumers. State the gap and the risk.

## Step 8 — Output the Impact Plan

The plan must include (in this order):

1. **Spec Delta** — Added / Removed / Materially Changed Requirements, changed System Invariants, changed Acceptance Obligations, editorial-only changes, baseline comparison note.
2. **Affected Capabilities** — per affected System Capability, what changed.
3. **Affected Modules** — per module, role (Primary Owner / Collaborator / Provider / Consumer).
4. **Affected Public Capabilities and Contracts** — per capability, the Step-5 classification.
5. **Documentation Impact** — per document, the change required and the owner.
6. **Verification Obligations** — which end-to-end / system / integration verifications must be updated.
7. **Unresolved Unknowns** — what is still unknown, what evidence would resolve each.
8. **Decision: A | B | C** — one paragraph of reasoning.
9. **Recommended Next Step** — `Module Design` for A; `/architecture revise <spec-id>` for B; targeted investigation for C.

Avoid generic checklists. Tailor the plan to the actual delta.

---

## Output Template

```text
## Impact Analysis: SPEC-NNN

### Spec Delta
- Added Requirements: <list or "none">
- Removed Requirements: <list or "none">
- Materially Changed Requirements: <list>
- Changed System Invariants: <list or "none">
- Changed Acceptance Obligations: <list or "none">
- Editorial-only Changes: <list or "none">
- Baseline comparison: <git commit / archived baseline / "unable to determine">

### Affected Capabilities
- <capability name>: <how it changed>

### Affected Modules
- <module name>: <Primary Owner | Collaborator | Provider | Consumer>

### Affected Public Capabilities and Contracts
- <capability name> (<owner module>): <Existing Sufficient | Internal Only | Compatible Extension | Breaking | New | Insufficient>
- ...

### Documentation Impact
- <doc path> — <owner> — <what needs update>
- ...

### Verification Obligations
- <capability / invariant>: <verification path that must hold>
- ...

### Unresolved Unknowns
- <unknown>: <what would resolve it>
- ...

### Decision: A | B | C
- Reasoning: <one paragraph>

### Recommended Next Step
- <Module Design for relevant module | /architecture revise SPEC-NNN | gather evidence: ...>
```
