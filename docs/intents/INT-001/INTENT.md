---
id: INT-001
title: Robinhood Chain UniswapV4 LP backtesting system (passive + CTA-driven strategies)
status: active
parent: null
related: []
impact_scope: []
created: 2026-10-08
updated: 2026-10-08
---

# Original Intent

我要创建一个 robinhood的 uniswapV4 做市商流动性回测系统

我希望在回测系统里支持CTA信号触发系统操作的回测，比如用布林线add liquidity或者quit liquidity 以及设置上下限等等

# Clarified Intent

Build a market-maker liquidity backtesting system targeting the **Robinhood Chain** (chain ID 4663) for **UniswapV4** positions. Scope is the **standard concentrated-liquidity model with multiple fee tiers** (no hooks, no custom 6909 accounting). Data source is the **public Robinhood Chain RPC** with iterative event fetching — V4 events carry post-state (`sqrtPriceX96`, `tick`, `liquidity`, `fee`) so no archive node is required. Output is a **local Web Dashboard styled after Robinhood** for visualizing LP performance.

The system supports two strategy modes on the same event-reconstructed price stream: (a) **passive range LP** (single position, no rebalance) — original scope; and (b) **CTA signal-driven active LP management** — uses technical-indicator signals (e.g. Bollinger Bands) to trigger LP operations such as `add_liquidity`, `quit_liquidity`, and `set_range` (upper/lower tick limits). Signal evaluation (assumed) runs on the historical price series reconstructed from V4 events.

# Constraints and Success Criteria

- V4 scope: concentrated liquidity, multi fee tier only (no hooks, no custom accounting)
- Chain: Robinhood Chain (Arbitrum-based L2, chain ID 4663)
- Data: public Robinhood Chain RPC, iterative event fetching for a single V4 pool. No archive node needed.
- Output: local web dashboard (Robinhood-style UI)
- Strategy modes: passive range LP **and** CTA signal-driven active LP. Both must work on the same data pipeline and produce a comparable P&L view.
- CTA position model: single position only (always one open range).
- CTA action vocabulary (v1, locked): `add_liquidity`, `quit_liquidity`, `set_range`, `partial_withdraw`, `rebalance_only`, `stop_loss_take_profit`.
- CTA indicator scope: general framework; Bollinger Bands ships as first concrete indicator.
- CTA signal frequency: per swap event.
- CTA capital sizing: fixed total capital; strategy allocates per open (default 100%).

# Decisions

