"""F1 / F2 / F-D: timestamp acquisition + reorg detection.

Per DESIGN.md Verification § REQ-019 (F1 / F2 fix):
- Acquisition path = eth_getBlockByNumber per unique block in window.
- Cached {timestamp, block_hash} per block.
- Reorg detection: cached block_hash vs current block_hash mismatch → invalidate + REQ-020(c) recovery.
- avg_block_time_seconds: mean of positive consecutive deltas (F6 ignore non-positive).
- Empty-filtered-set edge cases (F-A fix):
  - 1 unique block → EventStreamFetchError { cause: "timestamp_no_pairs", cache_corruption_events: [...] }
  - All non-positive deltas → same.
"""
import os
import tempfile
import unittest

import _helpers


class TestTimestampCache(unittest.TestCase):
    def test_reorg_mismatch_surfaces_corruption_record(self):
        from ingestion import fetch_event_stream

        # First run: blocks [100, 102], block_hashes deterministic.
        # Second run: block 101's current_block_hash differs (simulate reorg).
        block_hashes_run1 = {b: "0x" + format(b, "x").rjust(64, "0") for b in range(100, 103)}
        block_hashes_run2 = dict(block_hashes_run1)
        block_hashes_run2[101] = "0x" + "ff" * 32  # reorged

        window_logs = [
            _helpers.make_init_log(100, 0),
            _helpers.make_swap_log(101, 0),
        ]

        with tempfile.TemporaryDirectory() as tmp:
            ev_cache, ts_cache, cache_root = _helpers.fresh_caches(tmp)

            # Run 1 — populate caches.
            rpc1 = _helpers.mock_rpc(
                logs_by_window={(100, 102): window_logs},
                block_timestamps={b: b * 1000 for b in range(100, 103)},
                block_hashes=block_hashes_run1,
            )
            r1 = fetch_event_stream(
                _helpers.POOL, 100, 102, rpc_client=rpc1,
                event_cache=ev_cache, timestamp_cache=ts_cache, cache_root=cache_root,
            )
            self.assertEqual(r1.stats.cache_corruption_events, [])

            # Run 2 — block 101 reorged.
            rpc2 = _helpers.mock_rpc(
                logs_by_window={(100, 102): window_logs},  # cache hit, no eth_getLogs called
                block_timestamps={b: b * 1000 for b in range(100, 103)},
                block_hashes=block_hashes_run2,
            )
            r2 = fetch_event_stream(
                _helpers.POOL, 100, 102, rpc_client=rpc2,
                event_cache=ev_cache, timestamp_cache=ts_cache, cache_root=cache_root,
            )
            # The reorg at block 101 → corruption record + new timestamp written.
            self.assertGreaterEqual(len(r2.stats.cache_corruption_events), 1)
            causes = {r.cause for r in r2.stats.cache_corruption_events}
            self.assertIn("reorg_block_hash_mismatch", causes)

    def test_single_block_window_raises_timestamp_no_pairs(self):
        from ingestion import fetch_event_stream
        from ingestion.exceptions import EventStreamFetchError

        window_logs = [_helpers.make_init_log(100, 0)]
        with tempfile.TemporaryDirectory() as tmp:
            ev_cache, ts_cache, cache_root = _helpers.fresh_caches(tmp)
            rpc = _helpers.mock_rpc(
                logs_by_window={(100, 100): window_logs},
                block_timestamps={100: 1700000000},
            )
            with self.assertRaises(EventStreamFetchError) as ctx:
                fetch_event_stream(
                    _helpers.POOL, 100, 100, rpc_client=rpc,
                    event_cache=ev_cache, timestamp_cache=ts_cache, cache_root=cache_root,
                )
            err = ctx.exception
            self.assertEqual(err.cause, "timestamp_no_pairs")
            self.assertEqual(err.cache_corruption_events, [])  # no corruption, just empty window

    def test_non_monotonic_timestamps_ignored_per_f6(self):
        from ingestion import fetch_event_stream

        # Three blocks 100, 101, 102; timestamps decreasing (L2 anomaly, F6).
        block_ts = {100: 100, 101: 90, 102: 80}
        window_logs = [
            _helpers.make_init_log(100, 0),
            _helpers.make_swap_log(101, 0),
            _helpers.make_modify_log(102, 0, liquidity_delta=10 ** 17),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            ev_cache, ts_cache, cache_root = _helpers.fresh_caches(tmp)
            rpc = _helpers.mock_rpc(
                logs_by_window={(100, 102): window_logs},
                block_timestamps=block_ts,
            )
            # All deltas non-positive → EventStreamFetchError(cause="timestamp_no_pairs").
            from ingestion.exceptions import EventStreamFetchError
            with self.assertRaises(EventStreamFetchError) as ctx:
                fetch_event_stream(
                    _helpers.POOL, 100, 102, rpc_client=rpc,
                    event_cache=ev_cache, timestamp_cache=ts_cache, cache_root=cache_root,
                )
            self.assertEqual(ctx.exception.cause, "timestamp_no_pairs")


if __name__ == "__main__":
    unittest.main()
