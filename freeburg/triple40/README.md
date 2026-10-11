# Triple-40

Long S&P 500 when:

- S&P 500 > its 40-week moving average, and
- either Moody's Baa yield < its 40-week moving average **or** 90-day commercial paper < its 40-week moving average.

Otherwise commercial paper/cash.

## Results

| Metric | Freeburg | Reconstruction |
|---|---:|---:|
| CAGR | 12.0% | **11.89%** |
| Max drawdown | -18.7% | **-18.81%** |
| Sharpe | — | **1.25** |
| Equity exposure | — | **53.79%** |
| Risk-on entries | — | **65** |

Reconstruction: 1970-10-02 to 2013-09-27, 2,244 weeks, using Freeburg's 90% commercial-paper cash convention.

### Post-2013

2013-10-04 to 2026-08-14: **10.68% CAGR, 1.10 Sharpe, -13.23% max drawdown, 59.91% equity exposure**.

## Data provenance

- S&P 500: weekly Friday last price level.
- Moody's Baa: Federal Reserve H.15 weekly seasoned Baa corporate yield (`RIMLPBAAR_N.WF`) for the historical reconstruction.
- 90-day commercial paper: NBER Macrohistory `m13002` pre-1971, Fed H.15 3-month prime CP from April 1971, Fed 90-day nonfinancial AA CP from September 1997 onward.
- Risk-off accounting: 90% of commercial-paper yield / 52.

`strategy.py` contains only the published rule; data timing/provenance and execution remain outside the strategy.


**[Year-by-year OOS comparison: annual return, excess Sharpe, Calmar and maximum drawdown vs S&P buy-and-hold and weekly-rebalanced 60/40](reports/README.md)** (2014–2025 full years; 2026 YTD). The 60/40 uses S&P total-return approximation plus AGG adjusted closes.