- 2026-10-08: "robinhood的" interpreted as Robinhood Chain (Arbitrum L2), not Robinhood-style UX. — user-confirmed
- 2026-10-08: V4 feature scope = standard CL + multi fee tier; hooks and 6909 accounting out of scope. — user-confirmed (smallest viable scope)
- 2026-10-08: Data source = on-chain archive node historical replay. — user-confirmed (later revised: see 2026-10-08 below)
- 2026-10-08: **Data source revised** = public Robinhood Chain RPC with iterative event fetching. — user-challenged "archive node" assumption; empirical test showed public RPC returns full historical logs for a single pool address. V4 Swap events carry post-state (`sqrtPriceX96`, `tick`, `liquidity`, `fee`), so pool history can be reconstructed from event log stream alone. No archive node required.
- 2026-10-08: Output = local web dashboard with Robinhood-style UI. — user-confirmed
- 2026-10-08: Strategy model = passive range LP (single-position, no rebalance). — user-confirmed (simplest scope)
- 2026-10-08: **Strategy model expanded** to also include CTA signal-driven active LP management. Same backtest system, two strategy modes. User-confirmed. — extends, does not replace, the passive mode. Concrete action vocabulary at minimum: `add_liquidity`, `quit_liquidity`, `set_range` (update upper/lower tick limits). Initial indicator example: Bollinger Bands.
- 2026-10-08: CTA position-state model = **single position only** — always exactly one open range at a time. `add_liquidity` opens a new range (after quitting the old). — user-confirmed (simplest LP math surface).
-  2026-10-08: CTA indicator scope = **general indicator + signal framework**, with Bollinger Bands as the first concrete implementation. Other indicators plug in later without re-engineering. — user-confirmed.
-  2026-10-08: CTA action vocabulary (final) = `add_liquidity`, `quit_liquidity`, `set_range`, `partial_withdraw`, `rebalance_only`, `stop_loss_take_profit` (single action type with direction; triggers forced `quit_liquidity` when position value crosses a user-set threshold). — user-confirmed. **All six ship in v1.**
-  2026-10-08: CTA signal evaluation frequency = **per swap event** — re-evaluate on every V4 Swap event. No bar resampling in v1. — user-confirmed (simplest, signals fire at the exact block price moves).
-  2026-10-08: CTA capital sizing = **fixed total capital**, strategy allocates per open. User sets one total-capital field; default rule allocates 100% of available cash to each new position. — user-confirmed.
- 2026-10-08: Target pool scope = one manually-specified pool. — user-confirmed (smallest viable scope)
- 2026-10-08: Backtest window = V4 launch on Robinhood Chain (~July 2026) → today (~3 months). — user-confirmed
- 2026-10-08: Performance metrics = fee income + APR, impermanent loss (IL), and overall asset change (total portfolio value over time, net of fees and IL). — user-confirmed
- 2026-10-08: Pool address input = web dashboard form (not CLI or config file). — user-confirmed
- 2026-10-08: Data caching = local cache (first fetch from RPC, reuse on rerun). — user-confirmed
- 2026-10-08: Tech stack = agent-recommended. — user delegated decision. Recommendation: **Python** (pandas + web3.py + Streamlit). Rationale: best-in-class ecosystem for financial backtesting (pandas, numpy, vectorbt, backtesting.py), simple local dashboard via Streamlit (Robinhood-style UI achievable with custom CSS), web3.py is mature for EVM RPC + ABI decoding. TypeScript alternative noted but heavier for a single-user research tool.

# Facts and Research

- **Fact**: Robinhood Chain mainnet chain ID is **4663** (testnet is 46630). Currency is ETH.
  **Source**: chainlist.org/chain/4663; docs.robinhood.com/chain/connecting (via yieldo.me aggregator, since direct docs fetch returned 403)
  **Verified on**: 2026-10-08
  **Method**: web search cross-check across 3 independent aggregators
  **Scope**: mainnet config
  **Uncertainty**: low; consistent across sources. One outlier search returned "466" — likely stale or misread.

- **Fact**: Mainnet public RPC is `https://rpc.mainnet.chain.robinhood.com`. Public endpoints do **NOT** serve archive data.
  **Source**: yieldo.me/blog/ecosystems/how-to-start-on-robinhood-chain (paraphrasing docs.robinhood.com)
  **Verified on**: 2026-10-08
  **Method**: web search and fetch
  **Scope**: public RPC limits
  **Uncertainty**: medium — direct docs fetch blocked (403); verified via secondary aggregator only.

- **Fact**: Robinhood Chain public RPC returns historical `eth_getLogs` results for arbitrary block heights on a single contract address, up to 10,000 logs per query and 10M blocks per query range.
  **Source**: direct empirical test of `https://rpc.mainnet.chain.robinhood.com` against V4 PoolManager (`0x8366a39cc670b4001a1121b8f6a443a643e40951`) on 2026-10-08. Queries for Swap events from block ~77M returned full event data with `sqrtPriceX96`, `tick`, `liquidity`, `fee`, `amount0`, `amount1` in `data` field.
  **Verified on**: 2026-10-08
  **Method**: direct curl call to public RPC
  **Scope**: single-contract historical event queries
  **Uncertainty**: low for event/log data. **Caveat**: this approach reconstructs pool state from events alone. Reading `eth_call` against historical block heights for arbitrary storage slots still requires archive. But V4 events contain post-swap state, so for the backtest use case the public RPC suffices.

