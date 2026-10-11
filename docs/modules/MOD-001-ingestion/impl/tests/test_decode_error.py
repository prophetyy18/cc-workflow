"""EventDecodeError surfacing (DESIGN.md Provided Public Contracts).

Per DESIGN.md Failure semantics: "Numerical decode errors propagate as
EventDecodeError { block_number, log_index, raw: bytes }."

Per Implementation SKILL §13.1: each public capability has at least one
observable test. EventDecodeError is part of the public exception surface;
no test previously exercised the actual decode path.

Two triggering paths in _decode_log_to_event:
1. Empty `topics` list (api.py line 89).
2. topic0 does not match Initialize/Swap/ModifyLiquidity ABI (api.py line 169).

Both paths MUST propagate as EventDecodeError to the caller (api.py line 318).

Test pattern: include a valid Initialize log in the same window (so the
REQ-020(b) pre-check passes), then a broken log that fails in _decode_log_to_event.
"""
import os
import sys
import tempfile
import unittest

# Ensure impl/src is importable.
_IMPL_SRC = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, "src")
)
if _IMPL_SRC not in sys.path:
    sys.path.insert(0, _IMPL_SRC)

import _helpers


class TestEventDecodeError(unittest.TestCase):
    def test_empty_topics_raises_event_decode_error(self):
        """A log with empty topics in a window with a valid Initialize pre-check
        must raise EventDecodeError carrying the broken log's block_number/log_index."""
        from ingestion import fetch_event_stream
        from ingestion.exceptions import EventDecodeError

        valid_init = _helpers.make_init_log(100, 0)
        broken_log = dict(valid_init)
        broken_log["topics"] = []  # empty topics triggers EventDecodeError

        with tempfile.TemporaryDirectory() as tmp:
            ev_cache, ts_cache, cache_root = _helpers.fresh_caches(tmp)
            rpc = _helpers.mock_rpc(
                logs_by_window={(100, 110): [valid_init, broken_log]},
                block_timestamps={b: b * 1000 for b in range(100, 111)},
            )
            with self.assertRaises(EventDecodeError) as ctx:
                fetch_event_stream(
                    _helpers.POOL, 100, 110, rpc_client=rpc,
                    event_cache=ev_cache, timestamp_cache=ts_cache,
                    cache_root=cache_root,
                )
            err = ctx.exception
            self.assertEqual(err.block_number, 100)
            self.assertEqual(err.log_index, 0)

    def test_unknown_topic0_raises_event_decode_error(self):
        """A log whose topic0 doesn't match any V4 ABI in a window with a valid
        Initialize pre-check must raise EventDecodeError.

        Pick a topic0 provably NOT in the V4 ABI list (keccak of an arbitrary
        signature won't match Initialize/Swap/ModifyLiquidity)."""
        from ingestion import fetch_event_stream
        from ingestion.exceptions import EventDecodeError

        valid_init = _helpers.make_init_log(100, 0)
        unknown_topic = "0x" + ("11" * 32)  # arbitrary 32-byte value, not a V4 topic0
        broken_log = dict(valid_init)
        broken_log["topics"] = [unknown_topic]

        with tempfile.TemporaryDirectory() as tmp:
            ev_cache, ts_cache, cache_root = _helpers.fresh_caches(tmp)
            rpc = _helpers.mock_rpc(
                logs_by_window={(100, 110): [valid_init, broken_log]},
                block_timestamps={b: b * 1000 for b in range(100, 111)},
            )
            with self.assertRaises(EventDecodeError) as ctx:
                fetch_event_stream(
                    _helpers.POOL, 100, 110, rpc_client=rpc,
                    event_cache=ev_cache, timestamp_cache=ts_cache,
                    cache_root=cache_root,
                )
            err = ctx.exception
            self.assertEqual(err.block_number, 100)
            self.assertEqual(err.log_index, 0)


if __name__ == "__main__":
    unittest.main()