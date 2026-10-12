# Freeburg

> **Release status (11 October 2026):** Five historical strategy decision replays run successfully through the causal engine. The sixth (Heine) is **not** an exact historical reconstruction, and the independent free-source data profile remains subject to third-party licensing and original-vintage timing limitations. Start with [Release status](RELEASE_STATUS.md), [fresh-data quickstart](QUICKSTART_DATA.md), and [rebuild results](REBUILD_RESULTS_2026-10-11.md). Do **not** claim fully free, point-in-time, six-sleeve reproduction yet.

Clean, auditable reconstruction of the six Freeburg timing sleeves.

This directory consolidates the validated work from `karhic/edge-research-scratchpad` into a readable strategy project. The scratchpad remains the research archive; this directory is the clean implementation and documentation layer.

## Design goals

A reader should be able to:

1. read each sleeve rule in a small amount of code;
2. trace every input to a documented source;
3. rebuild/download the data using provided scripts;
4. verify that only information available at the decision time is visible to the strategy;
5. replay historical data through the exact strategy code used live;
6. inspect the resulting canonical ledger of events, decisions, orders and fills; and
7. calculate performance independently from that ledger.

The core invariant is:

> **Historical backtest = chronological replay through the same strategy implementation used live.**

There is no separate Freeburg backtester containing alternate signal logic.

## Runtime boundary

`karhic/causal-trading-engine` is the generic runtime for Freeburg.

Freeburg supplies strategy code, configuration and normalized point-in-time `DataEvent` streams. The runtime supplies the causal clock/data barrier, replay/live event loop, execution abstraction and append-only ledger.

The Freeburg strategy must not know whether it is being replayed or run live. It receives the same generic context and emits the same generic targets/actions in either case.

`karhic/open-alpha-verifier` is **not** an alternative Freeburg runtime. It is an optional downstream verification project for independently checking published strategy outputs/ledgers, especially when strategy logic is private.

## Canonical output

The canonical product of a historical replay is the raw runtime ledger, not a Sharpe ratio or chart.

The ledger should contain enough information to independently reconstruct the run:

- run manifest and code/config identity;
- consumed data events and their point-in-time timestamps;
- strategy actions / target weights;
- submitted orders;
- fills;
- any required account/portfolio state emitted by the runtime.

Performance statistics and plots are downstream analytics. They should be reproducible from the ledger without rerunning or reimplementing the strategy.

This separation makes the claim easy to audit: the same strategy code generated the historical decisions and the live decisions; analytics merely summarize the resulting ledger.

## The six sleeves

1. Primas
2. Triple-40
3. Heine
4. Pu Shen
5. Competitive Returns
6. Prime / Discount Spread

The equal-weight six-sleeve portfolio is a portfolio layer, not a seventh sleeve.

## What is already established

The accounting and most of the historical reconstruction work already exists in `edge-research-scratchpad`; it is not being rediscovered here.

The corrected scratchpad reconstruction reached approximately:

- five-sleeve common-sample portfolio: 11.52% CAGR / -9.16% max drawdown;
- six sleeves with the current Heine return proxy: 11.34% CAGR / -7.33% max drawdown;
- Freeburg published six-sleeve target: 11.3% CAR / -11.7% max drawdown.

The mean-return fingerprint is therefore essentially replicated. The main unresolved historical discrepancy is the exact weekly Dow Jones 20/Composite Bond return path used by Heine, whose current proxy is too smooth and therefore understates portfolio drawdown.

## Project policy

This clean project ports canonical results, source logic, timing conventions and accounting from the scratchpad. It does not silently replace them with new approximations.

Where a result is unresolved, the unresolved state is documented explicitly rather than tuned away.

The generic runtime remains outside this repository. Freeburg-specific strategy and data code live here; generic replay/live machinery stays in `causal-trading-engine`; analytics and optional third-party verification remain downstream concerns.


### Reproducing the four-sleeve modeled return series

[Exact instructions, sources, checks, and important limitations](REPRODUCE_FOUR.md). This standalone tool runs from local CSV source inputs without the separate private scratchpad code; a separately obtained original archived S&P quarterly source is still necessary for identical historical statistics.
