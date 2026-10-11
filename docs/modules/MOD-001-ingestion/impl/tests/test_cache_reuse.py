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
        import json

        with tempfile.TemporaryDirectory() as tmp:
            cache = EventCache(root=os.path.join(tmp, "events"))
            # Write known raw bytes.
            raw = b'[{"event": "test"}]'
            cache.write(_helpers.POOL, 100, 200, raw)

            cached, _ = cache.read_with_corruption_check(_helpers.POOL, 100, 200)
            self.assertEqual(cached, raw)

    def test_fetch_writes_deterministic_sorted_json_to_cache(self):
        """REQ-N02 byte-identity via the FETCH path (not just cache round-trip).

        fetch_event_stream writes `json.dumps(raw_logs, sort_keys=True)` to cache.
        The cached file content must equal the independently-computed sorted-JSON
        serialization of raw_logs — so REQ-020(c) SHA-256 check is meaningful
        (deterministic round-trip), independent of dict insertion order.

        Pinning the expected content as the independently-computed serialization,
        not derived from the impl's return.
        """
        from ingestion import fetch_event_stream
        import json

        # Valid Initialize + a non-Init log whose dict insertion order is NOT
        # alphabetical — proves sort_keys=True is in effect at the write boundary.
        valid_init = _helpers.make_init_log(100, 0)
        swap_log_unsorted = {
            "transactionHash": "0x" + "aa" * 32,
            "logIndex": "0x1",
            "address": _helpers.POOL,
            "data": "0x",
            "blockHash": "0x" + ("00" * 32),
            "topics": [],  # empty topics is fine here; we don't decode past cache write
            "removed": False,
            "transactionIndex": "0x0",
            "blockNumber": "0x65",
        }
        raw_logs = [valid_init, swap_log_unsorted]

        with tempfile.TemporaryDirectory() as tmp:
            ev_cache, ts_cache, cache_root = _helpers.fresh_caches(tmp)
            rpc = _helpers.mock_rpc(
                logs_by_window={(100, 110): raw_logs},
                block_timestamps={b: b * 1000 for b in range(100, 111)},
            )
            # Cache is written in step 2 (pagination) BEFORE step 3 (decode);
            # a decode error on the second log leaves the cache file on disk.
            from ingestion.exceptions import EventDecodeError
            try:
                fetch_event_stream(
                    _helpers.POOL, 100, 110, rpc_client=rpc,
                    event_cache=ev_cache, timestamp_cache=ts_cache, cache_root=cache_root,
                )
            except EventDecodeError:
                pass

            cache_path = os.path.join(tmp, "events", _helpers.POOL, "100_110.json")
            self.assertTrue(os.path.exists(cache_path), "cache file should be on disk after pagination")
            with open(cache_path, "rb") as f:
                cached_bytes = f.read()

            expected_bytes = json.dumps(raw_logs, sort_keys=True).encode("utf-8")
            self.assertEqual(cached_bytes, expected_bytes)


if __name__ == "__main__":
    unittest.main()
