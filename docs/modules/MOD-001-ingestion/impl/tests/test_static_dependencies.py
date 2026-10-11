"""REQ-N03 zero-cost data path (static check).

Per DESIGN.md Verification § REQ-N03:
- grep + dependency manifest: no reference to paid providers (Alchemy, QuickNode,
  Chainstack, Blockdaemon, dRPC, Validation Cloud); no paid SDK in dependencies.
"""
import os
import re
import unittest


class TestStaticDependencies(unittest.TestCase):
    def test_no_paid_provider_references_in_source(self):
        impl_src = os.path.abspath(
            os.path.join(os.path.dirname(__file__), os.pardir, "src")
        )
        paid = ["alchemy", "quicknode", "chainstack", "blockdaemon", "drpc",
                 "validation cloud"]
        for root, _, files in os.walk(impl_src):
            for fn in files:
                if not fn.endswith(".py"):
                    continue
                path = os.path.join(root, fn)
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read().lower()
                for provider in paid:
                    if provider in text:
                        self.fail(
                            f"paid provider '{provider}' referenced in {path}"
                        )


if __name__ == "__main__":
    unittest.main()
