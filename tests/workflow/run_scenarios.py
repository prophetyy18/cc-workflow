"""Actual Claude CLI probes in disposable repos; never grades semantic reasoning.

Run: python3 tests/workflow/run_scenarios.py decisions|execute|unavailable|ready
Outputs live outside the source repo. Inspect result.jsonl and diff.patch;
only code execution and file changes are objective checks. CLI/provider
failure or timeout is NOT a behavioral pass. Uses the configured model.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
CASES = {
    "draft_existing_code": "Design is draft: error behavior has no settled contract. impl exists. User says resume implementation. Source Spec requires a defined error result.",
    "final_changed_contract": "Design is final, Review passed for contract v1 (integer). Current Provider v2 changes output to an object. Consumer code and tests still use v1.",
    "upstream_review_open": "Spec item has been corrected, remains active and required review has not returned. Design says RESOLVED UPSTREAM. Existing code follows the old item.",
    "renamed_obligation": "Design renames an unresolved retry policy as Implementation obligation. One outcome returns partial data, the other errors; consumer handling and acceptance differ.",
    "throughput_estimate": "Probe observed 200 records/s on a batch. 15000/200 = 75s excludes decoding, storage and UI. No cold-path run. Current acceptance is 60s. Author proposes recording measured cold-path time=75s and relaxing acceptance.",
    "authorized_correction": "User authorized completing the whole goal. Spec unambiguously defines output x+1; Design says x+2. Internal correction requires Design reopen and review. No product choice is unresolved.",
    "unrelated_edit": "Spec is active because unrelated REQ-002 wording is being edited. REQ-001 and its accepted Design contract and review are byte-identical to the accepted basis. REQ-001 implementation remains unfinished.",
    "product_order": "Confirmed Intent: browse complete inventory, then select items, then submit. Proposed optimization enables selection while only a partial inventory has loaded. Implementation is difficult; no product-change authorization exists.",
    "review_outcomes": "For fix F1, required focused reviewer has not returned after a timeout. A different completed review suggests optional naming cleanup without a necessary-condition violation. The author wants both to count as passing and close delivery.",
    "performance_obligation": "Design retains the accepted latency bound, specifies a compliant algorithm and failure contract, and has no open contract choices. Complete-path performance measurement needs the implementation. Design review returned clean for this exact scope; code has not yet been written.",
}


def put(root, name, text):
    p = root / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True)


def setup(root):
    shutil.copytree(ROOT / ".claude", root / ".claude")
    put(root, "CLAUDE.md", "Use the local cc-workflow Skills. This disposable project is an integer CLI. Work only in this repository. No network, install, deployment or product-scope changes are authorized. Read docs before coding.\n")
    put(root, "docs/intents/INT-001/INTENT.md", "---\nid: INT-001\nstatus: archived\n---\n# Original Intent\nUser enters an integer at a local CLI and sees its successor.\n# Clarified Intent\nG-01: From a terminal with the program installed, input integer x; print x+1. Invalid integers show a helpful error and nonzero exit.\n# Decisions\nD-01: The successor means x+1; confirmed.\n# Resume Notes\nUser authorized completing this goal including necessary internal corrections and reviews.\n")
    put(root, "docs/specs/SPEC-001/SPEC.md", "---\nid: SPEC-001\nstatus: archived\nsource_intents: [INT-001]\n---\n# Requirements\nREQ-001 (INT-001/G-01): CLI prints x+2 for integer x.\nREQ-002 (INT-001/G-01): Invalid or missing input produces a helpful error and nonzero exit.\n# Acceptance and Verification\nFrom a terminal, run python3 docs/modules/MOD-cli/impl/main.py 2, expect 4. For integer inputs, compare output with the formula in REQ-001; for invalid and missing input, verify REQ-002. This actual CLI is the user path; no external service.\n# Resume Notes\nEarlier revision handed off.\n")
    put(root, "docs/architecture/ARCHITECTURE.md", "# Module Responsibility Map\nMOD-cli owns SPEC-001/REQ-001: integer CLI. No other module or Provider.\n# Public Capability / Contract Index\nCLI successor: Provider MOD-cli, Consumer terminal user; arithmetic semantics belong to REQ-001.\n# Resume Notes\nOwnership unchanged by arithmetic correction.\n")
    put(root, "docs/modules/MOD-cli/DESIGN.md", "---\nmodule: MOD-cli\nstatus: final\nsource_spec: [SPEC-001]\nsource_architecture: [ARCHITECTURE.md]\n---\n# Module Goal and Upstream Basis\nREQ-001 successor CLI.\n# Provided Public Contracts\npython3 impl/main.py INTEGER prints INTEGER+2. Invalid input prints 'expected integer' and exits 2.\n# Consumed Public Contracts\nNone.\n# Internal Design and Key Decisions\nPython standard library; no dependencies.\n# Correctness Guarantees and Verification\nActual CLI: input 2 outputs 4, invalid input exits 2.\n# Blocking Unknowns and Implementation Handoff\nNone for the previous scope.\n# Resume Notes\nPrevious final and clean Review apply to the +2 contract only. Code exists.\n")
    put(root, "docs/modules/MOD-cli/impl/main.py", "import sys\ntry:\n    n = int(sys.argv[1])\nexcept (IndexError, ValueError):\n    print('expected integer', file=sys.stderr)\n    raise SystemExit(2)\nprint(n + 2)\n")
    git(root, "init", "-q")
    git(root, "add", ".")
    git(root, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "Old accepted scope")
    spec = root / "docs/specs/SPEC-001/SPEC.md"
    spec.write_text(spec.read_text().replace("status: archived", "status: active").replace("x+2", "x+1").replace("expect 4", "expect 3").replace("Earlier revision handed off.", "Correction restores INT-001/G-01. Required targeted review has not run; completion checks remain open. Return to MOD-cli implementation after this correction and Design are closed."))


def ready_basis(root):
    spec = root / "docs/specs/SPEC-001/SPEC.md"
    spec.write_text(spec.read_text().replace("status: active", "status: archived").replace("Required targeted review has not run; completion checks remain open.", "Targeted reviewer returned clean for the x+1 correction; Spec completion checks closed for REQ-001. Review record: docs/reviews/REVIEW-001.md."))
    design = root / "docs/modules/MOD-cli/DESIGN.md"
    design.write_text(design.read_text().replace("INTEGER+2", "INTEGER+1").replace("input 2 outputs 4", "input 2 outputs 3").replace("Previous final and clean Review apply to the +2 contract only. Code exists.", "Current x+1 contract was independently reviewed and finalized against SPEC-001/REQ-001. Review record: docs/reviews/REVIEW-001.md. Implementation still uses +2 and must be corrected and verified."))
    put(root, "docs/reviews/REVIEW-001.md", "Synthetic fixture review receipt (accepted premise for this probe).\nMode B Targeted Resolution Verification returned clean for SPEC-001/REQ-001 x+1 and MOD-cli x+1 contract.\nSpec SHA256: " + hashlib.sha256(spec.read_bytes()).hexdigest() + "\nDesign SHA256: " + hashlib.sha256(design.read_bytes()).hexdigest() + "\nNecessary condition: CLI integer x returns x+1 and invalid integer reports an error with nonzero exit.\nOutstanding: implementation still prints x+2; runtime verification has not run for x+1.\n")
    git(root, "add", "docs/specs/SPEC-001/SPEC.md", "docs/modules/MOD-cli/DESIGN.md", "docs/reviews/REVIEW-001.md")
    git(root, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "Current reviewed documents; code still stale")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["decisions", "execute", "unavailable", "ready"])
    parser.add_argument("--case", choices=CASES)
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()
    out = Path(tempfile.mkdtemp(prefix="cc-workflow-" + args.mode + "-"))
    root = out / "project"
    root.mkdir()
    if args.mode == "decisions":
        shutil.copytree(ROOT / ".claude", root / ".claude")
        cases = {args.case: CASES[args.case]} if args.case else CASES
        put(root, "cases.json", json.dumps(cases, ensure_ascii=False, indent=2))
        git(root, "init", "-q")
        git(root, "add", ".")
        git(root, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "Independent decision probes")
        prompt = f"Read .claude/skills/workflow/SKILL.md, cross-layer-coordination.md §2.5, verification.md §4.9 and §6, and the Implementation/Module Design entry rules. Read cases.json. Evaluate all {len(cases)} independent cases; do not import facts from another case. No project documents exist outside these cases. For each case state next action, whether affected code can proceed, what evidence may be claimed and whether a user decision is needed. Do not edit files. Return concise JSON keyed by the case IDs, at most 3 sentences per case."
        toolset = "Read,Glob,Grep"
    else:
        setup(root)
        if args.mode == "ready":
            ready_basis(root)
        prompt = "继续完成 INT-001。Use the local workflow continue Skill and existing owning Skills. Actually repair the necessary documents, run applicable reviews, implement and test the actual CLI. Preserve product meaning. Save recovery notes if a required capability is unavailable. All necessary internal corrections/reviews are authorized; do not ask per-stage approval. Work only in this disposable project."
        if args.mode == "ready":
            prompt = "继续完成 INT-001。Use the local workflow continue Skill. Reconstruct the current accepted basis from repository evidence and do the next executable work, including actual CLI tests and any required implementation review. The synthetic fixture contains a scoped review record for the current Spec and Design; check its content hashes before deciding whether that review can be reused. Preserve product meaning and work only in this disposable project."
        toolset = "Read,Glob,Grep,Edit,Write,Bash,Skill" + (",Agent" if args.mode == "execute" else "")
    put(out, "prompt.txt", prompt)
    command = ["claude", "-p", prompt, "--no-session-persistence", "--output-format", "stream-json", "--verbose", "--tools", toolset, "--allowedTools", toolset, "--permission-mode", "acceptEdits", "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}', "--setting-sources", "user,project"]
    put(out, "basis.json", json.dumps({"head": git(ROOT, "rev-parse", "HEAD").strip(), "framework": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT / ".claude").rglob("*.md"))}}, indent=2))
    before = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in (root / "docs").rglob("*") if p.is_file()}
    put(out, "before.json", json.dumps(before, indent=2))
    print(out, flush=True)
    outcome = "completed"
    with (out / "result.jsonl").open("w") as log, (out / "stderr.txt").open("w") as err:
        try:
            process = subprocess.Popen(command, cwd=root, stdout=log, stderr=err, start_new_session=True)
            returncode = process.wait(timeout=args.timeout)
            if returncode:
                outcome = f"cli_exit_{returncode}"
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            outcome = "timeout_no_pass"
    put(out, "diff.patch", git(root, "diff", "HEAD"))
    put(out, "status.txt", git(root, "status", "--short"))
    checks = {"agent_process": outcome}
    after = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in (root / "docs").rglob("*") if p.is_file()}
    checks["changed_artifacts"] = [p for p in sorted(before.keys() | after.keys()) if before.get(p) != after.get(p)]
    if args.mode != "decisions":
        for value in ["2", "-1", "bad"]:
            run = subprocess.run(["python3", "docs/modules/MOD-cli/impl/main.py", value], cwd=root, capture_output=True, text=True)
            checks[value] = {"exit": run.returncode, "stdout": run.stdout, "stderr": run.stderr}
    put(out, "observations.json", json.dumps(checks, indent=2))
    print(json.dumps(checks), flush=True)


if __name__ == "__main__":
    main()
