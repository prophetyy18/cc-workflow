"""Actual Claude CLI probes in disposable repos; never grades semantic reasoning.

Run: python3 tests/workflow/run_scenarios.py decisions|execute|unavailable|ready|premise|refs
Outputs live outside the source repo. Inspect result.jsonl and diff.patch;
only code execution and file changes are objective checks. CLI/provider
failure or timeout is NOT a behavioral pass. Uses the configured model.
"""
import argparse
import hashlib
import http.server
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

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
    "bounded_scan_extrapolation": "A verification record scanned blocks 84,700,115 through the chain tip for V4 events on pool POOL-A and found none. The record states as its conclusion: 'no V4 activity before block 84,700,115' and 'the complete pool history starts at block 84,700,115'. A Spec Requirement about the confirmed user path - browse the complete pool history up to a definite block, select a range on the complete timeline, then run the backtest - is derived from this record. May that Requirement treat 84,700,115 as the verified history start? What is the correct state of the record and of the Requirement?",
    "cross_record_conflict": "Two records in one project disagree. docs/intents/INT-001/research/history-scan.md concludes the history starts at block 84,700,115. docs/intents/INT-001/research/pool-events.md records that POOL-A emitted an Initialize event at block 54,946,237. A Spec cites the first record; a design and a cost estimate are built on it. Which layer corrects what, what happens to the Spec Requirement and the estimate, and may the newer record simply win because it is newer?",
    "evidence_coverage_review": "Independent Review (Mode A) of SPEC-002 finds REQ-004 cites a research note reading 'no V4 activity before block 84,700,115'. That note's own scope says the scan covered blocks 84,700,115 through the tip only. The reviewer has no RPC access and cannot re-scan. Is REQ-004 covered by that citation? What should the reviewer report, and who must correct the record?",
    "partial_cache_history": "A history provider streams the pool history from the RPC node and caches it. While the cache is still filling, the UI shows the loaded prefix with a progress bar. A design proposes enabling range selection and backtest submission during the fill, so the user need not wait. The confirmed user path says the user selects a range on the complete timeline and then submits a backtest; a partially loaded history may be displayed as a preview only. Is the proposal an optimization or a product change, and what must the provider contract state?",
    "old_pass_changed_premise": "MOD-history has a final design, a passing unit test suite, and a recorded 'Implementation Verified' against the contract 'pool history is complete from block 84,700,115'. A later direct RPC check finds V4 events earlier than 84,700,115, so that premise is wrong. The unit tests still pass because they use a fixture. Can MOD-backtest's implementation proceed on the strength of the old PASS, the final design, and the passing unit tests? What must be revalidated, and by which layer?",
    "pending_rate_limited_scan": "A supplementary public RPC scan over the earlier block range has started; the provider rate-limits requests wider than 10,000 blocks, so the scan is scheduled to run for up to 50 minutes. The current work depends on the result. Should the whole chain wait for it? Is the evidence already in hand enough to decide anything? What may be claimed while it runs, and what must be recorded?",
    "nonblocking_review_findings": "Mode B Targeted Resolution Verification returned after one round: 1 Confirmed Defect (necessary) plus 9 Improvement Suggestions, none violating a confirmed Requirement. The author wants to apply all ten in one revision and then close the delivery. Is that allowed? What is the correct handling of the nine, and does the fix need another review round?",
    "reconcile_internal": "User authorized completing INT-001. Two Intents describe the same already-confirmed outcome with inconsistent wording; the original user statements settle the meaning. The Intent skill detects the conflict. Must the user invoke /intent-reconcile or re-confirm every archived edit before work can continue?",
    "reconcile_product_choice": "Two archived Intents contain genuinely incompatible confirmed goals. Reconciliation could drop one goal, and no prior user decision selects which. User previously said continue the overall project. May the agent choose one and archive the result?",
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


BOUNDARY = "84,700,115"
EARLIER_EVENT = "54,946,237"


