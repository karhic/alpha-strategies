# Pu Shen: Year-by-year out-of-sample comparison

**2014–2025 are complete calendar years; 2026 is YTD through 7 August 2026 (32 weeks).**

Four compact metric tables compare the sleeve with buy-and-hold and a weekly-rebalanced 60/40 portfolio. Machine-readable statistics: [annual comparison CSV](annual_comparison_2014_2026.csv).

## Annual return

| Year | Pu Shen | S&P buy & hold | 60/40 |
|---|---:|---:|---:|
| 2014 | +14.2% | +14.5% | +11.3% |
| 2015 | +5.1% | +1.3% | +1.1% |
| 2016 | +0.5% | +13.8% | +9.4% |
| 2017 | +1.1% | +22.8% | +14.5% |
| 2018 | +2.1% | -6.0% | -2.9% |
| 2019 | +7.1% | +30.2% | +21.4% |
| 2020 | +9.7% | +18.3% | +14.7% |
| 2021 | +10.1% | +26.3% | +13.8% |
| 2022 | -9.6% | -15.4% | -12.8% |
| 2023 | +5.2% | +22.5% | +14.2% |
| 2024 | +7.3% | +28.2% | +17.3% |
| 2025 | +16.8% | +16.8% | +13.4% |
| 2026 (YTD) | +16.8% | +14.3% | +8.4% |

## Excess Sharpe

| Year | Pu Shen | S&P buy & hold | 60/40 |
|---|---:|---:|---:|
| 2014 | 1.79 | 1.25 | 1.72 |
| 2015 | 1.22 | 0.16 | 0.17 |
| 2016 | — | 1.06 | 1.21 |
| 2017 | — | 3.38 | 3.69 |
| 2018 | — | -0.36 | -0.40 |
| 2019 | 0.62 | 2.30 | 2.87 |
| 2020 | 0.53 | 0.68 | 0.74 |
| 2021 | 1.05 | 1.96 | 1.76 |
| 2022 | -1.07 | -0.70 | -0.95 |
| 2023 | — | 1.19 | 0.91 |
| 2024 | 0.36 | 1.69 | 1.38 |
| 2025 | 0.75 | 0.75 | 0.89 |
| 2026 (YTD) | 1.77 | 1.45 | 1.14 |

## Calmar

| Year | Pu Shen | S&P buy & hold | 60/40 |
|---|---:|---:|---:|
| 2014 | 3.50 | 2.41 | 3.72 |
| 2015 | 6.22 | 0.13 | 0.20 |
| 2016 | — | 1.62 | 2.12 |
| 2017 | — | 11.07 | 13.17 |
| 2018 | — | -0.35 | -0.30 |
| 2019 | 1.10 | 4.69 | 6.78 |
| 2020 | 0.45 | 0.58 | 0.70 |
| 2021 | 3.01 | 6.84 | 5.44 |
| 2022 | -0.85 | -0.69 | -0.67 |
| 2023 | — | 2.30 | 1.87 |
| 2024 | 2.82 | 5.23 | 4.16 |
| 2025 | 1.00 | 1.00 | 1.41 |
| 2026 (YTD) | 4.49 | 2.90 | 2.57 |

## Maximum drawdown

| Year | Pu Shen | S&P buy & hold | 60/40 |
|---|---:|---:|---:|
| 2014 | -4.1% | -6.0% | -3.0% |
| 2015 | -0.8% | -9.4% | -5.6% |
| 2016 | 0.0% | -8.5% | -4.5% |
| 2017 | 0.0% | -2.1% | -1.1% |
| 2018 | 0.0% | -17.1% | -9.9% |
| 2019 | -6.4% | -6.4% | -3.2% |
| 2020 | -21.3% | -31.7% | -21.2% |
| 2021 | -3.3% | -3.8% | -2.5% |
| 2022 | -11.3% | -22.5% | -19.0% |
| 2023 | 0.0% | -9.8% | -7.6% |
| 2024 | -2.6% | -5.4% | -4.2% |
| 2025 | -16.9% | -16.9% | -9.5% |
| 2026 (YTD) | -6.4% | -8.4% | -5.5% |

## Definitions and interpretation

- **Return:** compounded weekly returns indexed to the decision Friday; underlying holding returns are close-to-next-close and may settle in the next calendar year.
- **Excess Sharpe:** mean of weekly returns minus contemporaneous nonnegative 3-month Treasury-bill carry, divided by standard deviation of those excess returns and multiplied by sqrt(52). This differs from raw-return Sharpe in the main README. Em dashes indicate weekly excess-return volatility below 0.15%, suppressing spurious huge ratios in cash-only years.
- **Calmar:** annual compounded return / absolute maximum within-year drawdown, with the 2026 YTD return annualized before division. Zero drawdown makes the ratio undefined. This is an annual diagnostic, NOT a conventional 3-year rolling Calmar.
- **Max drawdown:** calculated within each calendar year, resetting wealth to 1.0 at the year boundary; outstanding drawdowns from preceding years are excluded.
- **S&P buy & hold:** same existing Freeburg OOS S&P weekly price-return-plus-dividend-accrual approximation, not ETF after-fee total return.
- **60/40:** 60% the same S&P return plus 40% AGG adjusted-close total returns, rebalanced weekly; AGG is a broad US aggregate-bond ETF proxy rather than a Treasury-only index. Trading costs and taxes excluded.
- **Method/data:** the original 90-day-lag post-2013 OOS research in edge-research-scratchpad/research/freeburg/test_post2013_and_leverage_v4.py. The AGG series was obtained from Yahoo Finance for this diagnostic; rights to raw provider data are not assumed.
- **2026:** through August 7, not a full year.

Cash-heavy years often have undefined or misleadingly extreme annual risk-adjusted ratios.

## Rebuild

Use the available Freeburg tools build_annual_oos_inputs and render_annual_oos with the user's own scratchpad checkout and locally retrieved AGG observations. Source prices are not committed.
