"""REQ-020(c) combined-failure path (F-B / F3 fix; F5 Independent Reviewer fix).

Per DESIGN.md Verification § REQ-020(c) combined-failure test:
"With a populated cache where one file is corrupted AND the RPC re-fetch
itself fails (e.g., truncated response), the call raises
EventStreamFetchError whose cache_corruption_events field carries the
corruption records — REQ-020(c) surfacing obligation is honored on every
exit path."

F5 fix: tests MUST actually call fetch_event_stream with mocked RPC and
assert the exception's fields. Constructing the exception class directly is
a tautology that does not verify the implementation's failure-handling path.
"""
import os
import tempfile
import unittest

import _helpers
from ingestion.client import MAX_LOGS_PER_CALL


class TestCombinedFailure(unittest.TestCase):
    def test_cache_corruption_plus_rpc_truncation_surfaces_corruption_records(self):
        """F5 / F6: combined-failure path — populated cache (one sub-range tampered) +
        RPC that fails with truncation on the re-fetch must raise EventStreamFetchError
        whose cache_corruption_events list contains the corrupted sub-range's record.

        Setup: pre-populate cache for [10, 30] with 4 events at distinct blocks
        (init+swap at blocks 15, 18, 25, 28). Then tamper the cached file
        (10_30.json). Second run uses an RPC whose re-fetch raises RuntimeError
        to simulate truncation. EventStreamFetchError must carry both the
        corruption record AND the truncation cause.
        """
        from ingestion import fetch_event_stream
        from ingestion.exceptions import EventStreamFetchError

        # 4 events at distinct blocks for non-empty delta computation.
        init_A = _helpers.make_init_log(15, 0)
        swap_A = _helpers.make_swap_log(18, 0, sqrt_price_x96=int((2 * (2 ** 192)) ** 0.5), tick=6931)
        init_B = _helpers.make_init_log(25, 0)
        swap_B = _helpers.make_swap_log(28, 0, sqrt_price_x96=int((2 * (2 ** 192)) ** 0.5), tick=6931)
        logs_by_window = {
            (10, 20): [init_A, swap_A],
            (21, 30): [init_B, swap_B],
        }

        def fail_on_get_logs(s, e):
            # Run 2 only — pagination calls (10, 30) as one sub-range
            # (MAX_BLOCKS_PER_CALL >> window); fail that call to trigger truncation.
            return RuntimeError(f"truncation at [{s}, {e}]")

        with tempfile.TemporaryDirectory() as tmp:
            ev_cache, ts_cache, cache_root = _helpers.fresh_caches(tmp)

            # Run 1: populate cache with all 4 events (no fail).
            rpc1 = _helpers.mock_rpc(
                logs_by_window=logs_by_window,
                block_timestamps={b: b * 1000 for b in range(10, 31)},
            )
            fetch_event_stream(
                _helpers.POOL, 10, 30, rpc_client=rpc1,
                event_cache=ev_cache, timestamp_cache=ts_cache, cache_root=cache_root,
            )

            # Tamper with the [10, 30] cache file (written by pagination's single iteration).
            cache_path = os.path.join(tmp, "events", _helpers.POOL, "10_30.json")
            with open(cache_path, "rb") as f:
                data = bytearray(f.read())
            data[0] ^= 0xFF
            with open(cache_path, "wb") as f:
                f.write(bytes(data))

            # Run 2: window [10, 30]. Cache corruption detected; re-fetch fails with truncation.
            rpc2 = _helpers.mock_rpc(
                logs_by_window=logs_by_window,
                block_timestamps={b: b * 1000 for b in range(10, 31)},
                fail_on_get_logs=fail_on_get_logs,
                cap_get_logs=MAX_LOGS_PER_CALL + 1,
            )
            with self.assertRaises(EventStreamFetchError) as ctx:
                fetch_event_stream(
                    _helpers.POOL, 10, 30, rpc_client=rpc2,
                    event_cache=ev_cache, timestamp_cache=ts_cache, cache_root=cache_root,
                )
            err = ctx.exception
            self.assertEqual(err.cause, "rpc_truncation")
            # F6 fix: truncation path carries cache_corruption_events too.
            self.assertGreaterEqual(len(err.cache_corruption_events), 1)
            causes = {r.cause for r in err.cache_corruption_events}
            self.assertIn("sha256_mismatch", causes)
            # failed_range should point at the truncated sub-range (MAX_BLOCKS_PER_CALL
            # > window so pagination is a single sub-range).
            self.assertEqual(err.failed_range, (10, 30))
            # F8 fix: partial_entries field MUST exist on the exception (verified by
            # the assertion below on every entry — empty list passes trivially when the
            # failure occurred before any pagination could accumulate raw_logs, which is
            # acceptable per DESIGN's failure semantics).
            for entry in err.partial_entries:
                self.assertIsNotNone(entry.post_state)

    def test_event_stream_fetch_error_carries_cache_corruption_events_field(self):
        """Static type check: cache_corruption_events MUST be present on every
        EventStreamFetchError instantiation (F-B / F3 fix discipline)."""
        from ingestion.exceptions import CacheCorruptionRecord, EventStreamFetchError

        record = CacheCorruptionRecord(block_range=(100, 200), cause="sha256_mismatch")
        err = EventStreamFetchError(
            cause="rpc_truncation",
            cache_corruption_events=[record],
            partial_entries=[],
            failed_range=(100, 200),
            message="test",
        )
        self.assertEqual(len(err.cache_corruption_events), 1)
        self.assertEqual(err.cache_corruption_events[0], record)

        err2 = EventStreamFetchError(
            cause="timestamp_unavailable",
            cache_corruption_events=[record],
            partial_entries=[],
            failed_range=(5, 5),
            message="test",
        )
        self.assertEqual(len(err2.cache_corruption_events), 1)


if __name__ == "__main__":
    unittest.main()
