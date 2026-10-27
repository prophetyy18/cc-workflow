# Cross-layer coordination

This reference owns decisions shared by Intent, Spec, Architecture, Module
Design, Implementation and Verification. Each Skill owns only its layer's
content and completion checks. Apply these rules to the **affected item or
contract**, not automatically to an entire document or project.
`change-impact.md` locates dependencies; `verification.md` owns reviews and
runtime evidence.

## 0. Reasoning boundary

Derive necessary behavior from the highest applicable authority; locate the
gap; let its owner resolve it; verify the actual resolution. A review finding
is evidence to triage, not an edit or final decision. Feedback sent, content
edited, review returned and runtime verified are distinct events.

## 1. Authority layers

| Layer | Decides |
|---|---|
| Intent | User goal, starting state, confirmed order, success and constraints |
| Spec | System behavior, invariants and acceptance |
| Architecture | Module responsibility, capability ownership and dependencies |
| Module Design | Provider/Consumer contracts and module design |
| Implementation | Code, executable tests and implementation evidence |
| Verification | What a review or real run actually demonstrated |
| User | A change to confirmed product meaning or an unresolved material choice |

The layer that recorded an evidence claim corrects it. A corrected fact does
not automatically invalidate every Requirement citing it: trace its actual
use and decide whether each conclusion needs an edit, revalidation, or none.
Engineering difficulty or cost is evidence for investigating options; it is
not a user-confirmed Intent constraint unless the user adopts it.

## 2. Cross-layer work

### 2.1 Identify

Compare the finding with the current authoritative item and evidence. If the
current owner can preserve confirmed upstream constraints, it fixes its own
content. Otherwise locate the smallest authority whose content must change.
An uncertain fact requires investigation, not necessarily a product decision.

### 2.2 Escalate

Send the contradiction, source item, evidence, needed decision and return
point to that owner (§3). Do not default to Intent or ask the user to
dispatch Skills. The Main Agent enters the owning Skill under current task
authorization.

### 2.3 Resolve

The owner re-derives the answer from its sources, then accepts, rejects,
defers for named evidence, or redirects the finding. Record actual edits and
outstanding checks. Feedback received or content edited is progress, not
resolution.

### 2.4 Propagate

Use `change-impact.md` to follow only justified dependencies: source item →
relevant Requirement/acceptance → ownership/contract → Provider and actual
Consumers → code, tests and real-path evidence. Classify each candidate
`modify`, `revalidate only`, `unaffected`, or `unknown — investigate`.
Old PASS and `final` remain historical for their tested scope. Stop a branch
at an evidenced unchanged boundary; do not reopen unrelated work.

### 2.5 Verify and Return

Reread the changed authoritative artifact, applicable review and open
conditions. Check the original necessary condition and affected references;
do not accept a return message as proof. Resume dependent work only when the
owner actually closed the affected prerequisite (§2.5.c). A runtime
obligation can remain for Implementation (§2.5.e).

### 2.5.b Authorization by impact

An instruction to complete a goal covers necessary internal correction,
reopen/revise, review and return when confirmed upstream meaning determines
the fix. A layer boundary or operation name is not a new approval. Ask the
user only if the proposed result changes confirmed product meaning, order,
scope, key constraint or compatibility, or if the sources leave a material
product trade-off unresolved. Investigate a compliant solution first. An
optional alternative that would change confirmed meaning is deferred while
the confirmed path remains feasible; it does not block compliant work or
require a user choice now. An internal contradiction alone does not
authorize choosing one of two possible user-visible outcomes.

### 2.5.b.1 Routine correctness

A correction is routine when current authorization covers it, upstream
sources determine the answer, confirmed meaning is preserved and no product
choice remains. Its owner uses the normal edit and review flow, including
`reopen` or `revise` where required.

### 2.5.c Execution prerequisites

At entry, resume, cross-layer return and handoff, check the selected scope:

1. Read actual upstream content/version and open decisions. Determine which
   review and evidence still apply. A status, old PASS, existing code or
   `RESOLVED UPSTREAM` note is not sufficient.
2. If any plausible unresolved outcome would change this work's behavior,
   contract or acceptance, affected dependent work waits for the owner's
   resolution and required review. An obvious fix direction does not release
   formal affected implementation before the contract is revised and reviewed.
3. Continue unaffected work on its accepted basis. Git dirtiness is neither
   a global stop nor a delivery claim. Authorized exploration against open
   premises is provisional and cannot certify a handoff.

If blocked, save the sought result, source version, missing condition, owner
and return point in existing Resume Notes. Resolve at the owner, reread the
artifacts and repeat the check. Sending feedback is not closure.

### 2.5.e Prerequisite or handoff obligation