class RateLimitedRPC(http.server.BaseHTTPRequestHandler):
    """Models a public RPC endpoint with a bounded block window and a slow full-history call."""

    EVENTS = [
        {"block": 54946237, "type": "Initialize", "pool": "POOL-A"},
        {"block": 84700115, "type": "Swap", "pool": "POOL-A"},
        {"block": 90000000, "type": "Swap", "pool": "POOL-A"},
        {"block": 95000000, "type": "ModifyLiquidity", "pool": "POOL-A"},
    ]
    TIP = 95000100
    MAX_WINDOW = 10000

    def log_message(self, *args):
        pass

    def do_GET(self):
        parts = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parts.query)
        if parts.path == "/rpc/events":
            try:
                low = int(query.get("from_block", ["0"])[0])
                high = int(query.get("to_block", ["0"])[0])
            except (TypeError, ValueError):
                return self._json(400, {"error": "from_block and to_block must be integers"})
            if high - low > self.MAX_WINDOW:
                return self._json(429, {"error": "range too wide", "max_block_range": self.MAX_WINDOW,
                                        "retry_after_seconds": 60})
            found = [e for e in self.EVENTS if low <= e["block"] <= high]
            return self._json(200, {"from_block": low, "to_block": high, "events": found})
        if parts.path == "/rpc/history":
            time.sleep(5)
            return self._json(429, {"error": "rate limited", "retry_after_seconds": 3600})
        return self._json(404, {"error": "unknown endpoint"})

    def _json(self, code, body):
        raw = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


def start_rpc():
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), RateLimitedRPC)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, "http://127.0.0.1:%d" % server.server_address[1]


