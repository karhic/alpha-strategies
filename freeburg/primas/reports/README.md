# Primas: Year-by-year out-of-sample comparison

**2014–2025: full calendar years. 2026: partial year through 7 August 2026 (32 weekly observations).** All figures are from the existing 90-day-lag Freeburg out-of-sample research implementation, with a separately downloaded AGG adjusted-close bond benchmark.

For readability, each metric gets its **own three-column comparison table**. The full underlying machine-readable data, including week counts, are in [`annual_comparison_2014_2026.csv`](annual_comparison_2014_2026.csv).

## Annual return

| Year | Primas | S&P buy & hold | 60/40 |
|---|---:|---:|---:|
| 2014 | +0.9% | +14.5% | +11.3% |
| 2015 | -0.4% | +1.3% | +1.1% |
| 2016 | +0.5% | +13.8% | +9.4% |
| 2017 | +1.1% | +22.8% | +14.5% |
| 2018 | +2.1% | -6.0% | -2.9% |
| 2019 | +14.4% | +30.2% | +21.4% |
| 2020 | +10.0% | +18.3% | +14.7% |
| 2021 | +26.6% | +26.3% | +13.8% |
| 2022 | +2.0% | -15.4% | -12.8% |
| 2023 | +5.2% | +22.5% | +14.2% |
| 2024 | +9.9% | +28.2% | +17.3% |
| 2025 | +8.8% | +16.8% | +13.4% |
| 2026 (YTD) | +10.6% | +14.3% | +8.4% |

## Excess Sharpe

| Year | Primas | S&P buy & hold | 60/40 |
|---|---:|---:|---:|
| 2014 | 0.19 | 1.25 | 1.72 |
| 2015 | -0.15 | 0.16 | 0.17 |
| 2016 | — | 1.06 | 1.21 |
| 2017 | — | 3.38 | 3.69 |
| 2018 | — | -0.36 | -0.40 |
| 2019 | 1.69 | 2.30 | 2.87 |
| 2020 | 0.57 | 0.68 | 0.74 |
| 2021 | 2.25 | 1.96 | 1.76 |
| 2022 | — | -0.70 | -0.95 |
| 2023 | — | 1.19 | 0.91 |
| 2024 | 0.48 | 1.69 | 1.38 |
| 2025 | 0.44 | 0.75 | 0.89 |
| 2026 (YTD) | 1.08 | 1.45 | 1.14 |

## Calmar

| Year | Primas | S&P buy & hold | 60/40 |
|---|---:|---:|---:|
| 2014 | 0.30 | 2.41 | 3.72 |
| 2015 | -0.18 | 0.13 | 0.20 |
| 2016 | — | 1.62 | 2.12 |
| 2017 | — | 11.07 | 13.17 |
| 2018 | — | -0.35 | -0.30 |
| 2019 | 2.50 | 4.69 | 6.78 |
| 2020 | 0.76 | 0.58 | 0.70 |
| 2021 | 6.94 | 6.84 | 5.44 |
| 2022 | — | -0.69 | -0.67 |
| 2023 | — | 2.30 | 1.87 |
| 2024 | 2.08 | 5.23 | 4.16 |
| 2025 | 0.78 | 1.00 | 1.41 |
| 2026 (YTD) | 2.14 | 2.90 | 2.57 |

## Maximum drawdown

| Year | Primas | S&P buy & hold | 60/40 |
|---|---:|---:|---:|
| 2014 | -3.1% | -6.0% | -3.0% |
| 2015 | -2.0% | -9.4% | -5.6% |
| 2016 | 0.0% | -8.5% | -4.5% |
| 2017 | 0.0% | -2.1% | -1.1% |
| 2018 | 0.0% | -17.1% | -9.9% |
| 2019 | -5.8% | -6.4% | -3.2% |
| 2020 | -13.2% | -31.7% | -21.2% |
| 2021 | -3.8% | -3.8% | -2.5% |
| 2022 | 0.0% | -22.5% | -19.0% |
| 2023 | 0.0% | -9.8% | -7.6% |
| 2024 | -4.7% | -5.4% | -4.2% |
| 2025 | -11.3% | -16.9% | -9.5% |
| 2026 (YTD) | -8.4% | -8.4% | -5.5% |

## Definitions and interpretation

- **Annual return:** geometrically compounded weekly returns in the calendar year. No rebalancing across the year beyond the normal strategy and benchmark schedules.
- **Excess Sharpe:** mean weekly strategy return minus contemporaneous nonnegative 3-month Treasury-bill carry, divided by weekly standard deviation of excess returns, annualized by `sqrt(52)`. This is intentionally distinct from the raw-return Sharpe in the main sleeve README. Reported as **—** if weekly excess-return volatility is below 0.15% to avoid mathematically huge, economically meaningless ratios in virtually cash-only years.
- **Calmar (within-year):** full-year compounded return divided by absolute maximum drawdown *within that year* (equity curve resets to 1.0 at the start of every year). For 2026 YTD, numerator is annualized YTD return. If no within-year drawdown occurs, ratio is **—** (undefined), not infinity. Yearly Calmar is unstable and not comparable to conventional 3-year rolling Calmar; use principally as a descriptive diagnostic.
- **Max drawdown:** within-year trough from that year’s previous peak, including a starting 1.0 baseline; not the ongoing drawdown inherited from a previous December.
- **Primas:** original weekly signal and historical return approximation, including weekly dividend-yield accrual when long and commercial-paper carry when out.
- **S&P buy & hold:** identical weekly S&P return and approximated dividend accrual used by the strategy; not a particular ETF’s after-fee total return.
- **60/40:** 60% of that same S&P weekly total-return approximation + 40% of **AGG** adjusted-close total return, rebalanced to 60/40 **weekly**. AGG is a tradable broad U.S. aggregate-bond proxy, not a 40% long-Treasury allocation; ignores transaction costs and AGG management fees insofar as adjusted NAV history embeds them.
- **Data provenance:** Freeburg original historical signal research from `edge-research-scratchpad/research/freeburg/test_post2013_and_leverage_v4.py` (90-day earnings/dividend reporting lag where relevant); AGG adjusted close via Yahoo chart history, fetched for this diagnostic. The benchmark is free-to-access but third-party vendor redistribution permissions remain subject to provider terms.
- **Sample mechanics:** weekly observations are indexed to the decision Friday with the following close-to-close holding-week return. Consequently a return indexed to late December may settle in early January. This report groups returns by the **decision-week date** to stay aligned with the backtest.
- **Caution:** these are modelled historical returns without a full slippage/taxes implementation; annualization at weekly frequency can be volatile. 2026 is **not** a complete calendar year.

A number of Primas years are virtually cash-only, so **Sharpe and Calmar can be misleading or undefined**. That is important information, not a missing-data bug.

## Regenerating

Raw reproducibility relies on the original scratchpad’s OOS research and a user-local download of AGG; this tabulation is not yet standalone under `freeburg/` alone. Source snapshots are excluded from Git.
