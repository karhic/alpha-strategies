# Primas production runbook

## Runtime

`causal-trading-engine` is the only execution/replay runtime.

Historical replay, paper trading and live trading instantiate the same Primas strategy implementation. The strategy receives only point-in-time data, current time, account state and persistent state; it never receives a mode flag, provider client or broker SDK.

## Canonical artifact

Every run emits the causaltrader append-only JSONL ledger. That ledger is the source of truth for:

- input events consumed;
- strategy actions;
- submitted orders;
- fills;
- run manifest and code revision.

Performance analytics are downstream and must not alter runtime behaviour.

## Historical benchmark profile

The benchmark profile exists to reproduce the documented Freeburg fingerprint using the canonical historical data/accounting conventions recovered in the scratchpad.

Expected headline:

- CAGR about 12.08%
- maximum drawdown about -16.43%
- Sharpe about 1.43
- equity exposure about 39.5%
- 43 risk-on entries

A clean replay is accepted only if its ledger-derived statistics reproduce the frozen benchmark within explicit tolerances.

## IBKR paper profile

IBKR integration belongs in the generic causaltrader IBKR adapter, not in Primas.

The live Primas profile should:

1. consume normalized current S&P and commercial-paper events;
2. evaluate the same strategy class on the weekly trigger;
3. map the risk-on target to SPY in the execution configuration;
4. leave risk-off capital in the configured cash/defensive implementation;
5. archive every consumed live event before or while processing it;
6. persist the resulting ledger;
7. replay the archived live event stream later and require identical strategy-decision fingerprints.

Paper and live differ only by broker/account configuration.

## Public callouts

Public publishing is a downstream subscriber to the canonical ledger. It must never call the strategy directly or become an execution dependency.

A callout may include:

- timestamp;
- sleeve/version;
- risk-on or risk-off state;
- current SPX versus MA52;
- current CP yield versus MA52;
- code revision / run identifier.

Publishing failure must have zero effect on trading.