- **Fact**: Archive node access on Robinhood Chain requires a third-party paid provider. **Alchemy is officially recommended**; QuickNode, Chainstack, Blockdaemon, dRPC, Validation Cloud also supported.
  **Source**: docs.robinhood.com/chain/connecting via yieldo.me
  **Verified on**: 2026-10-08
  **Method**: web search
  **Scope**: archive access provisioning
  **Uncertainty**: low. **No longer required for this intent** — public RPC suffices given event-stream reconstruction approach.

- **Fact**: Uniswap V4 is deployed on Robinhood Chain. Reported TVL ~$60M as of mid-July 2026; ~880k MAU. Uniswap versions live on the chain: v2, v3, v4, UniswapX.
  **Source**: gov.uniswap.org/t/temp-check-protocol-fee-expansion-robinhood-chain/26168; theagenttimes.com
  **Verified on**: 2026-10-08
  **Method**: web search
  **Scope**: deployment status
  **Uncertainty**: low

- **Fact**: PoolManager address on Robinhood Chain reported as `0x8366a39cc670b4001a1121b8f6a443a643e40951`. PositionManager `0x58daec3116aae6d93017baaea7749052e8a04fa7`. Quoter `0x8dc178efb8111bb0973dd9d722ebeff267c98f94`. StateView `0xf3334192d15450cdd385c8b70e03f9a6bd9e673b`. WETH `0x0Bd7D308f8E1639FAb988df18A8011f41EAcAD73`.
  **Source**: theagenttimes.com article + Bitquery docs.bitquery.io docs
  **Verified on**: 2026-10-08
  **Method**: web search (single secondary source); Uniswap's official deployments page is behind a redirect I couldn't resolve
  **Scope**: V4 contract set
  **Uncertainty**: **medium-high** — single source. Should be re-verified by querying the actual contracts on-chain before use, or by fetching the official Uniswap deployments JSON.

- **Fact**: Robinhood Chain is an EVM-compatible L2. One source describes it as "Arbitrum Orbit", another as "OP Stack". Likely Arbitrum Orbit given the Robinhood–Arbitrum partnership history.
  **Source**: quicknode.com guides; web search
  **Verified on**: 2026-10-08
  **Method**: web search
  **Scope**: chain architecture
  **Uncertainty**: medium — affects how the system handles L1↔L2 bridging data; not material for V4 LP backtest which is intra-L2.

# Unknowns

- **Unknown**: Specific V4 pool address to backtest (currency0, currency1, fee tier, tick spacing). Pool address is required to start; user must supply when running the dashboard.
  **Why it matters**: Drives ABI decoding; different fee tiers have different swap economics.
  **How to resolve**: user supplies at runtime via dashboard form.

- **Unknown**: Position initialization shape — user specifies min/max ticks (centered ±X% from current price) or absolute tick range, and capital amount + entry/exit block range.
  **Why it matters**: Determines input form fields and event-slicing logic.
  **How to resolve**: clarify at spec level if needed; reasonable defaults can be assumed (centered ±20% with X% capital, full window).

- **Unknown**: External price reference for IL computation. V4 events give pool's internal price but IL vs HODL needs a stable external price (e.g., a reference AMM swap, or a CEX feed).
  **Why it matters**: IL is meaningless without a stable reference.
  **How to resolve**: Spec Agent should pick the simplest available — likely a chainlink oracle read at backtest entry/exit, or use pool's own swap prices. Mark as Spec Agent's call.

# Evaluation

(agent opinion — not user requirement)

- **Critical risk resolved**: "archive node" was assumed to be self-hosted or freely available. Empirical testing showed Robinhood Chain's public RPC serves full historical event logs for a single address (10M block / 10k log limits per query). Combined with V4 events carrying post-state, the public RPC is sufficient — no archive provider needed, no cost. User's intuition on this was correct.

- **Cost model**: zero ongoing operational cost for data. Only cost is local compute + storage (a few hundred MB of JSON logs for one pool over 3 months).

