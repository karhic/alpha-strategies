# Primas

Weekly market-timing strategy documented by Nelson Freeburg.

## Rule

Risk-on when both are true:

1. S&P 500 > its 52-week simple moving average
2. 3-month commercial-paper yield < its 52-week simple moving average

Otherwise risk-off.

## Results

### Freeburg vs reconstruction, 1970-2013

| Metric | Freeburg | Reconstruction |
|---|---:|---:|
| CAGR | 12.1% | **12.08%** |
| Max drawdown | -16.4% | **-16.43%** |
| Sharpe | — | **1.43** |
| Equity exposure | — | **39.52%** |
| Risk-on entries | — | **43** |

Reconstruction period: **1970-12-25 to 2013-09-27** (2,232 weeks).

The clean causal replay independently reproduces the same 2,232 decisions, 39.5161% equity exposure and 43 risk-on transitions.

### Post-2013, out of sample

Period: **2013-10-04 to 2026-09-04**.

| Metric | Primas | S&P 500* |
|---|---:|---:|
| CAGR | **7.58%** | 14.33% |
| Sharpe | **0.91** | 0.91 |
| Max drawdown | **-13.20%** | -31.67% |
| Terminal wealth | **2.57x** | 5.64x |
| Equity exposure | **37.63%** | 100% |
| Risk-on entries | **21** | — |

\*Same weekly S&P total-return approximation used for comparison.

The post-2013 figures are not part of Freeburg's published sample.

## Data provenance

### S&P 500

- Signal input: weekly S&P 500 level
- Source used by the clean rebuild: Yahoo Finance `^GSPC` daily history
- Normalization: final observation of each Friday week
- Dividends are used only for return accounting, not for the signal

### 3-month commercial paper

The historical series is explicitly spliced because no single source covers the full sample:

- **pre-April 1971:** NBER Macrohistory `m13002` (60-90 day prime commercial paper), month-start stamped and carried forward weekly
- **April 1971-August 1997:** Federal Reserve H.15 `H0.RIFSPPCM03_N.WF`
- **September 1997 onward:** Federal Reserve `RIFSPPNAAD90_N.WF` (90-day nonfinancial AA commercial paper)

Federal Reserve numeric missing-value sentinels such as `-9999` are discarded before normalization.

### Return accounting

- Risk-on: S&P 500 weekly price return + weekly dividend-yield accrual
- Risk-off: commercial-paper yield / 52
- Headline replication uses 100% commercial-paper carry

Historical dividend data were reconstructed from contemporaneous Standard & Poor's observations preserved in FRASER's *Economic Indicators* archive, with later archived S&P observations where required.

## Reproducibility

`build_historical_events.py` rebuilds the weekly signal inputs from public sources. `run_replay.py` replays them through the same `PrimasStrategy` used for paper/live trading and emits the canonical decision ledger.

Research provenance and the original diagnostics remain in `karhic/edge-research-scratchpad`.
