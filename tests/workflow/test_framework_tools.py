"""Small counterexamples for the framework probe tools (no agent service needed)."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runner = load("workflow_probe", "run_scenarios.py")
analyzer = load("workflow_analysis", "analyze_context.py")


class ProbeChecks(unittest.TestCase):
    def test_unrelated_qualifier_cannot_release_old_provider_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "project"
            root.mkdir()
            runner.premise_setup(root, "http://127.0.0.1:1")
            for path in (root / "docs").rglob("*.md"):
                lines = path.read_text().splitlines()
                path.write_text("\n".join(
                    ("Unrelated correction pending.\n" + line)
                    if runner.BOUNDARY in line else line for line in lines
                ) + "\n")
            checks = runner.premise_checks(root, Path(temp))
            self.assertFalse(checks["history_provider_not_final"])
            self.assertFalse(checks["provider_contract_revised"])

            provider = root / "docs/modules/MOD-history/DESIGN.md"
            provider.write_text(provider.read_text().replace("status: final", "status: draft")
                                .replace("from_block below 84,700,115 is rejected",
                                         "Missing early history remains an open contract question")
                                .replace("The complete history of the pool from block 84,700,115 to to_block, with no gap.",
                                         "Completeness cannot be claimed until the earlier range is checked."))
            checks = runner.premise_checks(root, Path(temp))
            self.assertTrue(checks["history_provider_not_final"])
            self.assertTrue(checks["provider_contract_revised"])

    def test_missing_lettered_section_is_reported(self):
        with tempfile.TemporaryDirectory() as temp:
            framework = Path(temp) / ".claude"
            framework.mkdir()
            (framework / "target.md").write_text("### 2.5 Existing heading\n")
            (framework / "source.md").write_text("See `target.md` §2.5.z\n")
            old_root = runner.ROOT
            try:
                runner.ROOT = Path(temp)
                self.assertTrue(runner.check_framework_refs())
            finally:
                runner.ROOT = old_root

    def test_skill_result_is_not_agent_reasoning(self):
        with tempfile.TemporaryDirectory() as temp:
            trace = Path(temp) / "trace.jsonl"
            trace.write_text("\n".join(json.dumps(row) for row in [
                {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "s1", "name": "Skill", "input": {"skill": "workflow"}}]}},
                {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "s1", "content": "INJECTED_RULE_TEXT verification.md §6"}]}},
            ]))
            reasoning, reads = analyzer.load(trace)
            self.assertNotIn("INJECTED_RULE_TEXT", "\n".join(reasoning))
            self.assertTrue(reads)

    def test_existing_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "saved"
            destination.mkdir()
            marker = destination / "result.jsonl"
            marker.write_text("original evidence")
            result = subprocess.run(
                [sys.executable, str(HERE / "run_scenarios.py"), "decisions", "--out", str(destination)],
                capture_output=True, text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(marker.read_text(), "original evidence")


if __name__ == "__main__":
    unittest.main()
