# Pu Shen

Let `spread = S&P earnings yield - 90-day commercial-paper yield`.

Long S&P 500 when both are true:

- spread > spread 50 weeks ago
- S&P 500 > S&P 500 50 weeks ago

Otherwise commercial paper/cash.

## Results

Freeburg reports **10.0% CAGR / -15.1% max drawdown** through September 2013.

Two reconstructions are retained because earnings-history timing matters:

| Reconstruction | CAGR | Sharpe | Max DD | Exposure |
|---|---:|---:|---:|---:|
| Retrospective historical E/P close-match | **10.05%** | 1.42 | -15.68% | 29.56% |
| Strict publication-available/PIT | **10.25%** | 1.50 | **-11.34%** | 29.22% |

The retrospective row is useful for identifying Freeburg's historical fingerprint. **The PIT row is the deployable interpretation.** No finalized earnings value is backdated in live/replay operation.

### Post-2013

2013-10-04 to 2026-08-14: **6.49% CAGR, 0.69 Sharpe, -21.32% max drawdown, 33.23% equity exposure**.

## Data provenance

- S&P 500: weekly Friday last price level.
- Commercial paper: NBER/Federal Reserve splice used throughout the Freeburg reconstruction.
- Historical earnings yield: contemporaneous S&P observations preserved in FRASER *Economic Indicators* material; PIT reconstruction admits values only once publication/archival availability permits.
- Post-historical fundamentals: archived S&P earnings observations with explicit availability dates.

The clean strategy consumes an already point-in-time earnings-yield event stream and contains no interpolation or publication-date logic itself.


**[Year-by-year OOS comparison: annual return, excess Sharpe, Calmar and maximum drawdown vs S&P buy-and-hold and weekly-rebalanced 60/40](reports/README.md)** (2014–2025 full years; 2026 YTD). The 60/40 uses S&P total-return approximation plus AGG adjusted closes.
