"""REQ-020(c) cache corruption surfacing.

Per DESIGN.md Verification § REQ-020(c):
- With a populated cache, flip one byte in one cached file. Re-run;
  expected: call still succeeds (range re-fetched), FetchStats.cache_corruption_events
  contains a CacheCorruptionRecord for the affected range, returned stream
  equivalent to fresh-fetch, other cached files untouched.
"""
import os
import tempfile
import unittest

import _helpers


class TestCacheCorruption(unittest.TestCase):
    def test_sha256_mismatch_surfaces_corruption_record(self):
        from ingestion import fetch_event_stream

        window_logs = [
            _helpers.make_init_log(100, 0),
            _helpers.make_swap_log(105, 0),
        ]
        block_ts = {b: b * 1000 for b in range(100, 111)}

        with tempfile.TemporaryDirectory() as tmp:
            ev_cache, ts_cache, cache_root = _helpers.fresh_caches(tmp)
            rpc = _helpers.mock_rpc(
                logs_by_window={(100, 110): window_logs},
                block_timestamps=block_ts,
            )
            # First run — populate cache.
            r1 = fetch_event_stream(
                _helpers.POOL, 100, 110, rpc_client=rpc,
                event_cache=ev_cache, timestamp_cache=ts_cache, cache_root=cache_root,
            )
            self.assertEqual(r1.stats.cache_corruption_events, [])

            # Tamper with the cached event file (flip a byte).
            cache_path = os.path.join(tmp, "events", _helpers.POOL, "100_110.json")
            with open(cache_path, "rb") as f:
                data = bytearray(f.read())
            data[0] ^= 0xFF  # flip first byte
            with open(cache_path, "wb") as f:
                f.write(bytes(data))

            # Second run — corruption detected, FetchStats records it, fetch re-runs.
            r2 = fetch_event_stream(
                _helpers.POOL, 100, 110, rpc_client=rpc,
                event_cache=ev_cache, timestamp_cache=ts_cache, cache_root=cache_root,
            )
            self.assertEqual(len(r2.stats.cache_corruption_events), 1)
            record = r2.stats.cache_corruption_events[0]
            self.assertEqual(record.block_range, (100, 110))
            self.assertEqual(record.cause, "sha256_mismatch")
            # Returned stream still equivalent to fresh-fetch (2 entries).
            self.assertEqual(len(r2.event_stream), 2)


if __name__ == "__main__":
    unittest.main()