If plausible results of an unknown could change behavior, contract or
acceptance, it is an affected Design prerequisite. Relabeling it as an
Implementation obligation does not release Design. If all plausible results
leave Design valid and only a running implementation can verify the property,
record a specific Implementation verification obligation and hand it off.
Runtime performance commonly belongs here: retain the accepted bound for
measurement; an estimate cannot relax it.

### 2.6 Resume

The Main Agent resumes the original task from its saved position after
§2.5.c passes. It selects the next closable work without asking the user to
schedule stages. Reviewer timeout or missing real environment leaves that
evidence open while unrelated work may continue.

## 3. Feedback contract

### 3.1 Forward message

In the existing artifact record source finding/item IDs, target owner,
problem, evidence with scope, decision needed, affected path and return
point. Short prose suffices; no new issue file or fixed template is required.

### 3.2 Return message

Record decision and reason, changed item/version (or `none`), review/runtime
evidence actually obtained, downstream scope and remaining obligations.
The originating owner verifies the artifact itself.

### 3.3 Storage

Use existing `# Unknowns and Upstream Feedback`, `# Resume Notes`, or
Architecture change notes. Do not create a second relationship database or
lifecycle state.

## 4. Minimum necessary escalation

The highest necessary authority fixes the root cause first. Propagate through
actual consumers; stop where an artifact already satisfies the new basis.
The evidence-record owner corrects its record; each affected conclusion's
owner decides whether to edit or revalidate. Product choices go to the user
under §2.5.b.

## 5. Closure semantics

| Claim | What it establishes |
|---|---|
| Review Executed | A scoped independent report returned; findings may remain open |
| Authority Resolved | The owner corrected or justified affected content and completed applicable review/handoff checks |
| Implementation Verified | Actual code, data or runtime behavior was observed for the stated boundary |

These are versioned evidence claims, not new document statuses. A review call
or edit alone proves none of the later claims. Report document/contract
closure, code/local tests and real user-path acceptance separately.
`verification.md` owns review triggers, evidence levels, failure handling
and loop bounds.

## 6. Anti-patterns

The checks above address recurring errors: sending every defect to Spec;
renaming an open contract question to pass it downstream; reopening unrelated
work because one file changed; and claiming user success from local tests or
status. Optional review advice does not expand necessary work. A repeated
finding requires better evidence or a different method (`verification.md` §6).

## 7. When to load this reference

Read the relevant section when work crosses authority or depends on changed
upstream content. Routine single-layer edits use their owning Skill.
`/workflow status` and `/workflow continue` use these prerequisite and impact
rules to select work.

## 8. End-to-end user journey

### 8.1 Principle

The source Intent anchors the user's real starting state, known inputs,
confirmed order, visible success and failure. Each layer derives only the
capability or contract it owns. A path fails if a step needs a result not yet
produced, no Provider supplies a capability, or system work silently moves
to the user.

### 8.2 Acceptance from the real starting state

Component tests, mocks and static checks establish only their observed
boundary. A required real path is accepted after its transitions run under
actual operating conditions; otherwise name the missing environment and
keep that acceptance open (`verification.md` §4.7–4.8).

### 8.3 Scope

Apply the same reachability check to UI, CLI, API and data pipelines. The
Intent supplies the sequence; no second journey checklist or status exists.

### 8.4 Layer application

Intent records goal and starting state. Spec defines behavior and observable
acceptance. Architecture assigns owners and dependencies. Module Design
makes Provider/Consumer contracts compose. Implementation exercises the path
and failure behavior. Each layer checks only what it can define or observe
and routes other gaps to their owner.

### 8.5 Reviewer discipline

The independent Reviewer derives the path from source Intent before
challenging an artifact. It reports broken transitions and likely owner;
it cannot claim runtime execution.

### 8.6 Authority

Fix the broken transition at the smallest affected item in the highest
necessary layer (§4), preserving confirmed user meaning.

### 8.7 Completion claim

Report documents/contracts, module code and contract evidence, and real
user-path evidence separately. A module handoff closes only its verified
scope; only the full path establishes user success under real conditions.

### 8.8 Per-step reachability

#### 8.8.1 Describe each transition

At the starting state, identify what the user knows and supplies, what the
system has, what each action shows on success and failure, and which earlier
output the next action needs. Prose is enough.

#### 8.8.2 Check reachability

Check each input is available when needed, its Provider is ready, and the
next action does not depend on itself or a later result. Evidence claimed as
complete must cover the scope needed. Preserve confirmed choices and order.

#### 8.8.3 Resolve and verify

Route by §4. At a module Implementation handoff, exercise its required real
public and available integration boundaries and record the covered steps,
failure behavior, conditions and unexercised transitions (`verification.md`
§4.7). The integration owner runs the full sequence from its initial state
before claiming user-path acceptance. A final Design or module handoff is
not that acceptance.
