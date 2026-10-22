# Validation record

Scope: disposable integer CLI repositories created by `run_scenarios.py`.
These runs do not exercise `test-workflow` or its browser/service.

| Run | Observed result | Evidence |
|---|---|---|
| Ten independent decision cases | Agent completed all ten. Nine judgments were consistent with the expected prerequisite/evidence boundary. In `authorized_correction` it ambiguously answered that code could proceed before Design review. | `/tmp/cc-workflow-decisions-weohd_h2/result.jsonl` |
| Focused `authorized_correction` after rule fix | Agent explicitly said affected code cannot proceed until contract revision and required review, with no extra user approval needed. | `/tmp/cc-workflow-decisions-5vb3jue8/result.jsonl` |
| Whole-goal recovery with corrected, active Spec and stale Design/code | Agent reconstructed the impact chain and launched a scoped Independent Reviewer before changing downstream code. Reviewer did not return within 600 seconds. Spec remained active, code still printed `x+2`; result is `timeout_no_pass`. | `/tmp/cc-workflow-execute-r_18kbgl/observations.json`, `result.jsonl`, `diff.patch` |
| Ready Spec/Design, stale code | Agent changed code to `x+1` and ran 10 real CLI subprocess tests; wrong `+2` mutants failed the negative control. Direct CLI probes returned `2→3`, `-1→0`, and a nonzero invalid-input error. The 300-second run timed out before a final implementation review/handoff, so only code/local real CLI evidence is established. | `/tmp/cc-workflow-ready-1xmprrtc/observations.json`, `result.jsonl`, `diff.patch` |
| Agent tool removed | Run timed out after 240 seconds without a returned independent review or code changes. It does not demonstrate successful bounded recovery. The resulting rule now forbids searching outside the project or launching a nested CLI as a substitute. | `/tmp/cc-workflow-unavailable-7682rs_r/observations.json`, `result.jsonl` |

Static checks: `git diff --check`, Python compilation of the runner, and
`quick_validate.py` for the five changed Skills passed. The Architecture
Skill's pre-existing frontmatter description contained angle brackets and
was normalized to pass the validator. These checks do not establish agent
behavior or real-path acceptance.

Behavior still requiring a later end-to-end run: return from an actual
independent review, completion of the upstream correction, automatic
resumption through Design and Implementation, and final handoff with
applicable runtime evidence. A tool or process timeout is never a PASS.
