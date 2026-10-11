"""REQ-020(b) ValidationError on missing Initialize / invalid inputs.

Per DESIGN.md Verification § REQ-020(b):
- Pool address without Initialize in window → ValidationError("no_initialize_in_window").
- Invalid pool address (non-hex) → ValidationError("invalid_pool_address").
"""
import os
import tempfile
import unittest

import _helpers


class TestNoInitialize(unittest.TestCase):
    def test_no_initialize_in_window_raises_validation_error(self):
        from ingestion import fetch_event_stream
        from ingestion.exceptions import ValidationError

        # Window contains only a Swap event — no Initialize.
        window_logs = [_helpers.make_swap_log(100, 0)]

        rpc = _helpers.mock_rpc(
            logs_by_window={(100, 200): window_logs},
            block_timestamps={b: b * 1000 for b in range(100, 201)},
        )
        with tempfile.TemporaryDirectory() as tmp:
            ev_cache, ts_cache, cache_root = _helpers.fresh_caches(tmp)
            with self.assertRaises(ValidationError) as ctx:
                fetch_event_stream(
                    _helpers.POOL, 100, 200, rpc_client=rpc,
                    event_cache=ev_cache, timestamp_cache=ts_cache,
                    cache_root=cache_root,
                )
            self.assertEqual(ctx.exception.reason, "no_initialize_in_window")

    def test_invalid_address_raises_validation_error(self):
        from ingestion import fetch_event_stream
        from ingestion.exceptions import ValidationError

        with tempfile.TemporaryDirectory() as tmp:
            ev_cache, ts_cache, cache_root = _helpers.fresh_caches(tmp)
            rpc = _helpers.mock_rpc(
                logs_by_window={},
                block_timestamps={},
            )
            with self.assertRaises(ValidationError) as ctx:
                fetch_event_stream(
                    "not-a-hex-address", 100, 200, rpc_client=rpc,
                    event_cache=ev_cache, timestamp_cache=ts_cache,
                    cache_root=cache_root,
                )
            self.assertEqual(ctx.exception.reason, "invalid_pool_address")


if __name__ == "__main__":
    unittest.main()
