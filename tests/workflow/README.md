# Workflow behavior probes

Run `python3 tests/workflow/run_scenarios.py decisions`, `execute`, `ready`,
`unavailable`, `premise`, or `refs` from this repository with an
authenticated Claude CLI. The script copies the current `.claude`
framework into a disposable Git repository under
`/tmp/cc-workflow-<mode>-*`; it never edits a consumer project. Each
output directory contains the prompt, framework hashes, streamed agent
trace, Git diff, and objective CLI observations.

`decisions` asks a fresh agent to route nineteen independent cases,
including blocked and allowed transitions. Its answer needs human
semantic review; the script does not grade reasoning by keyword.
`execute` starts with a corrected but unreviewed Spec, stale final
Design and stale code. `ready` starts with the current Spec and Design
accepted but stale code; it includes the Agent tool for required review.
`unavailable` removes the Agent tool so
required independent review cannot return. The latter should preserve
the affected handoff as open.

`premise` reproduces the real incident that motivated the evidence
rules: a bounded block scan was recorded as a global "complete history
starts at block N" fact, a second record in the same project contradicts
it, the Intent was corrected, but the Spec, the design, the cost
estimate and the passing unit tests still rest on the corrected-away
premise. A local rate-limited RPC endpoint backs the fixture: a narrow
window returns real events (including one below the recorded boundary),
a wide window is rejected, and the full-history call is throttled. The
mode's checks are conservative artifact guards: they check frontmatter,
known Provider contract text, propagation into an affected authority,
open obligations and actual edits. They cannot decide arbitrary semantic
correctness. A passing guard still needs review of the contract, trace,
review result and runtime evidence. The fixtures do not establish a
consumer project's real user path.

`refs` is a deterministic static check: every `file.md §N` reference
inside the framework must resolve to a real heading. It needs no CLI
and is the guard against dangling cross-references after a rule edit.

`--agent` additionally gives the agent the Agent tool, so a required
independent review can actually return. `premise --agent` is the run
that exercises the review-returning path; without it the agent must
report the reviewer as unavailable and keep the review open.

Every run builds its project in a fresh `/tmp/cc-workflow-<mode>-*`
directory and never touches this repository or any consumer project.
The output directory is kept after the run because the agent trace,
the diff, and the observations are the evidence a reviewer reads.

**The transcript is an asset, not scratch.** `result.jsonl` is the
input to `analyze_context.py`; the `diff.patch` is the only record of
what the agent actually wrote. The default `/tmp` location is
disposable and will eventually be cleared. When the transcript matters
— when analysing framework bloat, or when a run has to be defended —
pass `--out <dir>` to keep it somewhere durable:

    python3 tests/workflow/run_scenarios.py premise --agent --out ~/cc-workflow-probes/premise-2026-10-22

The directory is then yours to keep or archive. The runner refuses a
nonempty `--out` directory so an earlier trace is not overwritten.
Nothing else writes to it, and the run never touches this repository.

Run the small deterministic counterexample tests with
`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/workflow -p 'test_*.py'`.
They guard the probe tooling, not Agent behavior.

These are actual agent runs on a synthetic project. A completed process,
mock, static rule check, or a test timeout is not by itself proof that a
consumer project's real user path works. Inspect `observations.json`,
`diff.patch`, and the final agent result together. A timeout or CLI
failure is recorded as such, never counted as a pass.
