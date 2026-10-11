"""REQ-001 fetch coverage (live RPC, env-gated).

Per DESIGN.md Verification § REQ-001: Run on a known V4 pool over a known window;
compare against an independent source (block explorer / Bitquery).
Expected: identical event set within documented RPC limits.

This test is SKIPPED unless env var MOD_001_LIVE_RPC_URL is set AND
MOD_001_TEST_POOL / MOD_001_TEST_START_BLOCK / MOD_001_TEST_END_BLOCK are set.
"""
import os
import unittest

import _helpers


class TestKnownPoolLive(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rpc_url = os.environ.get("MOD_001_LIVE_RPC_URL")
        cls.pool = os.environ.get("MOD_001_TEST_POOL")
        cls.start = os.environ.get("MOD_001_TEST_START_BLOCK")
        cls.end = os.environ.get("MOD_001_TEST_END_BLOCK")
        if not (cls.rpc_url and cls.pool and cls.start and cls.end):
            raise unittest.SkipTest(
                "Live RPC test requires MOD_001_LIVE_RPC_URL, MOD_001_TEST_POOL, "
                "MOD_001_TEST_START_BLOCK, MOD_001_TEST_END_BLOCK env vars."
            )

    def test_live_fetch_returns_non_empty_event_stream(self):
        from ingestion.client import RpcClient
        from ingestion import fetch_event_stream

        rpc = RpcClient(rpc_url=self.rpc_url)
        result = fetch_event_stream(
            self.pool,
            int(self.start),
            int(self.end),
            rpc_client=rpc,
            cache_root="/tmp/mod_001_live_cache",
        )
        # Smoke check — actual coverage assertion requires external comparison source
        # which is documented in DESIGN.md but not bundled in this repo.
        self.assertIsNotNone(result)
        self.assertGreater(len(result.event_stream), 0)


if __name__ == "__main__":
    unittest.main()
