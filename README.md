# Freeburg — historical market timing, rebuilt and running live

**A 2013 trading talk. Six decades-old systematic strategies. One independently runnable, auditable signal engine.**

This project started with Nelson Freeburg's 2013 MTA London presentation, **[Systematic Market Analysis: Expanding Opportunities and Managing Risk](https://cmtassociation.org/video/systematic-market-analysis-expanding-opportunities-and-managing-risk-2/)** ([CMT presenter/video archive](https://cmtassociation.org/presenter/nelson-freeburg/)). Freeburg revisited mechanical market-timing ideas originating with earlier researchers, many published years or decades before his talk, and tested them on US-market history reaching back to **1970**. His philosophy: **avoid devastating drawdowns so compounding has a better chance to produce strong long-run returns**. Avoiding a 50% loss, which takes a 100% gain merely to recover, can matter more than capturing every rally.

### Freeburg's original reported results, approximately 1970–September 2013

| Presented strategy | Reported compound annual return | Reported maximum drawdown |
|---|---:|---:|
| Primas | 12.1% | −16.4% |
| Triple-40 | 12.0% | −18.7% |
| Pu Shen earnings yield | 10.0% | −15.1% |
| Heine bond model | 11.5% | −4.8% |
| Competitive Returns | 12.9% | −35.9% |
| **Equal-weight six-model composite** | **11.3%** | **−11.7%** |

These are **Freeburg's own figures as transcribed from the presentation**, not returns earned by this code or verified live trading. The Prime/Discount slide showed an equity curve but the available reference did not establish a precise standalone CAGR and drawdown. Our historical reconstruction of Heine requires a proprietary bond-index history and is **not** claimed to be exact.

### What this repository adds

- **One strategy implementation for backtests and forward signals.** The four production signal classes execute through the same `causaltrader` engine whether processing a historical event stream or a newly captured snapshot. There is no separate, independently rewritten live strategy.
- **Real historical cross-checks:** the four-strategy **2014–August 2026** study replays **2,632 strategy-week decisions**, all matching an independent reference calculation; a ledger-to-portfolio-accounting bridge reproduces the stated simulated returns to numerical precision.
- **Causality guards and visible provenance:** timestamp-aware event availability, append-only decision/audit logs, input SHA-256 hashes, missing/stale-data rejection, and a corrected month-end Baa observation convention. An assumed **90-day** lag protects quarterly earnings/dividend inputs from obvious premature use. **Those protections do not prove that every archived historical value was the unrevised figure available at the assumed date**, so the historical study is not described as fully PIT certified.
- **A live-running, portable research monitor:** build and run with **one Docker Compose command**. The app independently acquires its *current* S&P, Federal Reserve/FRED, earnings and dividend feed data from publicly reachable providers; it computes, independently checks and records weekly **0/25/50/75/100% equity target weights**. **No brokerage or Twitter credentials required** for the default, non-trading container.

```bash
docker compose up -d --build
```

