# alpha-strategies

Systematic market-timing research and historical strategy replications. The [Freeburg project](freeburg/README.md) includes six documented timing sleeves; this report covers a **four-sleeve equal-weight composite**, excluding Prime/Discount and Heine. Five original strategy decision replays are operational; complete independent point-in-time sourcing and the exact Heine bond history remain unresolved.

## Equal-weight four-sleeve Freeburg composite — out-of-sample performance

**Portfolio:** 25% each in Primas, Triple-40, Pu Shen, and Competitive Returns, rebalanced weekly. **Comparisons:** S&P 500 buy-and-hold and 60% S&P / 40% AGG adjusted-close bond returns, rebalanced weekly.

**Sample:** January 3, 2014 through August 7, 2026 (658 weekly decision observations). The 2014–2025 rows are complete years; **2026 is YTD**.

### Full-period summary

| Metric | Freeburg 4 | S&P 500 | 60/40 |
|---|---:|---:|---:|
| CAGR | **9.21%** | 13.99% | 9.40% |
| Maximum drawdown | **−19.20%** | −31.68% | −21.18% |
| Terminal wealth | 3.05× | 5.24× | 3.12× |

### Annual returns

| Year | Freeburg 4 | S&P 500 | 60/40 |
|---|---:|---:|---:|
| 2014 | +8.8% | +14.5% | +11.3% |
| 2015 | +2.2% | +1.3% | +1.1% |
| 2016 | +5.1% | +13.8% | +9.4% |
| 2017 | +6.0% | +22.8% | +14.5% |
| 2018 | +2.2% | -6.0% | -2.9% |
| 2019 | +11.8% | +30.2% | +21.4% |
| 2020 | +13.0% | +18.3% | +14.7% |
| 2021 | +23.0% | +26.3% | +13.8% |
| 2022 | -1.0% | -15.4% | -12.8% |
| 2023 | +7.5% | +22.5% | +14.2% |
| 2024 | +17.7% | +28.2% | +17.3% |
| 2025 | +12.4% | +16.8% | +13.4% |
| 2026 YTD | +10.3% | +14.3% | +8.4% |

### Annual excess Sharpe ratios

| Year | Freeburg 4 | S&P 500 | 60/40 |
|---|---:|---:|---:|
| 2014 | 1.25 | 1.25 | 1.72 |
| 2015 | 0.51 | 0.16 | 0.17 |
| 2016 | 1.42 | 1.06 | 1.21 |
| 2017 | 2.48 | 3.38 | 3.69 |
| 2018 | 0.20 | -0.36 | -0.40 |
| 2019 | 1.25 | 2.30 | 2.87 |
| 2020 | 0.68 | 0.68 | 0.74 |
| 2021 | 2.08 | 1.96 | 1.76 |
| 2022 | -1.12 | -0.70 | -0.95 |
| 2023 | 1.30 | 1.19 | 0.91 |
| 2024 | 1.32 | 1.69 | 1.38 |
| 2025 | 0.74 | 0.75 | 0.89 |
| 2026 YTD | 1.39 | 1.45 | 1.14 |

### Annual Calmar ratios

| Year | Freeburg 4 | S&P 500 | 60/40 |
|---|---:|---:|---:|
| 2014 | 1.93 | 2.41 | 3.72 |
| 2015 | 1.28 | 0.13 | 0.20 |
| 2016 | 3.34 | 1.62 | 2.12 |
| 2017 | 6.09 | 11.07 | 13.17 |
| 2018 | 2.36 | -0.35 | -0.30 |
| 2019 | 2.17 | 4.69 | 6.78 |
| 2020 | 0.68 | 0.58 | 0.70 |
| 2021 | 6.71 | 6.84 | 5.44 |
| 2022 | -0.37 | -0.69 | -0.67 |
| 2023 | 10.81 | 2.30 | 1.87 |
| 2024 | 5.62 | 5.23 | 4.16 |
| 2025 | 1.28 | 1.00 | 1.41 |
| 2026 YTD | 2.88 | 2.90 | 2.57 |

### Maximum drawdown by calendar year

| Year | Freeburg 4 | S&P 500 | 60/40 |
|---|---:|---:|---:|
| 2014 | -4.6% | -6.0% | -3.0% |
| 2015 | -1.8% | -9.4% | -5.6% |
| 2016 | -1.5% | -8.5% | -4.5% |
| 2017 | -1.0% | -2.1% | -1.1% |
| 2018 | -0.9% | -17.1% | -9.9% |
| 2019 | -5.4% | -6.4% | -3.2% |
| 2020 | -19.2% | -31.7% | -21.2% |
| 2021 | -3.4% | -3.8% | -2.5% |
| 2022 | -2.7% | -22.5% | -19.0% |
| 2023 | -0.7% | -9.8% | -7.6% |
| 2024 | -3.1% | -5.4% | -4.2% |
| 2025 | -9.7% | -16.9% | -9.5% |
| 2026 YTD | -6.0% | -8.4% | -5.5% |

### Methodology and limitations

- **Annual returns:** compounded model returns over weekly close-to-next-close holding periods, attributed to the Friday *decision* date. A return attributable to a December decision may settle in January.
- **Excess Sharpe:** mean weekly return above contemporaneous nonnegative three-month Treasury-bill carry divided by weekly excess-return volatility, annualized by √52. Unlike the raw-return Sharpe shown in some sleeve summaries, this metric deducts the short-term cash benchmark. Extremely low-volatility ratios are withheld in the individual reports.
- **Annual Calmar:** yearly compounded return divided by maximum drawdown *within that calendar year*; for partial 2026, the YTD return is annualized in the numerator. It is **not** the conventional three-year rolling Calmar, and can be unstable when yearly drawdowns are tiny.
- **Annual max drawdown:** peak-to-trough within each year, resetting the starting equity curve to 1.0 every January. The full-period max drawdown above does **not** reset.
- **Portfolio accounting:** the four sleeves are held equally and rebalanced weekly. The 60/40 benchmark is rebalanced weekly. S&P returns use the same price-plus-dividend-accrual approximation as the Freeburg OOS research; the bond proxy is AGG adjusted-close total returns. No additional transaction costs or taxes are included.
- **Provenance:** the existing 90-day-lag post-2013 Freeburg research in [edge-research-scratchpad](https://github.com/karhic/edge-research-scratchpad), with an AGG historical series acquired for the comparison. This is simulated historical performance, **not** live audited performance or a fully certified independent point-in-time reproduction. Third-party historical market-data redistribution rights are not assumed.

**Individual annual reports:** [Primas](freeburg/primas/reports/README.md) · [Triple-40](freeburg/triple40/reports/README.md) · [Pu Shen](freeburg/pushen/reports/README.md) · [Competitive Returns](freeburg/competitive/reports/README.md).

**Reproduction tools and source notes:** [Freeburg data quickstart](freeburg/QUICKSTART_DATA.md) · [Release status](freeburg/RELEASE_STATUS.md). The annual portfolio statistics above use the same local weekly OOS research sample as the four individual sleeve reports.
