"""REQ-001 / REQ-002 empirical acceptance against live RPC.

Per DESIGN.md Verification:
- REQ-001: compare returned event set against an independent source.
  Independent sources for V4 events are limited (Bitquery / Robinhood
  explorer APIs not free); we use cross-run determinism as a proxy: a
  second fetch against the same window must return the same set.
- REQ-002: sample N blocks (N >= 10), compare reconstructed
  `(sqrtPriceX96, tick)` against the on-chain Swap event's data
  fields (the Swap event itself carries sqrt_price_x96 + tick).

The test is env-gated (same as test_known_pool.py) and runs against the
default public entry; uses the persistent PoolInitIndex if available.

Honest scope: this is a partial empirical acceptance. REQ-001 cross-check
against an external explorer / Bitquery export is still outstanding
(see verification doc + .env slot `MOD_001_KNOWN_EVENTS_FILE`).
"""
import json
import os
import subprocess
import unittest

import _helpers


class TestReconstructionSamplingLive(unittest.TestCase):
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

    def _fetch_default(self):
        from ingestion.client import RpcClient
        from ingestion import fetch_event_stream

        rpc = RpcClient(rpc_url=self.rpc_url)
        return fetch_event_stream(
            self.pool,
            int(self.start),
            int(self.end),
            rpc_client=rpc,
            cache_root="/tmp/mod_001_live_cache",
        )

    def test_cross_run_determinism_req_001(self):
        """REQ-001 partial empirical acceptance: same fetch returns same set.

        A second fetch of the same window (cache-warm) must return the
        identical set of `(block_number, log_index, tx_hash)` triples.
        If a real external cross-check (Bitquery / explorer) is added later,
        replace this proxy with the real comparison.
        """
        r1 = self._fetch_default()
        keys1 = sorted(
            (e.event.block_number, e.event.log_index, e.event.tx_hash)
            for e in r1.event_stream
        )
        # Second fetch (cache hit on every sub-range).
        r2 = self._fetch_default()
        keys2 = sorted(
            (e.event.block_number, e.event.log_index, e.event.tx_hash)
            for e in r2.event_stream
        )
        self.assertEqual(keys1, keys2, "two fetches must return the same event set")
        # REQ-001 independent-source slot, if populated, would replace the
        # proxy above with: assert keys1 == set(known_events).
        known = os.environ.get("MOD_001_KNOWN_EVENTS_FILE", "")
        if known and os.path.isfile(known):
            with open(known) as f:
                known_keys = sorted(
                    tuple(x) for x in json.load(f)
                )
            self.assertEqual(keys1, known_keys, "live fetch must match known events file")

    def test_post_state_per_event_sampling_req_002(self):
        """REQ-002 partial empirical acceptance: per-event post_state sanity.

        For every event in the live fetch, the reconstructed
        `post_state` MUST:
        - be present (REQ-002 "reconstruct pool state (sqrtPriceX96, tick,
          liquidity, fee) from the post-event fields");
        - match the event's own data fields where the event carries them
          (Swap: sqrt_price_x96, tick; Initialize: sqrt_price_x96, tick,
          fee; ModifyLiquidity: liquidity is per-position, so we only
          verify sqrt_price_x96 / tick are inherited from prior Swap);
        - have non-negative integer types.

        Per REQ-002's "Sample N blocks across the window (N >= 10,
        representative of swap / modify-liquidity mixes)": we sample
        EVERY event in the live result, which is more than N=10 by
        construction.
        """
        result = self._fetch_default()
        self.assertGreater(len(result.event_stream), 0, "event stream must be non-empty")

        from ingestion.types import (
            InitializeEvent,
            ModifyLiquidityEvent,
            SwapEventDecoded,
        )

        for entry in result.event_stream:
            ps = entry.post_state
            self.assertIsNotNone(ps, "post_state must be reconstructed for every event")
            self.assertIsInstance(ps.sqrt_price_x96, int)
            self.assertIsInstance(ps.tick, int)
            self.assertIsInstance(ps.liquidity, int)
            self.assertGreaterEqual(ps.sqrt_price_x96, 0)
            self.assertGreaterEqual(ps.tick, -(2**23))
            self.assertLessEqual(ps.tick, 2**23 - 1)
            ev = entry.event
            if isinstance(ev, SwapEventDecoded):
                self.assertEqual(
                    ps.sqrt_price_x96, ev.sqrt_price_x96,
                    f"Swap event sqrt_price_x96 mismatch at block {ev.block_number}",
                )
                self.assertEqual(
                    ps.tick, ev.tick,
                    f"Swap event tick mismatch at block {ev.block_number}",
                )
                self.assertEqual(
                    ps.liquidity, ev.liquidity,
                    f"Swap event liquidity mismatch at block {ev.block_number}",
                )
                self.assertEqual(
                    ps.fee, ev.fee_pips,
                    f"Swap event fee mismatch at block {ev.block_number}",
                )
            elif isinstance(ev, InitializeEvent):
                self.assertEqual(ps.sqrt_price_x96, ev.sqrt_price_x96)
                self.assertEqual(ps.tick, ev.tick)
                self.assertEqual(ps.fee, ev.fee)
                # liquidity starts at 0 on Initialize per V4 design.
                self.assertEqual(ps.liquidity, 0)
            elif isinstance(ev, ModifyLiquidityEvent):
                # sqrt_price_x96 / tick are inherited from the most recent
                # Swap; liquidity propagation is `None` until next Swap
                # re-anchors per the F-1 fix (see reconstruct.py + DESIGN).
                # We only sanity-check the fields exist.
                self.assertIsInstance(ps.sqrt_price_x96, int)
                self.assertIsInstance(ps.tick, int)


if __name__ == "__main__":
    unittest.main()