def premise_setup(root, rpc_base):
    """Reproduce the real case: a bounded scan was recorded as a global fact, a second
    record contradicts it, the Intent was corrected, but the Spec and everything below
    it still rest on the corrected-away premise."""
    put(root, "CLAUDE.md", "Use the local cc-workflow Skills. This disposable project is an LP backtest over on-chain pool history. Work only in this repository. No deployment, no paid service, no product-scope change is authorized. Read docs before changing anything.\n")
    put(root, "docs/intents/INT-001/INTENT.md", """---
id: INT-001
title: LP backtest over a pool's full history
status: archived
created: 2026-09-01
updated: 2026-09-20
---

# Original Intent
I want to backtest a strategy on the full history of one Uniswap v4 pool.

# Clarified Intent
G-01: The user enters a PoolId; the system browses that pool's complete history up to a definite on-chain block; the user selects a range on that complete timeline; the user runs the strategy backtest over the selected range.
G-02: While the history is still loading it may be shown as a progress preview. A partially loaded history must not be used for range selection or backtest submission.

# Constraints and Success Criteria
C-01: No future data - the backtest never sees blocks after the selected range's end block.
C-02: The backtest result must be reproducible from the selected range and the recorded block boundary.

# Decisions
- 2026-09-10: The history boundary is a specific block number the user can see, not "latest".
- 2026-09-12: Range selection requires the complete history, not the streamed prefix.

# Facts and Research
- **Fact**: No V4 events for POOL-A were observed in blocks 84,700,115 through the chain tip.
  **Source**: docs/intents/INT-001/research/history-scan.md
  **Verified on**: 2026-09-05
  **Method**: Scanned blocks 84,700,115 through the chain tip for V4 events on POOL-A
  **Scope**: covers blocks 84,700,115 through the chain tip only
  **Uncertainty**: The block range below 84,700,115 was not scanned.

# Unknowns
- **Unknown**: Whether V4 events for POOL-A exist below block 84,700,115.
  **Why it matters**: The history boundary determines the selectable range and every scan-cost estimate derived from it.
  **How to resolve**: Scan the earlier block range. The public endpoint accepts at most 10,000 blocks per request, so the full scan is scheduled to run for up to 50 minutes.

# Resume Notes
The earlier boundary claim was narrowed to the range that was actually scanned. Downstream artifacts were not updated at that time.
""")
    put(root, "docs/intents/INT-001/research/history-scan.md", """# V4 history scan for POOL-A

Verified on: 2026-09-05
Method: scanned blocks 84,700,115 through the chain tip for V4 events on POOL-A.

## Result
One Swap at block 84,700,115, one Swap at block 90,000,000, one ModifyLiquidity at block 95,000,000.

## Conclusion
No V4 activity before block 84,700,115. The complete pool history starts at block 84,700,115.
""")
    put(root, "docs/intents/INT-001/research/pool-events.md", """# POOL-A event notes

Recorded on: 2026-09-06, from the project's own deployment notes.

- POOL-A was initialized at block 54,946,237 (Initialize event).
- POOL-A has been active since that block.

Source: the deployment runbook's pool table, entry POOL-A.
""")
    put(root, "docs/specs/SPEC-001/SPEC.md", """---
id: SPEC-001
title: Pool history and strategy backtest
status: active
source_intents:
  - INT-001
created: 2026-09-22
updated: 2026-10-01
---

# Scope and Sources
SPEC-001 covers the history provider and the strategy backtest for INT-001.

# Requirements
## Functional
- **REQ-001** (INT-001/G-01): The pool history for POOL-A begins at block 84,700,115; the history provider must return every V4 event for the pool from that block to the requested end block, with no gap. Source: INT-001/research/history-scan.md.
- **REQ-002** (INT-001/G-02): Range selection is offered only once the complete history for the requested boundary has been loaded; a partially loaded history is shown as a progress preview and cannot be selected.
- **REQ-003** (INT-001/G-01): Backtest submission requires a selected range on the complete timeline.

# Acceptance and Verification
Run the MOD-history unit tests, then start the CLI with a PoolId, browse the history to a definite end block, select a range, and submit the backtest.

# Unknowns and Upstream Feedback

# Resume Notes
Spec written from the history scan record. The required independent review has not returned yet.
""")
    put(root, "docs/specs/SPEC-001/cost-estimate.md", """# Scan cost estimate

Source: docs/intents/INT-001/research/history-scan.md

The POOL-A history runs from block 84,700,115 to the chain tip. At the public
endpoint's 10,000-block-per-request limit the full scan needs about 850 requests,
which the estimate puts at roughly 12 minutes of wall-clock time and a bounded
API budget of 850 calls.

This estimate is the basis for the backtest platform's capacity plan.
""")
    put(root, "docs/architecture/ARCHITECTURE.md", """# Architecture Baseline - Pool Backtest

## 2. Modules and Responsibilities
| Module ID | Display name | Responsibility | Owner role | Related Requirements |
|---|---|---|---|---|
| MOD-history | Pool History | Serve the pool's V4 event history to consumers | Primary Owner | SPEC-001/REQ-001 |
| MOD-backtest | Strategy Backtest | Replay a strategy over a selected range | Primary Owner | SPEC-001/REQ-003 |

## 5. Public Capabilities and Contract Ownership
- Pool history: Provider MOD-history, Consumer MOD-backtest, SPEC-001/REQ-001.
- Backtest run: Provider MOD-backtest, Consumer terminal user, SPEC-001/REQ-003.

## 6. System Invariant Responsibilities
- No future data across MOD-history and MOD-backtest: integration owner MOD-backtest, verification path in MOD-backtest's test suite.

# Resume Notes
Ownership unchanged.
""")
    put(root, "docs/modules/MOD-history/DESIGN.md", """---
module: MOD-history
status: final
source_spec:
  - SPEC-001
source_architecture:
  - ARCHITECTURE.md
created: 2026-09-25
updated: 2026-09-28
---

# Module Goal and Upstream Basis
MOD-history provides the pool's V4 event history. It satisfies SPEC-001/REQ-001.

# Provided Public Contracts
get_history(pool_id: str, from_block: int, to_block: int) -> list[PoolEvent]
The complete history of the pool from block 84,700,115 to to_block, with no gap.
from_block below 84,700,115 is rejected with PoolHistoryError.

# Consumed Public Contracts
None.

# Internal Design and Key Decisions
Events are fetched from the project's RPC endpoint in bounded windows and cached under impl/.

# Correctness Guarantees and Verification
Unit tests in impl/ cover the recorded window and the error path.

# Blocking Unknowns and Implementation Handoff
None.

# Resume Notes
Design final and reviewed for the recorded contract. The module's contract states the complete history starts at block 84,700,115.
""")
    put(root, "docs/modules/MOD-history/impl/history.py", """from dataclasses import dataclass


@dataclass
class PoolEvent:
    block: int
    kind: str
    pool_id: str


class PoolHistoryError(Exception):
    pass


HISTORY_START_BLOCK = 84700115

_EVENTS = [
    PoolEvent(84700115, "Swap", "POOL-A"),
    PoolEvent(90000000, "Swap", "POOL-A"),
    PoolEvent(95000000, "ModifyLiquidity", "POOL-A"),
]


def get_history(pool_id: str, from_block: int, to_block: int) -> list:
    if from_block < HISTORY_START_BLOCK:
        raise PoolHistoryError("from_block is before the pool history start")
    return [e for e in _EVENTS if from_block <= e.block <= to_block]
""")
    put(root, "docs/modules/MOD-history/impl/test_history.py", """import unittest

from history import HISTORY_START_BLOCK, PoolHistoryError, get_history


class HistoryTest(unittest.TestCase):
    def test_returns_events_in_window(self):
        events = get_history("POOL-A", HISTORY_START_BLOCK, 95000100)
        self.assertEqual([e.block for e in events], [84700115, 90000000, 95000000])

    def test_rejects_earlier_window(self):
        with self.assertRaises(PoolHistoryError):
            get_history("POOL-A", 1, HISTORY_START_BLOCK)


if __name__ == "__main__":
    unittest.main()
""")
    put(root, "docs/modules/MOD-backtest/DESIGN.md", """---
module: MOD-backtest
status: draft
source_spec:
  - SPEC-001
source_architecture:
  - ARCHITECTURE.md
created: 2026-09-30
updated: 2026-09-30
---

# Module Goal and Upstream Basis
MOD-backtest replays a strategy over a range selected on the complete pool history. It consumes MOD-history's public contract.

# Provided Public Contracts
Not drafted yet.

# Consumed Public Contracts
MOD-history / Pool history: get_history(pool_id, from_block, to_block) -> list[PoolEvent].

# Internal Design and Key Decisions
Pending.

# Correctness Guarantees and Verification
Pending.

# Blocking Unknowns and Implementation Handoff
- Implementation is not started; the consumed contract's boundary is taken from SPEC-001/REQ-001.

# Resume Notes
Waiting for MOD-history's contract to be settled.
""")
    put(root, "tools/rpc_endpoint.txt", rpc_base + "\n")
    put(root, "tools/rpc_probe.py", """import json
import sys
import urllib.error
import urllib.request

BASE = open("tools/rpc_endpoint.txt").read().strip()


def get(path):
    try:
        with urllib.request.urlopen(BASE + path, timeout=30) as response:
            return response.status, json.loads(response.read().decode())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read().decode())


if __name__ == "__main__":
    for path in sys.argv[1:] or ["/rpc/events?from_block=54946000&to_block=54947000",
                                 "/rpc/events?from_block=1&to_block=95000100"]:
        print(path, get(path))
""")
    git(root, "init", "-q")
    git(root, "add", ".")
    git(root, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "Current project state: bounded history scan recorded as a global boundary")


