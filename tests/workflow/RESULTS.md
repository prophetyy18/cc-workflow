# Workflow verification record

The probes use disposable synthetic repositories. They cannot establish that
a consumer project's service or browser path works. Read each run's
`basis.json`, `result.jsonl`, `diff.patch` and `observations.json` together;
the framework hashes and process outcome determine what a run can support.

## Current checks

| Check | Scope and result |
|---|---|
| `python3 tests/workflow/run_scenarios.py refs` | Static reference integrity: passed; no missing numbered headings. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/workflow -p 'test_*.py'` | Four deterministic tool counterexamples passed: a qualifier in unrelated text cannot release an old Provider contract; a missing lettered section is reported; a Skill result is not counted as Agent reasoning; an existing output trace is preserved. These do not test Agent behavior. |
| `git diff --check` and Python syntax parsing | Passed for this framework edit; neither proves semantic correctness. |

Focused Agent decision probes ran in disposable repositories. Their
`basis.json` files capture the exact framework snapshot for each run:

| Case | Observed result | Trace |
|---|---|---|
| `authorized_correction` | Agent chose Design correction and required review under existing authorization; affected code waits, unrelated work can continue. | `/home/lpdev/cc-workflow-probes/2026-10-22/cc-workflow-redesign-authorized-20261022/` |
| `reconcile_internal` | Agent entered reconcile itself for a confirmed, internally consistent meaning and kept the original return point; no repeated user approval. | `/home/lpdev/cc-workflow-probes/2026-10-22/cc-workflow-redesign-reconcile_internal-20261022/` |
| `reconcile_product_choice` | Agent kept incompatible confirmed goals open and requested a real product choice. | `/home/lpdev/cc-workflow-probes/2026-10-22/cc-workflow-redesign-final-reconcile_product_choice-20261022/` |
| `product_order` | Agent preserved the confirmed order, deferred an optional shortcut and classified implementation difficulty as an engineering estimate rather than an Intent constraint. This was rerun after correcting a misclassification in the preceding trace. | `/home/lpdev/cc-workflow-probes/2026-10-22/cc-workflow-redesign-verified-product_order-20261022/` |
| `unrelated_edit` | Agent kept an unchanged Requirement, Design and Review applicable despite an unrelated Spec edit, and released that implementation. | `/home/lpdev/cc-workflow-probes/2026-10-22/decision-unrelated_edit/` |
| `performance_obligation` | Agent released Implementation on a reviewed final Design while leaving complete-path latency measurement open; it did not claim the bound met. | `/home/lpdev/cc-workflow-probes/2026-10-22/decision-performance_obligation/` |

These are Agent **decisions**, not edits to a real project or user-path
acceptance. A single combined run of all nineteen cases hit its 240-second
limit without a final answer (`timeout_no_pass`); its trace is preserved at
`/home/lpdev/cc-workflow-probes/2026-10-22/cc-workflow-redesign-decisions-20261022/`.

The first executable `ready` run used the old harness configuration without
the Agent tool. It changed the synthetic CLI's `x+2` implementation to `x+1`,
ran seven local unit tests successfully, and the runner's direct CLI probes
observed `2 → 3`, `-1 → 0`, and a nonzero error for invalid input. It timed out
at 240 seconds without a returned independent review or final handoff:
`/home/lpdev/cc-workflow-probes/2026-10-22/ready-current/`. This is code and
local-test progress, not delivery closure. The harness now gives `ready` the
Agent tool; `unavailable` alone exercises missing-review behavior.

The corrected `ready` run likewise fixed the synthetic CLI and produced eight
passing local tests. Direct CLI probes observed `2 → 3`, `-1 → 0`, and the
specified invalid-input error. The Agent launched the Independent Reviewer,
but only an asynchronous launch receipt returned before the 360-second limit;
no review report or closed handoff was observed. Outcome:
`timeout_no_pass`, trace at
`/home/lpdev/cc-workflow-probes/2026-10-22/ready-with-review/`. The review
brief requested several domain sections irrelevant to this small CLI; the
delegation rule now says to name applicable sections only. That last rule
edit has **not** been behavior-tested in a subsequent Reviewer run.

## Earlier probes and limits

Earlier versions ran seventeen Agent decision cases and several executable
synthetic project scenarios. The decision cases were reported as passing, but
their original `/tmp/cc-workflow-*` transcripts are no longer present, so
their exact answers and framework basis cannot now be independently checked.
Do not treat them as regression results for this revision. The previous
whole-goal and bounded RPC scenarios timed out before full delivery; some
showed useful upstream correction and local tests, but no completed real
user-path acceptance. A remaining review or unverified runtime transition
was still open. Run `decisions`, `execute`, `ready`, `unavailable` or `premise`
again against the current framework when that behavior needs evidence.

The surviving counterexample record was copied to
`/home/lpdev/cc-workflow-probes/2026-10-22/cc-framework-review-6e_rzyf8/`.
Use `--out` in a durable directory for future traces; the runner refuses to
overwrite a nonempty destination.

Behavior still needing a later full Agent run: closing a required independent
review, returning from upstream correction into Design and Implementation,
and accepting the complete user path under real operating conditions. A
timeout, mock, static text check or locally passing unit test is not that
acceptance.
