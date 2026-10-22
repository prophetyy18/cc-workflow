---
name: workflow
description: Recover project state and continue an authorized user goal through existing Skills. Use /workflow status for read-only progress or impact inspection; /workflow continue or "continue completing INT-NNN" to execute the next ready work and resolve necessary cross-layer blockers.
---

# Workflow Skill

| Entry | Behavior |
|---|---|
| `/workflow status [ID]`, "where are we?", "what changed?" | Read-only recovery; no edits, tests with side effects, or automatic next Skill execution. |
| `/workflow continue <ID>`, "继续完成 INT-NNN" | Recover, then execute the authorized goal through the existing owning Skills. |

Both modes reconstruct state from the repository. `continue` exists because
a status report cannot itself authorize execution; it uses the same recovery
and prerequisite checks rather than introducing another lifecycle or agent.

1. Read `CLAUDE.md`, Git branch/HEAD/status, and the authoritative Intent,
   Spec, Architecture, Design, contract, implementation and evidence files.
   Follow the relevant chain; load an owning Skill's details when its work
   is selected, not every Skill before the first executable action.
   Start with the optional target; otherwise find active/recently changed
   goals and open `# Resume Notes`. Inspect staged, unstaged and untracked
   files separately. Inspect relevant changes; dirty files alone neither
   prove handoff completion nor prohibit unrelated work.
2. Apply `../../references/change-impact.md` to reconstruct item links and
   compare each candidate with its last reliable adopted version. Read
   `../../references/cross-layer-coordination.md` §2-4 for ownership and
   feedback, and `../../references/verification.md` §4.7-4.8 for evidence
   levels. Check the load-bearing premises each candidate rests on: a
   cited fact whose recorded coverage no longer spans the scope it is
   used for, or that an applicable record contradicts, needs scoped impact
   analysis (`../spec/references/fact-verification.md` §2.1). Use `git diff`,
   `git log`, `git show`, frontmatter, ID references,
   contract consumers and actual tests. If the old version or a reverse link
   is missing, report uncertainty and the smallest investigation needed.
3. For each affected chain, report the changed item, propagation path,
   `modify` / `revalidate only` / `unaffected` / `unknown — investigate`,
   owner, specific evidence and next action. Show why a nearby module is
   unaffected only when its ownership and contract use support that claim.
   Terminate propagation at an evidenced unchanged boundary.
4. Report separately: current document/contract closure; code and local-test
   coverage; real user-path evidence. State the version and scope of each
   old PASS/final/real run, or say scope unknown. A working-tree edit, mock,
   skipped test, or status field alone cannot close the user path.
5. Select the next work that can close with concrete evidence. State its
   result sought, source items/versions, closure evidence, blocker owner
   and return point in a few lines. Apply cross-layer §2.5.c before naming
   it executable. Use existing `/intent`, `/spec`, `/architecture`,
   `/module-design` and `/implementation` operations. If a prerequisite
   is open, select the owner's corrective work instead of dependent code.

Output a compact status with Git basis, active goal, changed items, affected
and unaffected paths, evidence validity, blockers, and next command/action.
If no project documents exist, say so and point to the first relevant Intent
action. Never infer completion merely from `archived`, `final`, or a test count.

For `status`, stop after the report. For `continue`:

1. Preserve the user's confirmed meaning and operation order. Broad task
   authorization covers necessary internal corrections and their reviews,
   not a weaker goal, bypassed prerequisite, deployment permission or a new
   product trade-off. Apply cross-layer §2.5.b rather than asking per stage.
   Investigate compliant approaches first. An optional shortcut is not a
   required user decision while the confirmed path remains executable.
2. Execute the selected work using its owning Skill. If Skill invocation is
   unavailable but its file and tools are accessible, read and follow it in
   the Main Agent; do not make the user dispatch commands. Report a genuinely
   unavailable capability accurately. A single work may span Skills; separate
   ready modules need not wait for every design in the project. For required
   independent review, use the project's Reviewer through the Agent tool;
   if it cannot return, follow verification §6.3.a. Do not search outside
   the project for similarly named skills or start a nested CLI as a substitute.
   When the selected scope's prerequisites are closed, begin its work;
   check the next required reviewer at its verification gate, not as a
   speculative preflight before any implementation change.
3. On a blocker, record the interrupted work and return point in its existing
   Resume Notes, resolve the smallest necessary upstream scope, and reread
   actual artifacts with §2.5.c before returning. Preserve existing draft
   code; it is not permission to continue affected implementation early.
4. Close with the selected evidence, record its applicable basis and next
   action, then select and execute the next ready work automatically. Repeat
   until the authorized goal is verified or remaining work requires a genuine
   user decision, unavailable environment/capability, or the bounded diagnostic
   stop in verification §6. Continue unaffected work when useful. Save the
   exact recovery position; never turn missing review or runtime evidence
   into a completion claim.