- **Scope is appropriately minimal**: standard CL + multi fee tier, no hooks, is the smallest viable LP backtest surface. Reduces risk of scope creep.

- **Why this might be premature**: Robinhood Chain is ~3 months old (launched July 2026). V4 TVL is modest (~$60M). Historical depth may be shallow — backtesting results may not be statistically meaningful yet. This is worth noting in the spec.

- **Alternative data path (now obsolete)**: originally proposed The Graph / Dune fallback. Public RPC + iterative event fetching turned out to suffice.

- **Re-verification needed**: V4 contract addresses on Robinhood Chain come from a single secondary source. Spec Agent should re-verify by on-chain `eth_call` to the PoolManager (e.g., read `protocolFees` slot or known public getter) before consuming them.

- **Modularity suggestion**: the event-fetching + state-reconstruction logic is a reusable component. If the user later wants to backtest more pools, or another V4 chain, the same module applies. Worth designing it as a library from the start.

- **Statistical caveat**: ~3 months of V4 history on a young L2 may not be enough for statistically robust backtests. The dashboard should expose this — e.g., confidence intervals or a "data coverage" badge — to discourage over-trusting results.

- **Tech stack recommendation rationale**: Python chosen because (1) pandas/numpy dominate quant backtesting, (2) Streamlit or Dash can ship a Robinhood-styled local dashboard in <100 LOC, (3) web3.py + eth-abi handle V4 ABI decoding, (4) Plotly/Bokeh cover the visualization needs. TypeScript alternative would require rolling our own AMM math and chart stack.

- **Position state during range out**: when current tick exits the LP's `[tick_lower, tick_upper]` range, the position holds only one token (the one not "out of range"). Fee earnings stop. The dashboard should make this visible — it is the dominant cause of "why my LP earned nothing" in real V4 use.

# Relationships and Impact

- Root intent. No parent, no related intents yet.
- `impact_scope` (initial): docs/, src/ (Python or TS likely), public RPC client + local log cache, Uniswap V4 SDK + ABI decoder, AMM math library, web dashboard (frontend), data pipeline (event ingestion + state reconstruction), CTA strategy engine (indicator framework + action dispatcher), backtest event-loop that drives both passive and CTA modes from the same reconstructed event stream.
- Downstream Spec(s) will need to cite INT-001.

# Spec Input

A Spec Agent with no prior context should know:

- **Goal**: Backtest UniswapV4 LP positions on Robinhood Chain (chain ID 4663), standard concentrated liquidity only, single user-specified pool.
- **Why**: User is a market maker evaluating LP strategies before deploying capital.
- **Success criteria**: Given a strategy spec (pool address + tick range + capital amount + entry time + exit time), reproduce historical LP performance faithfully (fees earned, impermanent loss, capital evolution) and visualize it in a local Robinhood-styled web dashboard.
- **Hard constraints**:
  - V4 features limited to standard CL + multi fee tier. No hooks, no 6909.
  - Data source = public Robinhood Chain RPC (`https://rpc.mainnet.chain.robinhood.com`). No paid archive provider.
  - Event reconstruction approach (10M block / 10k log limits per `eth_getLogs` call).
  - Single pool per backtest run (user-supplied address).
  - Local web dashboard (no cloud deployment).
- **Confirmed decisions** (do not re-litigate):
  - Target chain = Robinhood Chain (4663)
  - V4 PoolManager = `0x8366a39cc670b4001a1121b8f6a443a643e40951` (verify on-chain before use)
  - V4 features = standard CL + multi fee tier (no hooks, no 6909)
  - Strategy = passive range LP (single position, no rebalance)
  - Backtest window = V4 launch (~July 2026) → today (~3 months), user-supplied subrange within
  - Data source = public Robinhood Chain RPC + local cache, event-stream reconstruction
  - Output = local web dashboard (Robinhood-styled), input via form
  - Tech stack = Python (pandas + web3.py + Streamlit)
  - Metrics = fee income + APR, IL, total asset change
