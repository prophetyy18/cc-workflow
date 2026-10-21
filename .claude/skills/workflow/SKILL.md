---
name: workflow
description: Read-only project recovery and cross-layer change-impact status from Git, authoritative artifacts, contracts, code, and verification evidence. Use for /workflow status, "where do we resume?", or "what did this change affect?".
allowed-tools: Read, Glob, Grep, Bash(git*), Bash(rg*)
---

# Workflow Skill

`/workflow status [INT-ID | SPEC-ID | item-ID]` is read-only. Natural-language
requests to resume a project or inspect change impact use the same entry.
It reconstructs state from the repository, not chat history or a stored
dashboard. Do not edit files, run mutating commands, or claim that invoking
the suggested next Skill has happened.

1. Read `CLAUDE.md`, Git branch/HEAD/status, and the authoritative Intent,
   Spec, Architecture, Design, contract, implementation and evidence files.
   Start with the optional target; otherwise find active/recently changed
   goals and open `# Resume Notes`. Inspect staged, unstaged and untracked
   files separately. Never treat an uncommitted change as an adopted handoff.
2. Apply `../../references/change-impact.md` to reconstruct item links and
   compare each candidate with its last reliable adopted version. Read
   `../../references/cross-layer-coordination.md` §2-4 for ownership and
   feedback, and `../../references/verification.md` §4.7-4.8 for evidence
   levels. Use `git diff`, `git log`, `git show`, frontmatter, ID references,
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
5. Choose **one next executable action at the highest necessary owner**,
   followed by the dependent actions in order. Prefer the existing
   `/intent`, `/spec`, `/architecture impact|revise`, `/module-design`, and
   `/implementation` flows. Only an unresolved product decision with
   insufficient authorization goes to the user. This command reports; the
   owning Skill applies fixes and writes Resume Notes.

Output a compact status with Git basis, active goal, changed items, affected
and unaffected paths, evidence validity, blockers, and next command/action.
If no project documents exist, say so and point to the first relevant Intent
action. Never infer completion merely from `archived`, `final`, or a test count.
