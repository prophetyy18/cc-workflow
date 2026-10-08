# Fact Verification (Evidence-Triggered)

When to verify a factual claim during Spec work, and how to reuse existing evidence without over-researching. Read on demand during intake, capability discovery, Requirement derivation, Spec review, and material changes.

## Goal

Establish an **adequate** factual basis for each load-bearing Requirement. Not maximum research — adequate evidence.

## 1. When Fact Verification Triggers

Fact verification is not limited to the initial Spec risk review. It applies at any point a load-bearing factual claim is encountered:

- **Intake** (risk review) — claims about the system domain (e.g., "Uniswap v4 supports hooks").
- **Capability discovery** — claims about what the system must do (e.g., "an event-driven backtest can reconstruct pool state at any block").
- **Requirement derivation** — claims that justify a Derived Requirement (e.g., "to prevent future-data leakage, the replay engine must not see blocks > end_block").
- **Spec review** — claims implicit in the existing Requirements.
- **Material changes** — claims whose accuracy may have shifted.

If a claim materially supports a system behavior, correctness, feasibility, acceptance criterion, or Derived Requirement, it is in scope.

## 2. Three States of a Factual Claim

For each load-bearing claim, classify as one of:

- **Verified** — current investigation produced evidence directly addressing the claim.
- **Supported** — previously recorded evidence is reusable; its source, method, date, scope, and applicability can be re-established and still apply.
- **Unverified / Insufficient** — no evidence, or evidence is too old, out of scope, or otherwise inapplicable.

A Verified claim may become Unverified if the new context shifts its scope. A Supported claim can be reused, but re-confirm its source, method, date, scope, and applicability before relying on it.

## 3. Reusing Existing Evidence

Reuse is allowed when:

- The source is identifiable (URL, repo path:line, or other reference).
- The method is recorded (read page, ran command, observed runtime, etc.).
- The verification date is recent enough to be relevant.
- The scope of the original claim still applies to the new context.
- The uncertainty notes still hold (or are still acceptable).

If any of these cannot be established, treat the claim as Unverified.

A Spec can cite an existing intent-layer fact by `INT-NNN#facts-and-research` (file + section) when the underlying evidence is still applicable.

## 4. Primary Sources

For protocol, API, external service, and library claims, prefer **primary sources**:

- Official documentation
- Source code of the library or API
- The repository's own code (for in-repo behavior)
- RFCs and standards

Secondary sources (maintainer blog posts, accepted Stack Overflow answers, conference talks by authors) are acceptable leads but should be verified against primary sources before being recorded as evidence.

Tertiary sources (aggregators, AI-generated content) are leads only. Never record them as the only evidence for a load-bearing claim.

## 5. Documentation vs. Empirical Evidence

Some properties cannot be confirmed from documentation alone. They must be **observed or measured**:

- **Runtime availability** — "the service is up" is not a documentation claim.
- **Data completeness** — "the archive has every block since X" is not a documentation claim.
- **Performance** — "the system runs in < 30s" is not a documentation claim.
- **Reconstruction accuracy** — "the historical reconstruction matches reality" is not a documentation claim.

If a Requirement depends on one of these, do not close it as Verified using documentation alone. Either run the empirical check, or record the verification as an acceptance obligation for the responsible downstream stage (e.g., Module Design, Implementation, or a separate test stage).

## 6. When to Resolve vs. Defer

- **Resolve** — the claim is essential to defining a correct Requirement. Block the affected Requirement until evidence is in hand.
- **Defer** — the claim is not essential to Requirement definition, but the Requirement's correctness depends on the claim holding downstream. Record:
  - The required evidence (what specifically must be true).
  - The acceptance obligation (who must verify, and how).
  - The affected Requirements (so they can be re-checked if the claim later fails).
  - The source of the claim (so a later reader can re-verify).

If deferring without recording the obligation, the Requirement silently relies on an unverified claim — a common source of post-implementation surprises.

## 7. What to Record

For each load-bearing claim that affects a Requirement, record in `# Unknowns and Upstream Feedback` (or the Spec's `## Research` section if present):

```markdown
- **Claim**: <one sentence, the minimum claim>
  **Status**: Verified | Supported | Unverified
  **Source**: <URL or path:line in this repo>
  **Method**: <how verified>
  **Verified on**: <YYYY-MM-DD>
  **Scope**: <what this covers and does not cover>
  **Uncertainty**: <remaining doubt, even after verification>
  **Affects**: <list of Requirement IDs that depend on this claim>
```

If a fact is non-trivial, the full evidence may move to `research/<topic>.md` and the Spec cites it.

## 8. When NOT to Research

- **User preferences and settled business objectives** — research won't change them. The user is the source of truth.
- **Already-verified facts with still-applicable scope** — do not re-research on every change. Re-confirm scope, but don't open a new investigation.
- **Speculative future claims** — "X might change in 6 months". Not actionable now. Note it in Unknowns and revisit when relevant.

The goal is adequate evidence, not exhaustive research. Each verification should be justifiable: "we know this because ..."

## 9. Cross-Skill Reuse

The `intent` skill maintains its own `references/research.md` for fact verification at the Intent layer. Spec-layer verification has the same shape, but its `Affects` field points to Requirements, and its `Source` may include both intent-layer facts and external research.

The two methodologies do not need to be unified. Spec-layer work can cite intent-layer recorded facts by file + section, but does not modify them. New external research done at the Spec layer is recorded in the Spec's own `research/` directory, not in the Intent's.
