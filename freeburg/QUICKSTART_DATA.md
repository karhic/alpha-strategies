# Freeburg data: fastest reproducible path

The strategy rules and existing historical replication have **not** been redesigned. This is the user-side **data acquisition and validation** route. It is not yet an exact fully free six-sleeve source build. In particular, **Heine's proprietary Dow bond and CRB histories remain unresolved**.

## Fresh download on a clean machine

From this repository's root:

```bash
python -m pip install -r freeburg/requirements-data.txt

# The user's explicit opt-in confirms they have reviewed the price provider's terms.
# No downloaded Yahoo/FRED data are committed back to the repository.
python -m freeburg.bootstrap \
  --output-dir local/freeburg-fresh-001 \
  --enable-yahoo-spx \
  --govinfo-start 2010-09 --govinfo-end 2026-09
```

The bootstrap downloads actual Federal Reserve H.15, NBER macrohistory, and Yahoo S&P closing observations (opt-in only), as well as month-by-month official GovInfo Economic Indicators tables. Outputs and SHA-256 provenance manifests stay under `local/` (git-ignored). Change the output path for a newly acquired snapshot.

**Prime/Discount (optional FRED key):** FRED API access requires the user's *own* key. The legacy-reproduction discount source is `INTDSRUSM193N` (IMF-origin); the official Fed H.15 administrative rate is a **different series**, not an exact substitution. FRED also hosts third-party sources with individual terms.

```bash
export FRED_API_KEY='your-own-key'
python -m freeburg.tools.download_fred --output-dir local/fred-prime-discount
python -m freeburg.prime_discount.build_fed_public_events \
  --prices local/freeburg-fresh-001/spx/spx_weekly.csv \
  --fred-prime-json local/fred-prime-discount/DPRIME.json \
  --fred-discount-json local/fred-prime-discount/INTDSRUSM193N.json \
  --output local/prime_discount_events.jsonl
```

Documentation: https://fred.stlouisfed.org/docs/api/fred/series_observations.html

## Rebuild the government fundamentals, without PDFs

```bash
python -m freeburg.tools.govinfo_vintages \
  --xls-dir local/freeburg-fresh-001/govinfo \
  --metadata-cache-dir local/freeburg-mods \
  --output local/govinfo_first_observed_vintages.csv

python -m freeburg.tools.govinfo_weekly_spx \
  --source-dir local/freeburg-fresh-001/govinfo \
  --output local/govinfo_weekly_average_proxies.csv
```

**Be precise about meanings:** The official index observations in this table are *weekly averages*, **not** Friday closes. Its S&P earnings and dividend tables contain vendor-derived observations. GovInfo's archival record-creation date is a conservative *scenario* for data availability, **not definitive original release timing**. Missing issues and suspicious labels are flagged. These outputs do not automatically replace the frozen Freeburg benchmark.

## Verify the original live/replay strategy implementation

If the connected runtime is installed separately:

```bash
python -m pip install -e /path/to/causal-trading-engine
python -m freeburg.primas.build_historical_events
python -m freeburg.triple40.build_historical_events
python freeburg/primas/run_replay.py
python freeburg/triple40/run_replay.py
```

These existing builders fetch their own inputs and should not be mistaken for the strict single-snapshot, user-opt-in `bootstrap` pipeline. Market source terms still apply.

## Actual integration tests from 2026-10-11

- Fresh S&P `^GSPC`: **14,315 daily / 2,963 weekly** observations, January 1970–October 2026; compared to the frozen Pu Shen price column on **2,959 overlapping weeks: 0 price mismatches, 0 weekly 52-MA-state disagreements**. This source reproduces itself exactly; it is not an independent vendor verification.
- Fresh S&P plus saved FRED JSON recreates original 1970–2013 Prime/Discount inputs at matching dates: **0 divergent rate/price levels or decisions**, among **2,234 signal-eligible weeks**. Fresh FRED API downloads require the user's own key and were **not tested end-to-end**.
- Official GovInfo `2010-09`–`2026-09` issue range: **191/193 official spreadsheet issues** downloaded and parsed after fixing mixed XLS/XLSX formats, footnoted rows and header layouts. **2 issues remained unavailable in the sampled XLS endpoint**. 191 valid issues yielded **2,605 individual monthly observations**, reduced to **264 period/indicator first-observed values**, 191 dividend and 73 earnings observations under the first-seen convention.
- GovInfo weekly-average proxy: **951 source rows / 825 unique Friday labels**, with **two anomalous weekly date labels quarantined** (2013-01 and 2023-05). A separate price audit flagged an obviously discrepant 2013 S&P observation.
- The existing causal-trading-engine successfully ran **Primas, Triple-40, Pu Shen, Competitive Returns and Prime/Discount** decision-only replays. The first two replays were built with fresh source requests; the remaining source histories were from existing validated/frozen files or fresh S&P plus saved FRED.
- **16 local Python tests passed**; GitHub CI covers the same test family.

## What still blocks a fully fresh free six-sleeve build?

1. Restore/reuse the already researched **1970–2010 FRASER** earnings/dividend source archive, with clear distributability and availability conventions. Do **not** restart OCR/LLM research.
2. Integrate post-2010 fundamentals using the established `EPS / weekly SPX * 100` construction and verified as-of logic; then verify decisions and performance against the existing legacy/PIT fingerprints.
3. Produce truly original-release-timestamp PIT evidence or label publication timing assumptions; an archive creation date is *not* proof of first release.
4. Obtain or classify Heine's unavailable exact bond/commodity source series.
5. Resolve redistribution and commercial-use permissions where third-party inputs are involved.

**Release principle:** ship benchmark reproduction and source-acquisition research as separate explicitly labelled modes. Never claim that an approximate or legally ambiguous vendor dataset is a verified exact free/PIT replication.
