"""REQ-020(a) RPC truncation surfacing.

Per DESIGN.md Verification § REQ-020(a): Inject a mock RPC client that
returns truncated results for one sub-range (or raises the truncation
signal). Expected: EventStreamFetchError with cache_corruption_events,
partial_entries, and failed_range populated.
"""
import os
import tempfile
import unittest

import _helpers


class TestPaginationTruncation(unittest.TestCase):
    def test_rpc_truncation_raises_event_stream_fetch_error(self):
        from ingestion import fetch_event_stream
        from ingestion.exceptions import EventStreamFetchError

        # A single sub-window [10, 20] returns truncated results (>= cap).
        pool = _helpers.POOL
        cached_block_ts = {b: b for b in range(10, 21)}

        rpc = _helpers.mock_rpc(
            logs_by_window={(10, 20): [_helpers.make_init_log(10, 0)]},
            block_timestamps=cached_block_ts,
            cap_get_logs=1,  # Force truncation by setting cap below the result count
        )

        with tempfile.TemporaryDirectory() as tmp:
            ev_cache, ts_cache, cache_root = _helpers.fresh_caches(tmp)
            with self.assertRaises(EventStreamFetchError) as ctx:
                fetch_event_stream(
                    pool, 10, 20, rpc_client=rpc,
                    event_cache=ev_cache, timestamp_cache=ts_cache,
                    cache_root=cache_root,
                )
            err = ctx.exception
            self.assertEqual(err.cause, "rpc_truncation")
            self.assertEqual(err.failed_range, (10, 20))


if __name__ == "__main__":
    unittest.main()
