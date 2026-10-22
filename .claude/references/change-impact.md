# Item-level change impact and recovery

Use this reference when an Intent item, Requirement, invariant, Architecture
decision/ownership, public contract, or its implementation changes, and when
resuming work after a gap. It refines cross-layer coordination §2.4; it is not
a separate authority, lifecycle, or manually maintained relationship index.

## 1. Reconstruct the evidence graph

Read the current working tree **and** Git status. Compare with the last
reliably adopted version (commit, tagged handoff, or explicit baseline
reference); record when that version cannot be found. Use stable item IDs
first, then the containing section and its semantic text:

`Intent goal/constraint/decision → Spec REQ/INV + acceptance → Architecture
capability/owner/decision → Design provided/consumed contract → code,
serializer/UI, tests and real-run evidence`.

Existing `source_intents`, `source_spec`, `source_architecture`, REQ/INV/AD
citations, ownership tables, contract references, and test or Resume Notes
are the links. A file-level link locates candidates; it does not prove which
items or evidence are affected. Expand cited ID ranges. Search for missing
reverse links and consumers in the actual code. If an item has no stable ID,
citation, or reliable old version, use its section and mark the relation
uncertain; add a precise citation to the owning document when editing it.
If an old item was renamed or split, map old to new by meaning and record
the mapping rather than assuming the ID itself is unchanged.
Do not invent coverage or create a parallel relationship database.

## 2. Compare meaning before propagating

For every changed item, state the old and new behavior, input/output,
ordering, failure, acceptance, or contract semantics with file/line or Git
evidence. A wording-only edit with the same meaning ends here after a local
reference check. A semantic change starts a read-only impact analysis before
downstream edits. For a working-tree version, distinguish an edit in progress
from a snapshot whose owning layer completed its scoped review/handoff checks.
Neither Git cleanliness nor dirtiness decides readiness: apply cross-layer
coordination §2.5.c. Never describe a dirty snapshot as committed delivery.

Walk only dependency edges justified by citations, Architecture ownership,
provided/consumed contracts, or actual code and test usage. For a changed
public field, query, or data meaning, walk Provider → every actual Consumer,
including serialization, UI, contract/integration tests and real-path checks.
Stop a branch when evidence shows the changed item is not used there or the
existing contract still satisfies it. Missing references or uncertain usage
are `unknown — investigate`, not `unaffected`.

For each candidate artifact report: **path through items/contracts; observed
effect; evidence; owner; verdict** (`modify`, `revalidate only`, `unaffected`,
`unknown — investigate`). Do not reopen an unaffected authority. If an
affected document already describes the new semantics, verify consistency
and choose `revalidate only`; status alone is not evidence.

## 3. Scope old evidence and close the chain

An old `final`, PASS, Review, or real run remains historical evidence for the
version and contract it checked. It does not establish the changed item.
For affected evidence, report `pending revalidation` as an assessment, not a
new lifecycle state or an edit to the old record. Reuse unaffected evidence.
If the old run does not name its item/contract scope, source revision, test
command/environment, and observed result, say `scope unknown`; investigate
before calling it current. Real-path evidence also names the actual start,
dependencies and visible failure behavior. Mock/static checks keep their
limited scope.

Record the smallest recovery note in the existing artifact's `# Resume Notes`:
changed item IDs and old/new basis, affected owner/contract path, verdict,
old evidence scope, missing check, and the next executable action. For new
verification evidence, record item/contract IDs, source commit or Git blob
IDs, working-tree cleanliness, command/environment, result, and evidence
location. A dirty run may be useful evidence but cannot certify a committed
handoff; a later commit or semantic change requires checking applicability.
No repeated approval is needed for in-authority corrections; use the existing
impact-based authorization rule for genuine product choices.

On entry, resume, cross-layer return and handoff, use cross-layer §2.5.c
to select work against this evidence. An impact report is an input to that
check, not permission to start every downstream action it lists. Preserve
the interrupted work's return point while its prerequisite is being fixed.
When quoting evidence in another layer, preserve observation vs estimate vs
assumption and the tested boundary (verification.md §4.9).

The chain closes only after each affected authority is corrected or confirmed
current, its impacted code and tests are checked, and required real user-path
evidence is observed. Report document/contract, local code/test, and real-path
closure separately. If a dependency or environment is missing, leave the
specific obligation and resume action open.
