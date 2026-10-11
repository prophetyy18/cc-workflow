"""REQ-019 / REQ-N04: FetchStats fields populated correctly.

Per DESIGN.md Verification § REQ-019 (timestamp acquisition) + § REQ-N04:
- cache_hit_count: sub-ranges served from on-disk cache (granularity = sub-ranges, F5+F-E fix).
- avg_block_time_seconds: ALWAYS populated, float seconds (F1 fix).
- last_event_block_timestamp: ALWAYS populated, int seconds (F1 fix).
- cache_corruption_events: list of records (empty on clean run).
"""
import os
import tempfile
import unittest

import _helpers


class TestFetchStats(unittest.TestCase):
    def test_clean_run_populates_all_fetch_stats_fields(self):
        from ingestion import fetch_event_stream

        # Single Initialize + Single Swap in window [100, 110].
        window_logs = [
            _helpers.make_init_log(100, 0),
            _helpers.make_swap_log(105, 0),
        ]
        block_ts = {b: b * 2 for b in range(100, 111)}  # 2s per block

        with tempfile.TemporaryDirectory() as tmp:
            ev_cache, ts_cache, cache_root = _helpers.fresh_caches(tmp)
            rpc = _helpers.mock_rpc(
                logs_by_window={(100, 110): window_logs},
                block_timestamps=block_ts,
            )
            result = fetch_event_stream(
                _helpers.POOL, 100, 110, rpc_client=rpc,
                event_cache=ev_cache, timestamp_cache=ts_cache, cache_root=cache_root,
            )

            stats = result.stats
            self.assertEqual(stats.cache_hit_count, 0)
            self.assertEqual(stats.cache_corruption_events, [])
            self.assertIsInstance(stats.avg_block_time_seconds, float)
            self.assertGreater(stats.avg_block_time_seconds, 0)
            self.assertIsInstance(stats.last_event_block_timestamp, int)
            # Last event block is 105.
            self.assertEqual(stats.last_event_block_timestamp, 105 * 2)

    def test_cache_hit_count_increments_per_subrange(self):
        from ingestion import fetch_event_stream

        window_logs = [
            _helpers.make_init_log(100, 0),
            _helpers.make_swap_log(150, 0),
        ]

        with tempfile.TemporaryDirectory() as tmp:
            ev_cache, ts_cache, cache_root = _helpers.fresh_caches(tmp)
            rpc = _helpers.mock_rpc(
                logs_by_window={(100, 200): window_logs},
                block_timestamps={b: b * 1000 for b in range(100, 201)},
            )
            # First run.
            r1 = fetch_event_stream(
                _helpers.POOL, 100, 200, rpc_client=rpc,
                event_cache=ev_cache, timestamp_cache=ts_cache, cache_root=cache_root,
            )
            self.assertEqual(r1.stats.cache_hit_count, 0)
            # Second run — cache hit_count >= 1.
            r2 = fetch_event_stream(
                _helpers.POOL, 100, 200, rpc_client=rpc,
                event_cache=ev_cache, timestamp_cache=ts_cache, cache_root=cache_root,
            )
            self.assertGreaterEqual(r2.stats.cache_hit_count, 1)


if __name__ == "__main__":
    unittest.main()