That command works from a checkout of this repository. The setup has been tested in a clean container, with persistent signals and source captures. Once the repository is publicly available, new users can obtain it with `git clone https://github.com/karhic/alpha-strategies.git`. [Docker quickstart and status commands](#run-the-current-signal-monitor-with-docker).

### What happened after Freeburg's talk? Our four-sleeve 2014–2026 study

The headline **four-sleeve** composite excludes Heine and Prime/Discount, whose exact historical inputs are not sufficiently resolved. With quarter-end-plus-90-day fundamentals and conservative month-end Baa timing, our **retrospective** results are:

| 2014–7 August 2026 | Freeburg 4 | S&P 500 | 60/40¹ |
|---|---:|---:|---:|
| CAGR | **8.72%** | 13.99% | 9.40% |
| Maximum drawdown | **−19.20%** | −31.68% | −21.18% |
| Terminal wealth, $1 → | **$2.88** | $5.24 | $3.12 |
| Weekly excess Sharpe² | **0.80** | 0.77 | 0.74 |

**Interpretation:** Freeburg mostly did what we hoped for drawdown control—particularly in **2018** and **2022**—but participated less in the powerful equity bull market, so CAGR lagged both buy-and-hold and 60/40. The **2020 COVID crash** exposed the limitation: Freeburg still drew down **19.2%** (S&P: **31.7%**). Perhaps a sudden exogenous shock is harder for slow-moving financial stress indicators to anticipate; that remains a hypothesis. Overall the rules look like **suggestive market-stress/regime indicators**, not a magic way to avoid every crash.

¹ 60% S&P / 40% AGG bond-ETF return proxy, weekly rebalanced. ² Weekly excess returns versus T-bill carry, annualized by √52. **All figures are simulated research results, not live audited P&L.** The historical model assumes completed-Friday-close returns and uses some retrospectively archived economic values; it is not fully independently PIT-certified or net of trading costs. [Audit details](freeburg/REPRODUCIBILITY_AUDIT_2026-10-12.md).

## How the strategy works

Four simple, independently evaluated sleeves each vote **risk-on (100% equities)** or **risk-off (cash)** every week. Each receives 25% of the composite's notional capital, so the overall equity target is **0%, 25%, 50%, 75% or 100%**; any remainder is in the model's cash proxy. The project generates a **target allocation**, not a price forecast or a short position.

| Sleeve | Risk-on condition (simplified) | What it tries to capture |
|---|---|---|
| **Primas** | S&P 500 above its 52-week moving average **and** commercial-paper yield below its 52-week average | Equity trend with easing short-term funding conditions |
| **Triple-40** | S&P 500 above its 40-week average **and** either Moody’s Baa yield or commercial-paper yield below its respective 40-week average | Equity momentum alongside improving credit/funding conditions |
| **Pu Shen** | S&P 500 above its level 50 weeks ago **and** the S&P earnings-yield-minus-commercial-paper spread wider than 50 weeks ago | Equity trend and relative equity valuation versus short-term funding |
| **Competitive Returns** | At least two of four indicators have fallen over 24 weeks: 10-year Treasury yield, three-month T-bill yield, S&P dividend yield, CPI | A broader cross-asset/macro regime vote |

The full decisions are in small Python strategy classes under [`freeburg/`](freeburg/). The live monitor runs the *same causal-strategy classes* and checks their output independently. This is a long/cash model, not a continuous volatility target, options hedge, or guarantee against sudden crashes.

## Annual breakdown and reproducibility details

**Evaluation:** 2014–2025 are full decision years; **2026 is year-to-date through 7 August**, not a complete year. Each table compares the conservative four-sleeve composite with S&P buy-and-hold and the weekly-rebalanced 60/40 comparator. Derived machine-readable annual metrics: [`freeburg4_month_end_annual_comparison_2014_2026.csv`](freeburg/reports/freeburg4_month_end_annual_comparison_2014_2026.csv).


### Annual compounded return

| Year | Freeburg 4 | S&P 500 | 60/40 |
|---|---:|---:|---:|
| 2014 | +8.9% | +14.5% | +11.3% |
| 2015 | +2.2% | +1.3% | +1.1% |
| 2016 | +4.8% | +13.8% | +9.4% |
| 2017 | +5.5% | +22.8% | +14.5% |
| 2018 | +1.6% | -6.0% | -2.9% |
| 2019 | +11.5% | +30.2% | +21.4% |
| 2020 | +13.0% | +18.3% | +14.7% |
| 2021 | +23.0% | +26.3% | +13.8% |
| 2022 | -2.5% | -15.4% | -12.8% |
| 2023 | +5.9% | +22.5% | +14.2% |
| 2024 | +16.4% | +28.2% | +17.3% |
| 2025 | +12.4% | +16.8% | +13.4% |
| 2026 YTD | +10.3% | +14.3% | +8.4% |


### Annual excess Sharpe ratio

| Year | Freeburg 4 | S&P 500 | 60/40 |
|---|---:|---:|---:|
| 2014 | 1.26 | 1.25 | 1.72 |
| 2015 | 0.49 | 0.16 | 0.17 |
| 2016 | 1.38 | 1.06 | 1.21 |
| 2017 | 2.43 | 3.38 | 3.69 |
| 2018 | -0.16 | -0.36 | -0.40 |
| 2019 | 1.21 | 2.30 | 2.87 |
| 2020 | 0.68 | 0.68 | 0.74 |
| 2021 | 2.08 | 1.96 | 1.76 |
| 2022 | -1.24 | -0.70 | -0.95 |
| 2023 | 0.35 | 1.19 | 0.91 |
| 2024 | 1.17 | 1.69 | 1.38 |
| 2025 | 0.74 | 0.75 | 0.89 |
| 2026 YTD | 1.39 | 1.45 | 1.14 |


### Annual Calmar ratio

| Year | Freeburg 4 | S&P 500 | 60/40 |
|---|---:|---:|---:|
| 2014 | 1.94 | 2.41 | 3.72 |
| 2015 | 1.24 | 0.13 | 0.20 |
| 2016 | 3.13 | 1.62 | 2.12 |
| 2017 | 5.62 | 11.07 | 13.17 |
| 2018 | 0.73 | -0.35 | -0.30 |
| 2019 | 2.11 | 4.69 | 6.78 |
| 2020 | 0.68 | 0.58 | 0.70 |
| 2021 | 6.71 | 6.84 | 5.44 |
| 2022 | -0.60 | -0.69 | -0.67 |
| 2023 | 6.30 | 2.30 | 1.87 |
| 2024 | 5.22 | 5.23 | 4.16 |
| 2025 | 1.28 | 1.00 | 1.41 |
| 2026 YTD | 2.88 | 2.90 | 2.57 |


### Maximum within-calendar-year drawdown

| Year | Freeburg 4 | S&P 500 | 60/40 |
|---|---:|---:|---:|
| 2014 | -4.6% | -6.0% | -3.0% |
| 2015 | -1.8% | -9.4% | -5.6% |
| 2016 | -1.5% | -8.5% | -4.5% |
| 2017 | -1.0% | -2.1% | -1.1% |
| 2018 | -2.2% | -17.1% | -9.9% |
| 2019 | -5.4% | -6.4% | -3.2% |
| 2020 | -19.2% | -31.7% | -21.2% |
| 2021 | -3.4% | -3.8% | -2.5% |
| 2022 | -4.2% | -22.5% | -19.0% |
| 2023 | -0.9% | -9.8% | -7.6% |
| 2024 | -3.1% | -5.4% | -4.2% |
| 2025 | -9.7% | -16.9% | -9.5% |
| 2026 YTD | -6.0% | -8.4% | -5.5% |


**Definitions.** Annual returns compound the simulated Friday-close-to-next-Friday-close periods and attribute each return to its decision Friday; the holding period can cross a calendar year. *Excess Sharpe* uses weekly return minus the nonnegative three-month T-bill benchmark, divided by weekly excess-return standard deviation and multiplied by √52. *Annual Calmar* divides that year's compounded return by the magnitude of its **within-year** maximum drawdown (2026 annualizes the YTD return first); it is **not** a conventional three-year Calmar. *Annual max drawdown* resets the starting wealth to 1 each January; the full-period maximum does not reset.

### What we tested for robustness

- **Corrected Baa timing.** The original monthly Baa series had been treated as available at the *start* of its observation month, which leaks information about the full month. Moving that observation to **month-end** lowers the four-sleeve modeled CAGR from **9.21% to 8.72%**. The original result is retained only as a labeled historical diagnostic, not the headline result. [Timing investigation](freeburg/TRIPLE40_MONTHLY_BAA_PIT_FINDING.md).
- **Fundamentals-release sensitivity.** Holding the month-end Baa convention constant and varying the assumed quarter-end EPS/dividend lag from **30 to 180 days** produced modeled composite CAGRs between **8.47% and 8.77%**. This is a sensitivity study, **not** confirmation that hindsight-revised figures existed on those dates. [Availability study](freeburg/FUNDAMENTAL_AVAILABILITY_ENVELOPE.md).
- **Late positioning stress.** Delaying every sleeve's position by a **whole additional week** changed CAGR from **8.70% to 8.32%** on the same 657-week aligned sample, while maximum drawdown increased from **−19.20% to −22.10%**. This is intentionally harsher than trading at the next market open, but does **not** substitute for a true next-session executable-price backtest. [Audit](freeburg/REPRODUCIBILITY_AUDIT_2026-10-12.md).
- **Implementation parity.** On the same fixed historical research inputs, all **2,632 of 2,632** decisions generated by the **four actual causal-engine strategy classes** matched the independently calculated research decisions. Reconstructing modeled sleeve and composite returns from those engine actions also matched to numerical precision. These checks establish *computational* reproducibility, not historical source-vintage certification. [Verification tool](freeburg/tools/verify_causal_parity.py).

## Data provenance and interpretation

This research tries to make assumptions and lineage inspectable, rather than hiding a backtest in a single performance number:

| Input family | Research or forward-feed route | Qualification |
|---|---|---|
| S&P levels and trade-return proxy | Historical weekly price series; user-side Yahoo downloads | Index-level weekly close returns, not audited SPY fills; provider redistribution terms apply |
| Treasury yields and commercial paper | Federal Reserve H.15, other historical macro snapshots | Some older observations are retrospectively processed; exact vintage/release-time coverage is incomplete |
| Moody’s Baa yields | FRED historical monthly series | **Month-end observation delay** used in headline scenario; actual historical first-release timestamps still require verification |
| Earnings and dividends | Archived S&P reports/Wayback/FRASER/GovInfo material; current data capture | **90 days after quarter-end** assumed in model; archived values can reflect subsequent revisions; original quarterly CSV not redistributed |
| Inflation / CPI | Historical macro/CPI sources | Historical vintages and their first release dates are not universally independently verified |
| Bond benchmark | User-downloaded AGG adjusted-close return series | ETF proxy, not a perfectly matched investable 60/40 implementation |

The original research table had a **lookahead error in Baa timing**, which this headline analysis corrects. Nevertheless, a fixed 90-day lag for EPS/dividends is *not evidence* that each exact retrospectively archived value existed 90 days after quarter-end. Likewise, a Friday signal calculated using a completed Friday close cannot actually be filled at that already-known closing price. Neither issue is concealed in the reported figures.

**Research result ≠ independently time-stamped investment track record.** The current audit establishes that the coded rules, decisions and stated *model accounting* agree; it does not prove independent historical data-vintage availability, transaction-cost-adjusted fills, or real investor performance. External archived quarterly source files remain necessary to reconstruct the exact historical numbers. See [reproducibility audit](freeburg/REPRODUCIBILITY_AUDIT_2026-10-12.md), [source-to-performance reproduction](freeburg/REPRODUCE_FOUR.md), and [S&P archive coverage](freeburg/SP500_QUARTERLY_ACQUISITION.md).

## Run the current signal monitor with Docker

The default package is a **standalone, read-only research signal monitor**, not an auto-trading bot. It downloads current market, macroeconomic, earnings and dividend inputs; keeps timestamped source snapshots and hashes; computes the four risk-on/off signals through the causal engine; checks them independently; and schedules subsequent refreshes. It persists results in a Docker volume. **No brokerage login, X/Twitter account or API keys are required for the default installation.**

After the release branch is merged into `main` and the repository made publicly readable:

```bash
git clone https://github.com/karhic/alpha-strategies.git
cd alpha-strategies
docker compose up -d --build
docker compose logs -f freeburg
docker compose run --rm freeburg freeburg.deploy.status
```

The first run collects a **retrospective history for indicator warm-up**; this is not an independently historical point-in-time backtest. The monitor retries transient upstream outages and rejects stale or inconsistent inputs rather than silently making up a signal. Compose schedules capture on weekday evenings and retains signal history across restarts. Use `docker compose down` to stop without deleting data; `docker compose down -v` **deletes** the named data volume.

**Reproducibility has two meanings here:** (1) a stranger can build the container and independently run the current research monitor, which was demonstrated in a clean-container test; (2) the entire 2014–2026 historical result can be rebuilt from contemporaneously available, independently licensed data. The latter is **not yet achieved**. Exact deterministic replay of the existing historical **model** is available with separately supplied source CSVs; see [instructions](freeburg/REPRODUCE_FOUR.md) and [engine-parity checks](freeburg/tools/verify_causal_parity.py).

## Forward operation, IBKR paper trading and X

The research VPS runs a **forward signal-capture service** with independent shadow verification, a Docker read-only monitor and separately gated scheduler jobs. One IBKR **paper** account is configured for an attempted Monday SPY target-weight rebalance, subject to broker permissions, source freshness, order-size caps and idempotency checks. **This is a paper-trading prototype, not production/live-money execution; successful order placement and fills should not be inferred from a scheduled timer.** The Docker demo has no order permission. [Paper workflow and operational gates](freeburg/deploy/AUTOPAPER.md) · [Docker monitor architecture](freeburg/deploy/DOCKER_OPERATIONS.md).

The X/Twitter publishing integration currently prepares signal drafts and is deliberately **not posting** without separately configured API access and explicit permission. [Publication setup](freeburg/deploy/AUTO_X.md). Neither broker credentials nor social-network credentials belong in Git. The forward signal record includes raw-source provenance and hashes for later inspection.

## Repository map and verification

- [`freeburg/{primas,triple40,pushen,competitive}/strategy.py`](freeburg/README.md): original, small, inspectable rules, plus per-sleeve research notes and annual reports ([Primas](freeburg/primas/reports/README.md), [Triple-40](freeburg/triple40/reports/README.md), [Pu Shen](freeburg/pushen/reports/README.md), [Competitive](freeburg/competitive/reports/README.md)). **Those older individual report tables reflect their original research conventions; they are not all regenerated for the corrected composite.**
- [`freeburg/tools/reproduce_four_from_sources.py`](freeburg/tools/reproduce_four_from_sources.py): source-CSV-to-signal-and-portfolio calculation; outputs weekly decisions, returns, annual tables and a hashed manifest.
- [`freeburg/tools/verify_causal_parity.py`](freeburg/tools/verify_causal_parity.py): full-period comparisons of the independent calculations with the actual four causal strategy classes, plus ledger-to-research-accounting checks.
- [`freeburg/deploy/`](freeburg/deploy/): forward data ingestion, independent signal check, scheduler, paper-trading prototype and optional X drafts.
- [`freeburg/tests/`](freeburg/tests/): fail-closed data-validation, strategy, deployment and reproduction checks.
- [`freeburg/RELEASE_STATUS.md`](freeburg/RELEASE_STATUS.md): status of the wider six-sleeve historical reconstruction, including unresolved Heine index sourcing and Prime/Discount data questions. The present README deliberately reports **four** sleeves only.

To run the repository's Python unit tests, install dependencies from [`freeburg/requirements-data.txt`](freeburg/requirements-data.txt), then run:

```bash
python -m unittest discover -s freeburg/tests -p 'test_*.py' -v
```

The current audit suite passed **52 tests** on the connected VPS. Test success does not remove the empirical historical data-vintage caveats above.

---

*Project type: independent open research and forward paper-trading prototype. Not investment advice. No representation of live audited returns, guaranteed drawdown protection, or market-beating CAGR.*
