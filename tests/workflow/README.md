# Workflow behavior probes

Run `python3 tests/workflow/run_scenarios.py decisions`, `execute`, `ready`,
or `unavailable` from this repository with an authenticated Claude CLI.
The script copies the current `.claude` framework into a disposable Git
repository under `/tmp/cc-workflow-<mode>-*`; it never edits a consumer
project. Each output directory contains the prompt, framework hashes,
streamed agent trace, Git diff, and objective CLI observations.

`decisions` asks a fresh agent to route ten independent cases, including
blocked and allowed transitions. Its answer needs human semantic review;
the script does not grade reasoning by keyword. `execute` starts with a
corrected but unreviewed Spec, stale final Design and stale code. `ready`
starts with the current Spec and Design accepted but stale code.
`unavailable` removes the Agent tool so required independent review cannot
return. The latter should preserve the affected handoff as open.

These are actual agent runs on a synthetic CLI project. A completed process,
mock, static rule check, or a test timeout is not by itself proof that a
consumer project's real user path works. Inspect `observations.json`,
`diff.patch`, and the final agent result together. A timeout or CLI failure
is recorded as such, never counted as a pass.
