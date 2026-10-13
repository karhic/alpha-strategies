## One-command public-data historical attempt (Docker)

```bash
docker compose run --rm freeburg freeburg.tools.public_reproduce
```

This is **on-demand** and separate from the default forward signal monitor. It downloads available original S&P Wayback workbooks (1988–2022), fills 2022–2025 quarterlies using the **same** public AlphaQuery EPS and index-derived dividends as the live monitor, acquires S&P 500 closes, Fed H.15 and FRED histories, and checks all 2,632 decisions through the canonical causal engine. The command makes a full 2014–August 2026 portfolio calculation when all providers respond and pass the checks. Source snapshots, failed-stage progress and results are persisted under `/data/historical/public-rebuild` in the Docker volume. To start anew after a provider failure, choose a different empty `--output-dir` or intentionally clean that *historical* subfolder.

**Evidence / limitations:** All required public-source inputs have been built and their historical results cross-compared successfully on the research VPS, but the entire network fetch has **not** been validated as one successful fresh-container run; Internet Archive availability is not guaranteed. Data from retrospective vendor snapshots may have been revised. Strict original-publication PIT timing and real executable Friday-after-close fills remain unverified, and this command does not claim them. Data suppliers may impose access/redistribution terms; the tool downloads locally instead of adding vendor content to Git. No brokerage credentials are needed.

# Reproduce Freeburg 4: exact research-model calculations

**Causal-engine parity:** The actual four strategy classes now reproduce **2,632/2,632 decisions** against the frozen research model (no mismatches), with separately hashed canonical ledgers. This is computational parity, not proof of historically available data or executable fills. Run `python -m freeburg.tools.verify_causal_parity --help` for the full audit CLI.

**Latest audited rerun and its certification limits:** [12 October reproducibility audit](REPRODUCIBILITY_AUDIT_2026-10-12.md). The default delayed-BAA return model is computationally reproducible with the original quarterly CSV; it is **not** an independently release-vintage-certified or next-session-tradable performance series.

**Updated 12 October 2026.** A standalone source-to-returns calculator now
exists **inside this repository**, independent of the private
`edge-research-scratchpad` Python code. It regenerates 658 Friday-stamped
weekly risk-on decisions, sleeve returns, equal-weight portfolio, S&P and 60/40
benchmark results, annual metric CSV and a source/assumptions manifest.

**Important: this is reproducibility of the *modeled research computation*,**
not a full independent point-in-time or execution audit. The underlying
historical S&P quarterly table was originally assembled from later captured
vendor workbooks, and the precise quarterly values may include later revisions.

**New acquisition path:** [Re-acquire S&P earnings/dividends from the 21 documented Wayback snapshots](SP500_QUARTERLY_ACQUISITION.md). In the first live validation, 17 snapshots yielded 138/151 quarterly records, all 138 numerically identical to the original research archive. The four latest snapshots remain inaccessible in this run, so **a full clean-machine download is not yet demonstrated**.

## Reproduction with the original research inputs

Prerequisites: Python 3.12+, `pandas`, `numpy`, `requests`. No private
scratchpad code or local trading-engine checkout is required for this
*return-model calculation*.

Start from the repository root:

```bash
python -m pip install -r freeburg/requirements-data.txt

# 1. Prepare the two frozen, previously published research-source tables.
python -m freeburg.tools.prepare_four_frozen_inputs \
  --output-dir local/four/frozen

# 2. Separately download the required monthly Baa and AGG prices/returns,
# after checking the providers' terms. Keep these files local.
python -m freeburg.tools.download_four_market_extras \
  --output-dir local/four/market --accept-provider-terms

# 3. Supply the historical S&P quarterly archive previously assembled
# from independently captured S&P/Wayback workbooks. This CSV must contain
# quarter_date, as_reported_eps, dividends_per_share. Its exact filename here
# is illustrative; the original remains in the researcher's scratchpad.
cp /path/to/quarterly_first_observed_actual.csv local/four/quarterly.csv

# 4. Run the more conservative Baa month-END research-timing scenario.
python -m freeburg.tools.reproduce_four_from_sources \
  --weekly-prices local/four/frozen/weekly_prices.csv \
  --macro local/four/frozen/macro.csv \
  --quarterly local/four/quarterly.csv \
  --baa-monthly local/four/market/fred_baa_monthly.csv \
  --agg local/four/market/agg_weekly_forward.csv \
  --baa-availability month-end \
  --lag-days 90 \
  --output-dir local/four/reproduced-month-end
```

