# Competitive Returns

Four weekly conditions are `Good` when the current value is below its value 24 weeks ago:

1. long Treasury yield
2. 3-month T-bill yield
3. S&P 500 dividend yield
4. CPI

Long S&P 500 when at least **2 of 4** are Good; otherwise cash.

## Results

| Metric | Freeburg | Reconstruction |
|---|---:|---:|
| CAGR | 12.9% | **12.86%** |
| Max drawdown | -35.9% | **-33.92%** |
| Sharpe | — | **1.08** |
| Equity exposure | — | **50.16%** |
| Risk-on entries | — | **80** |

Reconstruction: 1970-07-31 to 2013-09-27, 2,253 weeks, using 10Y Treasury as the public long-bond-yield analogue, 7-day availability safety and Freeburg's 90% CP cash convention.

### Post-2013

2013-10-04 to 2026-08-14: **11.34% CAGR, 0.98 Sharpe, -31.68% max drawdown, 52.46% equity exposure**.

## Data provenance

- Long Treasury: Federal Reserve constant-maturity Treasury yield; 10Y is the primary public analogue used in the validated reconstruction.
- 3-month T-bill: Federal Reserve H.15.
- S&P dividend yield: FRASER first-published observations followed by archived S&P dividend data, only after availability.
- CPI: publication-aware series with a one-month delay in the historical reconstruction.
- Risk-off accounting: 90% of 3-month commercial-paper yield / 52.

The exact Pinnacle long-T-bond series remains a source-identity ambiguity; the 10Y public implementation is frozen rather than optimized against returns.