- **Verified facts**: see `# Facts and Research`. Key: V4 Swap events carry post-swap `sqrtPriceX96`/`tick`/`liquidity`/`fee`, so event log stream is sufficient for state reconstruction.
- **Unknowns still open (small)**: specific pool address per run, position range and capital per run, external price reference for IL.
- **What Spec Agent must NOT decide on its own**:
  - Whether to actually run on Robinhood Chain (locked).
  - Whether to use paid archive provider (locked: no, public RPC only).
  - V4 feature scope (locked: standard CL only).
  - Tech stack (locked: Python).
  - Metrics (locked: fee + APR, IL, total asset change).
  - Pool address, capital, range (user supplies at runtime — Spec must build the form, not pick defaults).
  - Whether to support CTA mode (locked: yes — must ship both passive and CTA-driven modes on the same data pipeline).
  - Whether CTA mode is a separate system (locked: no — same engine, same dashboard).

## Spec Input — CTA Strategy Mode (added 2026-10-08)

- **Goal**: On top of the existing event-reconstructed price stream, run a CTA strategy that emits LP actions when technical-indicator signals trigger. Both strategy modes share the same dashboard and metrics.
- **Action vocabulary (locked)**: `add_liquidity`, `quit_liquidity`, `set_range`, `partial_withdraw`, `rebalance_only`, `stop_loss_take_profit` (threshold-driven forced `quit_liquidity`).
- **Indicator layer**: general framework. Bollinger Bands ships as the first concrete indicator; spec must define the indicator interface so RSI/MACD/etc. can plug in later.
- **Position-state model (locked)**: single position only — one open range at a time.
- **Signal evaluation (locked)**: per swap event. No bar resampling in v1.
- **Capital sizing (locked)**: fixed total capital field in dashboard form; strategy allocates per `add_liquidity` (default rule = 100% of available cash).
- **Hard constraints (inherited from base intent)**: same chain, same data source, same Python tech stack, same metrics (fee + APR, IL, total asset change).
- **Spec Agent must NOT decide on its own**: whether to ship CTA mode (locked: yes); whether CTA mode replaces passive (locked: no, both coexist); the locked action vocab, position model, signal frequency, capital sizing, and indicator scope above.

# Resume Notes

2026-10-08: Round 3 complete. All foundational decisions made. Metrics = fee+APR / IL / total asset change. Pool input = web form. Caching = local. Tech stack = Python (agent recommendation, user accepted). Frontier effectively empty for user-side decisions; remaining unknowns (pool address, IL reference price, exact range) are runtime inputs. Ready for handoff to Spec Agent. User may archive INT-001 when downstream Spec is written.

2026-10-08: `refine` assessment (no topic) → **Keep**. No independent sub-goal with its own outcome or decision space. Cross-domain surface (data / math / UI) is implementation layering, not splitting-worthy per hard rules #13 & #14. Frontier remains empty; intent is bounded and ready for Spec.

2026-10-08: **Scope expanded** — CTA signal-driven active LP mode added (modify, not split; CTA is a feature of the same backtest engine, not a separate system). Confirmed action vocab: `add_liquidity`, `quit_liquidity`, `set_range`. Initial indicator example: Bollinger Bands. Frontier reopened on: indicator scope (one-off vs. framework), action vocab completeness, signal/bar granularity, position-state model (single vs. layered), capital allocation under CTA.

2026-10-08: CTA frontier closed (5/5). Locked decisions: single-position model; general indicator framework (BB first); action vocab expanded to 6 (`add_liquidity`, `quit_liquidity`, `set_range`, `partial_withdraw`, `rebalance_only`, `stop_loss_take_profit`); per-swap signal evaluation; fixed total capital with strategy-side allocation. Intent is now bounded for both passive and CTA modes — ready for handoff to Spec Agent. User may archive when downstream Spec is written.
