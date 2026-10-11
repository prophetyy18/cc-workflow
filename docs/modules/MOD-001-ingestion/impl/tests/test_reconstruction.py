"""REQ-002 reconstruction accuracy (state-propagation rule).

Per DESIGN.md Output semantics state-propagation rule:
- Swap event: post_state.sqrt_price_x96/tick/liquidity/fee = event fields.
- ModifyLiquidity event: post_state.sqrt_price_x96/tick = most recent prior Swap's;
  post_state.liquidity = current_liquidity + event.liquidityDelta;
  post_state.fee = None.
- Initialize event: post_state = event.sqrt_price_x96/tick/liquidity=0/fee.

Numerical expectations (F4 fix):
- V4 sqrtPriceX96 encoding: sqrtPriceX96 = floor(sqrt(price) * 2^96) = isqrt(price * 2**192).
- For price = 2.0: sqrtPriceX96 = isqrt(2 * 2**192) ≈ 2^96 * sqrt(2) ≈ 1.4142 * 2^96.
- For price = 1.0: sqrtPriceX96 = 2^96 exactly.
- tick = floor(log_{1.0001}(sqrtPriceX96 / 2^96)) — Uniswap convention.

Test fixture (F4 fix — independently re-derivable):
  Initialize → Swap event where (sqrt_price_x96, tick) BOTH encode the same price,
  so the fixture does not encode an impossible pool state.
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


class TestReconstruction(unittest.TestCase):
    def test_swap_event_propagates_state(self):
        """Swap event: post_state.sqrt_price_x96/tick/liquidity/fee = event fields.

        Fixture: Swap at price=2.0 (sqrtPriceX96 = isqrt(2 * 2**192) ≈ 2^96 * sqrt(2),
        tick = log_{1.0001}(2.0) ≈ 6931). Both values encode the same price.
        """
        from ingestion import fetch_event_stream
        from ingestion.types import SwapEventDecoded

        # sqrtPriceX96 for price=2.0 (floor of sqrt(2) * 2^96).
        sqrt_price_x96 = int((2 * (2 ** 192)) ** 0.5)
        tick = 6931
        liquidity = 5 * 10 ** 18
        fee = 3000

        window_logs = [
            _helpers.make_init_log(100, 0),
            _helpers.make_swap_log(
                101, 0,
                sqrt_price_x96=sqrt_price_x96,
                liquidity=liquidity,
                tick=tick,
                fee=fee,
            ),
        ]
        block_ts = {b: b * 1000 for b in range(100, 103)}

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
            swap_entries = [
                e for e in result.event_stream
                if isinstance(e.event, SwapEventDecoded)
            ]
            self.assertEqual(len(swap_entries), 1)
            post = swap_entries[0].post_state
            self.assertEqual(post.sqrt_price_x96, sqrt_price_x96)
            self.assertEqual(post.liquidity, liquidity)
            self.assertEqual(post.tick, tick)
            self.assertEqual(post.fee, fee)  # Swap event carries fee

    def test_modify_liquidity_inherits_swap_state(self):
        """ModifyLiquidity inherits sqrt_price_x96/tick from most recent Swap; fee is None."""
        from ingestion import fetch_event_stream
        from ingestion.types import ModifyLiquidityEvent

        # Initialize → Swap (sets state) → ModifyLiquidity (uses prior swap state).
        # Both sqrt_price_x96 and tick are consistent for the same price.
        sqrt_price_x96 = int((2 * (2 ** 192)) ** 0.5)  # price=2.0
        tick = 6931

        window_logs = [
            _helpers.make_init_log(100, 0),
            _helpers.make_swap_log(
                101, 0,
                sqrt_price_x96=sqrt_price_x96,
                liquidity=10 ** 18,
                tick=tick,
            ),
            _helpers.make_modify_log(
                102, 0,
                tick_lower=-_helpers.TICK_SPACING * 10,
                tick_upper=_helpers.TICK_SPACING * 10,
                liquidity_delta=5 * 10 ** 17,
            ),
        ]
        block_ts = {b: b * 1000 for b in range(100, 104)}

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
            mod_entries = [
                e for e in result.event_stream
                if isinstance(e.event, ModifyLiquidityEvent)
            ]
            self.assertEqual(len(mod_entries), 1)
            post = mod_entries[0].post_state
            # State-propagation: sqrtPriceX96/tick from most recent Swap.
            self.assertEqual(post.sqrt_price_x96, sqrt_price_x96)
            self.assertEqual(post.tick, tick)
            # Liquidity = previous + delta = 10**18 + 5*10**17 = 1.5*10**18.
            self.assertEqual(post.liquidity, 10 ** 18 + 5 * 10 ** 17)
            # Fee = None (ModifyLiquidity doesn't carry fee per REQ-002).
            self.assertIsNone(post.fee)


if __name__ == "__main__":
    unittest.main()