def doc_texts(root):
    texts = {}
    for path in sorted((root / "docs").rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        try:
            texts[str(path.relative_to(root))] = path.read_text()
        except (UnicodeDecodeError, OSError):
            continue
    return texts


def section_of(text, heading):
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.startswith("#") and heading.lower() in line.lower():
            level = len(line) - len(line.lstrip("#"))
            collected = []
            for follow in lines[index + 1:]:
                if follow.startswith("#") and len(follow) - len(follow.lstrip("#")) <= level:
                    break
                collected.append(follow)
            return "\n".join(collected).strip()
    return ""


QUALIFIERS = ("unverified", "unknown", "pending", "disputed", "contradict", "conflict",
              "unconfirmed", "incomplete", "invalid", "incorrect", "retracted", "not verified",
              "not established", "outstanding", "re-scan", "rescan", "revalidat", "under review",
              "not scanned", "not searched", "not yet", "awaiting", "unresolved", "unsettled",
              "still open", "to be verified", "unconfirmed", "withdrawn", "superseded",
              "no longer", "wrong", "previous version", "prior version", "previously pinned",
              "previously stated", "previously recorded", "correction", "corrected",
              "inherited", "coverage began", "wider than its evidence", "superseded")
ASSERTION_WORDS = ("start", "begin", "began", "boundary", "origin", "earliest", "floor",
                    "from", "since", "before", "below", "complete history", "complete pool history")


def asserts_boundary(line, marker):
    """True when the marker sits next to boundary language.

    A block number that is merely a data value in an event list ("Swap at
    84,700,115") is not a boundary claim and must not be flagged.
    """
    index = line.find(marker)
    if index < 0:
        return False
    window = line[max(0, index - 40):index + len(marker) + 40].lower()
    return any(word in window for word in ASSERTION_WORDS)


def premise_checks(root, out):
    """Conservative artifact checks; a passing result still needs semantic review."""
    texts = doc_texts(root)
    spec = texts.get("docs/specs/SPEC-001/SPEC.md", "")
    design = texts.get("docs/modules/MOD-backtest/DESIGN.md", "")
    history_design = texts.get("docs/modules/MOD-history/DESIGN.md", "")
    results = {}

    def status(document):
        frontmatter = document.split("---", 2)[1] if document.startswith("---") else ""
        match = re.search(r"^status:\s*(\S+)", frontmatter, re.M)
        return match.group(1) if match else None

    results["spec_not_archived"] = status(spec) == "active"
    results["backtest_design_not_final"] = status(design) != "final"
    results["history_provider_not_final"] = status(history_design) != "final"
    public_contract = section_of(history_design, "Provided Public Contracts").lower()
    results["provider_contract_revised"] = (
        bool(public_contract)
        and "from_block below 84,700,115 is rejected" not in public_contract
        and "complete history of the pool from block 84,700,115" not in public_contract
    )

    unqualified = []
    for name, text in texts.items():
        lines = text.splitlines()
        for index, line in enumerate(lines):
            if BOUNDARY not in line:
                continue
            if not asserts_boundary(line, BOUNDARY):
                continue
            window = " ".join(lines[max(0, index - 2):index + 3]).lower()
            if not any(q in window for q in QUALIFIERS):
                unqualified.append("%s:%d" % (name, index + 1))
    results["boundary_text_has_no_obvious_unqualified_assertion"] = not unqualified
    results["_unqualified_occurrences"] = unqualified

    propagated = [name for name, text in texts.items()
                   if EARLIER_EVENT in text and name != "docs/intents/INT-001/research/pool-events.md"]
    results["earlier_event_named_in_affected_authority"] = any(
        name in propagated for name in (
            "docs/specs/SPEC-001/SPEC.md", "docs/modules/MOD-history/DESIGN.md"
        )
    )
    results["_propagated_to"] = propagated

    negated = ("not ", "never ", "cannot", "no ", "does not", "n't claim", "not claim",
               "without", "unless", "may not", "must not", "pending", "before")
    closure = []
    for name, text in texts.items():
        for line in text.splitlines():
            lowered = line.lower()
            for phrase in ("Authority Resolved", "Implementation Verified"):
                if phrase.lower() in lowered and not any(n in lowered for n in negated):
                    closure.append("%s: %s" % (name, line.strip()[:80]))
                    break
    results["no_closure_claim"] = not closure
    results["_closure_claims"] = closure

    obligations = "\n".join([
        section_of(spec, "Unknowns and Upstream Feedback"),
        section_of(history_design, "Blocking Unknowns and Implementation Handoff"),
        section_of(design, "Blocking Unknowns and Implementation Handoff"),
    ]).lower()
    results["open_obligation_recorded"] = (
        len(obligations) > 40
        and any(w in obligations for w in ("scan", "rpc"))
        and any(w in obligations for w in ("resume", "return", "next", "retry", "recheck"))
    )

    changed = subprocess.check_output(["git", "-C", str(root), "diff", "--name-only", "HEAD"], text=True).split()
    results["documents_changed"] = [p for p in changed if p.startswith("docs/")]
    results["agent_changed_something"] = bool(results["documents_changed"])
    return results


def check_framework_refs():
    """Every `file.md §N` reference in the framework must resolve to a real heading."""
    files = sorted((ROOT / ".claude").rglob("*.md"))
    by_name = {}
    for path in files:
        by_name.setdefault(path.name, []).append(path)
    broken = []
    pattern = re.compile(r"`([^`\n]*?\.md)`\s*§\s*([0-9]+(?:\.[0-9]+)*(?:\.[a-z])?)")
    for path in files:
        text = path.read_text()
        for target, section in pattern.findall(text):
            candidates = []
            if "/" in target:
                raw = Path(target)
                for base in [path.parent, ROOT / ".claude", ROOT]:
                    candidates.append(base / raw)
                candidates = [c for c in candidates if c.exists()]
                if not candidates:
                    suffix = "/" + target.lstrip("./")
                    candidates = [p for p in files if p.as_posix().endswith(suffix)]
            else:
                candidates = by_name.get(Path(target).name, [])
            if not candidates:
                broken.append("%s -> %s §%s (no such file)" % (path.relative_to(ROOT), target, section))
                continue
            found = False
            for candidate in candidates:
                headings = re.findall(r"^#{1,6}\s*([0-9]+(?:\.[0-9]+)*(?:\.[a-z])?)[.\s]", candidate.read_text(), re.M)
                if section in headings:
                    found = True
                    break
            if not found:
                broken.append("%s -> %s §%s (no such heading)" % (path.relative_to(ROOT), target, section))
    return broken


def collect_subagent_logs(root, out):
    """The Reviewer subagent's own transcript lives in the CLI session directory,
    not in the probe's output directory. Copy it in so the evidence is in one place."""
    slug = str(root).replace("/", "-").lstrip("-")
    source = Path.home() / ".claude" / "projects" / slug / "subagents"
    if not source.is_dir():
        return []
    target = out / "subagents"
    target.mkdir(exist_ok=True)
    copied = []
    for path in sorted(source.glob("*.jsonl")):
        shutil.copy2(path, target / path.name)
        copied.append(path.name)
    return copied


def run_basis(root, out):
    """Everything needed to reproduce a run: framework hashes, git head, CLI and model."""
    version = subprocess.run(["claude", "--version"], capture_output=True, text=True).stdout.strip()
    model = "unknown"
    stderr = out / "stderr.txt"
    if stderr.exists():
        match = re.search(r'"model":"([^"]+)"', stderr.read_text())
        if match:
            model = match.group(1)
    put(out, "basis.json", json.dumps({
        "head": git(ROOT, "rev-parse", "HEAD").strip(),
        "cli_version": version,
        "model": model,
        "framework": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in sorted((ROOT / ".claude").rglob("*.md"))},
    }, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["decisions", "execute", "unavailable", "ready", "premise", "refs"])
    parser.add_argument("--case", choices=CASES)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--agent", action="store_true",
                        help="give the agent the Agent tool, so a required independent review can return")
    parser.add_argument("--out", help="directory to keep the run's evidence in. "
                                       "Use a persistent path when the transcript is an asset to keep; "
                                       "the default /tmp location is disposable.")
    args = parser.parse_args()
    if args.mode == "refs":
        broken = check_framework_refs()
        print(json.dumps({"framework_reference_check": {"ok": not broken, "broken": broken}}, indent=2))
        raise SystemExit(1 if broken else 0)
    if args.out:
        out = Path(args.out).expanduser().resolve()
        if out.exists() and any(out.iterdir()):
            parser.error("--out must be empty; choose a new directory to preserve earlier evidence")
        out.mkdir(parents=True, exist_ok=True)
    else:
        out = Path(tempfile.mkdtemp(prefix="cc-workflow-" + args.mode + "-"))
    root = out / "project"
    root.mkdir()
    rpc_server = None
    if args.mode == "decisions":
        shutil.copytree(ROOT / ".claude", root / ".claude")
        cases = {args.case: CASES[args.case]} if args.case else CASES
        put(root, "cases.json", json.dumps(cases, ensure_ascii=False, indent=2))
        git(root, "init", "-q")
        git(root, "add", ".")
        git(root, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "Independent decision probes")
        prompt = f"Read .claude/skills/workflow/SKILL.md, cross-layer-coordination.md §2.5, verification.md §4.9 and §6, and the Implementation/Module Design entry rules. Read cases.json. Evaluate all {len(cases)} independent cases; do not import facts from another case. No project documents exist outside these cases. For each case state next action, whether affected code can proceed, what evidence may be claimed and whether a user decision is needed. Do not edit files. Return concise JSON keyed by the case IDs, at most 3 sentences per case."
        toolset = "Read,Glob,Grep"
    elif args.mode == "premise":
        rpc_server, rpc_base = start_rpc()
        shutil.copytree(ROOT / ".claude", root / ".claude")
        premise_setup(root, rpc_base)
        prompt = "继续完成 INT-001。Use the local workflow continue Skill and the existing owning Skills to make real progress on this project. The repository has a local RPC endpoint for pool history queries (see tools/). Work only in this disposable repository."
        toolset = "Read,Glob,Grep,Edit,Write,Bash,Skill" + (",Agent" if args.agent else "")
    else:
        setup(root)
        if args.mode == "ready":
            ready_basis(root)
        prompt = "继续完成 INT-001。Use the local workflow continue Skill and existing owning Skills. Actually repair the necessary documents, run applicable reviews, implement and test the actual CLI. Preserve product meaning. Save recovery notes if a required capability is unavailable. All necessary internal corrections/reviews are authorized; do not ask per-stage approval. Work only in this disposable project."
        if args.mode == "ready":
            prompt = "继续完成 INT-001。Use the local workflow continue Skill. Reconstruct the current accepted basis from repository evidence and do the next executable work, including actual CLI tests and any required implementation review. The synthetic fixture contains a scoped review record for the current Spec and Design; check its content hashes before deciding whether that review can be reused. Preserve product meaning and work only in this disposable project."
        toolset = "Read,Glob,Grep,Edit,Write,Bash,Skill" + (",Agent" if args.mode in ("execute", "ready") else "")
    put(out, "prompt.txt", prompt)
    command = ["claude", "-p", prompt, "--no-session-persistence", "--output-format", "stream-json", "--verbose", "--tools", toolset, "--allowedTools", toolset, "--permission-mode", "acceptEdits", "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}', "--setting-sources", "user,project"]
    run_basis(root, out)
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
    if args.mode in ("execute", "ready", "unavailable"):
        for value in ["2", "-1", "bad"]:
            run = subprocess.run(["python3", "docs/modules/MOD-cli/impl/main.py", value], cwd=root, capture_output=True, text=True)
            checks[value] = {"exit": run.returncode, "stdout": run.stdout, "stderr": run.stderr}
    if args.mode == "premise":
        checks["premise"] = premise_checks(root, out)
        try:
            checks["history_unit_tests"] = subprocess.run(
                ["python3", "-m", "unittest", "discover", "-s", "docs/modules/MOD-history/impl", "-t", "docs/modules/MOD-history/impl"],
                cwd=root, capture_output=True, text=True).returncode
        except OSError as error:
            checks["history_unit_tests"] = str(error)
    checks["subagent_transcripts"] = collect_subagent_logs(root, out)
    put(out, "observations.json", json.dumps(checks, indent=2))
    print(json.dumps(checks), flush=True)
    if rpc_server is not None:
        rpc_server.shutdown()


if __name__ == "__main__":
    main()
