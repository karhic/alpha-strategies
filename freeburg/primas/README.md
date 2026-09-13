# Primas

Primas is the first Freeburg sleeve taken through the clean production pipeline.

## Rule

Evaluate once per week. Risk-on only when both conditions are true:

1. S&P 500 level is above its 52-week simple moving average.
2. 3-month commercial-paper yield is below its 52-week simple moving average.

Otherwise the sleeve is risk-off.

The rule is intentionally trivial to inspect. All complexity belongs outside the rule: data provenance, point-in-time availability, execution, ledger generation, and analytics.

## Published fingerprint

Freeburg reports approximately **12.1% compound annual return and -16.4% maximum drawdown**.

The corrected scratchpad reconstruction, using full commercial-paper carry and the constant/month-start pre-1971 seed convention, produced:

- period: 1970-12-25 through 2013-09-27
- weeks: 2,232
- CAGR: 12.0799%
- Sharpe: 1.4344
- maximum drawdown: -16.4293%
- max-DD peak: 1998-07-10
- max-DD trough: 1998-09-25
- equity exposure: 39.5161%
- risk-on entries: 43

This is an essentially exact fingerprint match, not an optimization target.

## Separation of concerns

Primas owns only:

- the published rule;
- logical dataset requirements;
- source/provenance documentation;
- benchmark and live configuration;
- sleeve-specific tests and expected fingerprints.

`causal-trading-engine` owns chronological replay, point-in-time visibility, broker abstraction, simulation, live/paper mode, and the canonical append-only ledger.

A separate analytics project should consume that ledger and calculate CAGR, drawdown, Sharpe, exposure, charts, tables, and comparison reports. Analytics must never feed information back into the strategy runtime.

## Same code live and replay

The production requirement is stronger than merely sharing formulas: historical replay and live paper trading must instantiate the same Primas strategy class. The strategy must have no mode flag and no direct provider or broker access.

Historical and live systems may use different data adapters, but both adapters must emit the same logical event identities and availability semantics.

## Status

- published rule: recovered
- historical fingerprint: essentially replicated
- historical accounting: recovered from canonical scratchpad diagnostics
- exact source lineage: documented in `DATA.md`
- causal replay port: next
- IBKR paper execution: next after replay parity
- public callout publishing: downstream adapter, never strategy logic