Expected using **the original archived source snapshots and the matching
October 2026 provider data**, through Friday 7 August 2026:

| Scenario | Freeburg 4 CAGR | Max DD | Terminal wealth |
|---|---:|---:|---:|
| Month-end Baa (recommended diagnostic) | **8.7174%** | **−19.1981%** | **2.8795×** |
| Original research month-start Baa (**lookahead**) | **9.2138%** | **−19.1981%** | **3.0504×** |

To rebuild the historical **9.21% original** for audit rather than live/PIT
claims, repeat step 4 using `--baa-availability month-start`, and a
different `--output-dir`. **Do not silently substitute it for the
month-end result or call it point-in-time clean.**

Outputs are `weekly_decisions.csv`, `weekly_returns.csv`,
`annual_comparison.csv`, and `run_manifest.json`. The manifest includes
input conventions and the SHA-256 digest of the resulting weekly-return
file. The published top-level 9.21% and annual tables use the
**lookahead-contaminated original research model**, clearly labelled.

## Exact CSV requirements

- `weekly_prices.csv`: Friday date, `spx` index price close, `cp`
  3-month commercial-paper annual interest percent, with pre-2014 lookback.
- `macro.csv`: Friday date, `tbond_10y`, `tbill_3m`, `cpi` values
  (pre-2014 lookback mandatory). The frozen mode provides these.
- `quarterly.csv`: `quarter_date` (calendar quarter end),
  `as_reported_eps`, `dividends_per_share` (quarterly components).
  The TTM series is calculated as the trailing four quarters and becomes
  visible after the selected lag.
- `fred_baa_monthly.csv`: `observation_date,BAA` (monthly yield,
  annual percent). The *observation month* is distinct from publication date.
- `agg_weekly_forward.csv`: `date,agg`, where `agg` is AGG adjusted
  close's next Friday-to-Friday total return, stamped on the **decision**
  Friday. The downloader performs this alignment.

Input snapshots must span enough dates to calculate moving averages before
2014 and next-week returns through August 2026. Missing inputs cause
an explicit error; they are never silently substituted.

## What a fresh clone can do **without** the private archive

- Run the 27+ automated project tests, acquire historical S&P closes,
  Fed H.15 rates, NBER commercial-paper data, and GovInfo economic tables.
- Run the deterministic calculation using its documented *user-supplied*
  five CSV inputs, without installing the separate research scratchpad.
- Prepare an exact copy of the already tracked frozen price/macro columns
  for the research snapshot, then locally download the Baa and AGG
  histories if the providers remain accessible.

### Remaining clean-room limitation

**The original S&P quarterly first-observed CSV is not licensed/cleared
for direct redistribution and is not included in the public repository.**
Nor does our existing GovInfo downloader automatically recover precisely the
same quarterly as-reported EPS/dividend sequence from the historical
Wayback captures. An unaffiliated user currently has to independently obtain
a conforming historical quarterly source. Different vintages can produce
different trading decisions, which are genuine model sensitivity, not a
software failure.

**Therefore, an unaffiliated user still cannot necessarily obtain the
*exact same 9.21%/8.72% headline* from nothing but a clone and downloads.**
We have removed the *private research code* dependency and proved that
source-to-return reproduction works using the original source CSV, but
**the source-archive acquisition remains an external requirement**.

The previously released `reproduce_available` command checks historical
*decision-ledger logic*; it does **not** reproduce the OOS return series.
It requires the separate causal-trading-engine package and frozen/available
event streams. The standalone calculator here implements the same rules as
ordinary vectorized Python with explicit input CSVs, so it is independent of
that execution engine, but not a substitute for real order fills.

## Known credibility limits

- Triple-40's original monthly Baa month-start assumption used future
  intra-month observations. The month-end and following-month scenarios
  remove that specific lookahead **mechanism** but are not certified release
  timestamps.
- Quarterly EPS/dividends in archived retrospective workbooks may be
  revised. A fixed 90-day lag is **not a source-vintage guarantee**.
- CPI frozen values are not independently verified original-release vintages.
- Friday-stamped signal inputs and ideal Friday close return accounting
  do not prove tradability. Transaction costs/taxes omitted.
- The stock total-return series uses index prices plus a dividend-yield
  weekly accrual approximation, not actual SPY ETF distributions.

This is an honest and rerunnable **research reproduction**, with provenance
and sensitivity limitations surfaced rather than concealed.
