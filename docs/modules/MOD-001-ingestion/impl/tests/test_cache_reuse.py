"""REQ-003 cache reuse + REQ-N02 byte-identity.

Per DESIGN.md Verification § REQ-003 / REQ-N02:
- Fresh fetch populates cache; second fetch reuses cache (cache_hit_count > 0).
- Cached file content is byte-identical to raw RPC response.
"""
import os
import tempfile
import unittest

import _helpers


class TestCacheReuse(unittest.TestCase):
    def test_second_run_serves_from_cache(self):
        from ingestion import fetch_event_stream

        window_logs = [
            _helpers.make_init_log(100, 0),
            _helpers.make_swap_log(105, 0),
        ]

        with tempfile.TemporaryDirectory() as tmp:
            ev_cache, ts_cache, cache_root = _helpers.fresh_caches(tmp)
            rpc = _helpers.mock_rpc(
                logs_by_window={(100, 110): window_logs},
                block_timestamps={b: b * 1000 for b in range(100, 111)},
            )

            # First run — populates cache, cache_hit_count=0.
            r1 = fetch_event_stream(
                _helpers.POOL, 100, 110, rpc_client=rpc,
                event_cache=ev_cache, timestamp_cache=ts_cache, cache_root=cache_root,
            )
            self.assertEqual(r1.stats.cache_hit_count, 0)
            self.assertEqual(len(r1.event_stream), 2)

            # Second run — cache_hit_count >= 1.
            r2 = fetch_event_stream(
                _helpers.POOL, 100, 110, rpc_client=rpc,
                event_cache=ev_cache, timestamp_cache=ts_cache, cache_root=cache_root,
            )
            self.assertGreaterEqual(r2.stats.cache_hit_count, 1)

    def test_cached_file_is_byte_identical_to_raw(self):
        from ingestion.cache import EventCache
        from ingestion.client import RpcClient
        import json

        with tempfile.TemporaryDirectory() as tmp:
            cache = EventCache(root=os.path.join(tmp, "events"))
            # Write known raw bytes.
            raw = b'[{"event": "test"}]'
            cache.write(_helpers.POOL, 100, 200, raw)

            cached, _ = cache.read_with_corruption_check(_helpers.POOL, 100, 200)
            self.assertEqual(cached, raw)


if __name__ == "__main__":
    unittest.main()
