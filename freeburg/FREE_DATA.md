# Free-data acquisition and publication audit (2026-10-11)

**Status: prototype; not a cleared one-command reproduction.** Free to access does not imply permission to redistribute or use commercially. Do not publish the existing mixed-origin CSVs unchanged.

| Sleeve | Free alternative | Outstanding |
| --- | --- | --- |
| Primas | Fed H.15 + NBER CP; user-supplied S&P closes | Confirm price source access/rights; replay parity |
| Triple-40 | Fed/NBER + Moody's Baa through H.15/FRED | Moody's third-party rights, price data parity |
| Pu Shen | Extracted FRASER Economic Indicators; GovInfo Excel tables 1995+ | Archived S&P workbook and S&P rights, publication-time validation |
| Competitive | FRASER/GovInfo dividends, official CPI/Treasury | S&P-derived figures, publication-time validation |
| Prime/Discount | Official H.15 historical prime and discount series | Build an alternative from Fed records and compare decisions to frozen reference |
| Heine | Fed yields and archived DJ20/Utilities/CRB digitizations | No exact validated free DJ20 total-return reconstruction |

The original research archive already has FRASER earnings-yield quarterly and dividend-yield weekly first-publication files, plus scripts to acquire and parse old publications. Preserve those costly reconstructions; do not redo archival OCR.

## New user-side utility

`freeburg/tools/free_data.py` accepts **locally obtained** daily/weekly `Date,Close` or `date,spx` files. It never scrapes or redistributes market data.

```bash
python freeburg/tools/free_data.py import-prices --input local/spx.csv --output local/spx_weekly.csv
python freeburg/tools/free_data.py compare-prices --candidate local/spx_weekly.csv --baseline freeburg/prime_discount/data/spx_weekly_2026-08-07.csv
```

The comparator reports overlap, basis-point discrepancies, and changed 52-week S&P-versus-moving-average decisions. The reference CSV is present in the *private* research branch but must be replaced or cleared before publishing.

GovInfo (official Economic Indicators spreadsheets) is a promising 1995+ source. A page is not necessarily the same across monthly issues. After identifying an actual **Common Stock Prices and Yields** granule, inspect first, and only then extract verified columns and publication date:

```bash
python freeburg/tools/free_data.py govinfo-urls --issue 2012-10 --page 31
python freeburg/tools/free_data.py govinfo-download --issue 2012-10 --page 31 --output local/table.xls
pip install pandas xlrd openpyxl
python freeburg/tools/free_data.py govinfo-preview --input local/table.xls
python freeburg/tools/free_data.py govinfo-extract --input local/table.xls --output local/yields.csv --source-url <verified-official-granule-url> --published-on <verified-YYYY-MM-DD> --period-col <N> --dividend-col <N> --earnings-col <N>
```

The date and columns are intentionally required. Outputs are **preliminary extracts**, not verified point-in-time economic events. Direct government table access was not live-tested from the execution environment.

## Rights and source notes

- FRASER calls *Economic Indicators* “No Copyright – United States,” but S&P-derived tables may retain third-party rights. Clear the constituent columns and origins.
- GovInfo's official page: https://www.govinfo.gov/help/econi
- FRASER publication: https://fraser.stlouisfed.org/title/economic-indicators-1
- FRED terms (series-specific third-party restrictions): https://fred.stlouisfed.org/legal/
- Moody's Baa: https://fred.stlouisfed.org/series/BAA
- S&P market prices sourced from Yahoo should not be bundled without permission.
- Stooq offers no-cost manually accessible historical data, **not** automatically redistribution/commercial-use permission; do not scrape it by default.
- Pinnacle is an optional historical comparison, not a required purchase.

## Non-negotiable release gates

1. Audit every column of the current composite historical CSVs for third-party rights.
2. Confirm real GovInfo XLS files, actual table layouts, and real publication dates. Compare to archived FRASER vintage rows.
3. Independently download authorised price data and compare weekly levels and strategy decisions.
4. Add the Fed-only Prime/Discount alternative and compare its 1970–2013 decisions and performance.
5. Heine is **PROXY_UNVERIFIED** until bond history is accurately reconstructed.
6. Ship legally distributable sample data separately from user-supplied historical inputs.

The tools are for reproducible validation, **not** a legal opinion or proof that vendor data may be redistributed.

## Verified source probe (2026-10-11)

A live GET from `https://www.govinfo.gov/content/pkg/ECONI-2011-10/xls/ECONI-2011-10-Pg31.xls` returned HTTP **200**, 39,424 bytes, genuine OLE Excel signature. Parsed locally with `pandas.read_excel(..., header=None)`: **41 rows × 10 columns**. The spreadsheet title is **Common Stock Prices and Yields**. Source columns are:

- column **0**: Period;
- column **6**: Standard & Poor's composite price index;
- column **8**: dividend/price ratio;
- column **9**: earnings/price ratio.

Concrete example values in the sheet: **2010: Oct.** dividend ratio 1.97, earnings blank; **2011: Jan.** dividend ratio 1.84, earnings blank; **2011: Mar.** dividend ratio 1.90 and earnings ratio 6.13. Dots (`......`) denote missing observations, not zeros. Its rows include annual historical values and a rolling monthly window: distinguish them from contemporaneous observations; never backdate later publication vintages.

This confirms **GovInfo's XLS avenue really works**, not merely that a speculative URL can be assembled. It **does not** establish the actual public-release date of the October 2011 issue, a systematic spreadsheet page/granule mapping for other years, or redistribution clearance for S&P-derived content.

The converter handles month labels ending with periods, e.g. `2010: Oct.` and `Nov.`. To inspect this verified page locally:

```bash
python freeburg/tools/free_data.py govinfo-download --issue 2011-10 --page 31 --output local/econi-2011-10-p31.xls
python freeburg/tools/free_data.py govinfo-preview --input local/econi-2011-10-p31.xls --rows 35
```

Keep extracted GovInfo rows separate from the frozen research inputs until their publication dates and signal implications have been validated.

## Integration test results (2026-10-11, VPS)

- GitHub Actions `Freeburg free-data utilities`: **successful** (two successful workflow runs).
- VPS local standard-library tests: **4 passed**. The prior claim of “six local tests” was mistaken; the test module contains four.
- Real GovInfo XLS: October 2011 page 31 **HTTP 200, valid XLS, 41 × 10**; September 2020 page 31 also valid. **Tests for 2000-10, 2005-10, 2009-10 and 2010-05 returned HTML, not XLS**, despite HTTP 200. Therefore *GovInfo access is demonstrably inconsistent across old issues*. The header-signature guard correctly prevents falsely accepting HTML as a spreadsheet. GovInfo's format should not be advertised as continuously available since 1995.
- Stooq HTTP endpoint for S&P 500 returned a **JavaScript browser verification page**, not CSV. No bypass attempted; manual authorised downloads remain the fallback.
- **Fed H.15 Prime/Discount alternative**: constructed **9,544 DataEvents / 2,386 weekly decision events** from actual archived Fed H.15 series with a frozen S&P price CSV. This is a syntactic build, **not** verified decision parity.
- **Critical parity discovery:** In a direct 50-week signal comparison of the Federal Reserve archive with the existing `DPRIME / INTDSRUSM193N` snapshots on their **2,288 overlapping valid weeks**, there were **141 differing risk-on/off decisions (6.16%)**. Historical entry counts calculated with that comparator were **60** for the legacy definition versus **42** for the Fed archive alternative. (The original reported 60 entries is over its published evaluation convention, so these are *not* proof of its exact fingerprint either.) **Do not silently replace the original historical benchmark with the Fed alternative.** Likely causes include differences in the discount-series identity, observation calendars and cutover policy. Evaluate those differences explicitly.
- The updated event builder optionally uses `--fed-archive-dir <directory>` to run **offline** from real saved H.15 files, with -9999 sentinels removed. Direct live Fed download and full replay remain unverified.
- **Licensing unchanged:** the test demonstrates technical availability, *not* permission to redistribute Stooq, S&P, or Moody's data.

Tested offline builder example:

```bash
python -m freeburg.prime_discount.build_fed_public_events \
  --prices freeburg/prime_discount/data/spx_weekly_2026-08-07.csv \
  --fed-archive-dir /path/to/research/freeburg/prime_discount \
  --output local/fed_prime_discount_events.jsonl
```

The input S&P benchmark file in this command is for **private validation only** until redistribution rights are addressed.

## Prime/Discount legacy reproduction breakthrough (2026-10-11)

The initial Fed H.15 alternative's **140/2233** mismatching decisions (restricted to 1970-2013) are explained by **different series definitions**, not a malfunction of the normalizer. Swapping just the prime-rate source or just the discount source also changes signals. The gap is most acute after the January 2003 credit-window regime change.

We found user-side **FRED observations JSON** backups on the VPS (snapshots from June 2026). Comparing these JSONs independently against the benchmark's frozen change events produced **exactly identical rate values for every one of 2,387 common weekly dates**, for both:
- `DPRIME` (bank prime), and
- `INTDSRUSM193N` (IMF-provided historical discount series).

An explicit FRED JSON import mode was added, requiring users to provide both observation responses:

```bash
python -m freeburg.prime_discount.build_fed_public_events \
  --prices /path/to/locally_obtained_spx_weekly.csv \
  --fred-prime-json /path/to/DPRIME.json \
  --fred-discount-json /path/to/INTDSRUSM193N.json \
  --output /tmp/freeburg-prime-discount-legacy.jsonl

python -m freeburg.prime_discount.compare_sources \
  --prices /path/to/locally_obtained_spx_weekly.csv \
  --reference-rates /path/to/private_reference_rate_change_events.csv \
  --candidate-events /tmp/freeburg-prime-discount-legacy.jsonl
```

**Actual full-window test, 1970-01-02 through 2013-09-27:** **2,283/2,283 weekly decisions match**, zero input-level differences for prime/discount/SPX, **60/60 entries**, and **791/791 risk-on weeks**. The event builder generated **9,548 events / 2,387 decision events** from the frozen research SPX prices and saved FRED JSON.

**Fed H.15 alternative over the same window:** **2,233 overlapping decision weeks**, **140 different decisions**, agreement **93.7304%**, and **42** entries instead of 60. The differing H.15 source definition therefore must be labelled as an **alternative model**. It must **not** be substituted for the published benchmark.

**Important:** This proves reconstruction from **these saved JSON snapshots**, *not* that an unauthenticated/free fresh FRED download is automatically available or that FRED / IMF / Yahoo allow republication of the data. FRED API downloads may require a free API key, and FRED's third-party series rights still apply. The historical INTDSRUSM193N observations also do **not** establish point-in-time publication availability; they are retrospective snapshots.

Six local unit tests passed (normalization, GovInfo parsing, FRED JSON and parity checks). An updated GitHub CI workflow covers all six.

**Remaining decision:** make the original Prime/Discount benchmark optionally reproducible from **user-obtained FRED JSON (free access subject to terms)**, and retain official H.15 as an explicitly different source profile. This is much stronger than silently presenting H.15 as equivalent.

## GovInfo cross-year and end-to-end parsing validation (2026-10-11)

The public XLS for **page 31** was live downloaded and successfully parsed for these 10 additional representative issues: **2010-12, 2011-01, 2011-03, 2012-01, 2013-10, 2015-10, 2018-10, 2020-09, 2022-10, 2024-10**. Each has the title *Common Stock Prices and Yields*. The observed earlier boundary is specific: tested issues **2009-12, 2010-02, 2010-04 to 2010-08** returned a generic HTML document rather than the XLS; **2010-09 onward** succeeded for those samples. This is not exhaustive monthly coverage.

The real **2011-10** page-31 workbook passed the importer end-to-end: **13 monthly dividend rows**, and quarterly earnings observations of **6.15% (2010-12), 6.13% (2011-03), 6.35% (2011-06)**. Example: **2011-03 dividend yield 1.90%, earnings yield 6.13%**. The importer now handles abbreviated month names with periods, ellipsis missing-value markers, and provisional `p`/`r` prefixes.

GovInfo's official MODS metadata lists `dateIssued=2011-10-01` but `recordCreationDate=2011-11-08` for October 2011. **Neither field alone proves the date of first public availability.** The 2011-11-08 field used in the end-to-end importer demonstration is *only a provisional example*, not verified publication timing; the importer correctly labels all its observations unverified. Do not use the current demonstration CSV as PIT data.

**Important 2024 source issue:** dividends were represented as ellipses in a sampled 2024 table, despite earnings observations. The series can be partially missing even when a workbook loads successfully. A full historical harvest must record missingness and provider-specific changes, not fill from future issues.

All **six local Python tests passed**, and the updated GitHub Actions workflows have also passed.

## Independent FRASER fundamentals signal comparison (2026-10-11)

Added a reproducible `freeburg/tools/compare_fraser_fundamentals.py` CLI. Executed it on the user's VPS against the preserved scratchpad FRASER first-published series and the original two clean-sleeve CSVs. The comparator uses a **heuristic** availability delay of the **first of the month following the recorded issue month**; this is a sensitivity analysis, **not proven first-publication timing**.

| Sleeve | Compared signal weeks | Changed decisions | Percentage |
|---|---:|---:|---:|
| Competitive Returns | 2,929 | **197** | **6.73%** |
| Pu Shen | 2,873 | **415** | **14.44%** |

The dividend yield absolute difference had median **0.00 percentage points** (mean 0.13249); Pu Shen's earnings yield absolute difference had median **0.60761 percentage points** (mean 0.89334). These numbers include observations extending beyond the archive's end, where historical values are mechanically forward-filled; **do not interpret as a full independent 1970–2026 reconstruction**.

Source archive last observations: FRASER dividend weekly series **2010-06-05**, FRASER earnings monthly/quarterly series **2010-03-01**. Later data therefore require GovInfo vintages or another lawful source; extending the last value to 2026 is not acceptable production behavior.

This is decisive evidence that simply swapping in original archival FRASER observations is **not** an exact replay of the frozen models. It is valuable as an independent sensitivity check and an eventual stricter publication-aware variant. Neither headline historical return nor point-in-time status is inherited automatically.

Run:
```bash
python -m freeburg.tools.compare_fraser_fundamentals \
  --fraser-dir /path/to/edge-research-scratchpad/research/freeburg/data/fraser_sp500 \
  --sleeve-dir freeburg
```

### Corrected coverage-capped FRASER comparison

The first comparator run **incorrectly extrapolated the 2010 FRASER observation indefinitely to 2026**, inflating disagreement counts. That failure was identified and fixed: comparisons now stop at each series' last source observation, without future-period forward fill. The **superseding, accurate** diagnostics are:

| Sleeve | Source-covered valid signal weeks | Differences | Difference rate | Median underlying value difference |
| --- | ---: | ---: | ---: | ---: |
| Competitive | **2,080** | **37** | **1.7788%** | 0.00 percentage points |
| Pu Shen | **2,010** | **236** | **11.7413%** | 0.46422 percentage points |

These numbers apply only to the existing FRASER series ending in **2010** and retain the deliberately provisional issue-date availability assumption. **They supersede the longer-period values above.** The archival dividend source aligns relatively closely; the earnings yield does not. This suggests prioritising the Pu Shen earnings-definition and reporting-vintage audit before spending more time on Competitive.

## Does a script download all data fresh? (2026-10-11)

**Not yet.** The completed prototype now downloads and hashes **three types of source** into an immutable snapshot: the Federal Reserve H.15 ZIP, the NBER historic commercial paper text, and explicitly requested official GovInfo `Economic Indicators` table XLSs. It deliberately does not imply that the entire six-sleeve package is fresh-downloadable.

From the repository root:

```bash
python -m freeburg.tools.acquire_fresh \
  --output-dir local/snapshots/2026-10-11 \
  --govinfo-issue 2011-10 \
  --govinfo-issue 2009-12
```

A live VPS end-to-end test (2026-10-11) produced:
- **Federal Reserve H.15:** valid ZIP, **4,285,147 bytes**, SHA-256 `bb2e439536b7312483db8dafd4770509e1c34dcef692e14e4797bd16d051f24a`.
- **NBER CP:** valid non-HTML text, **59,340 bytes**, SHA-256 `cdd996194d1c47f6559dec75343bef32c070d5128f81664322113da7cedd4739`.
- **GovInfo 2011-10 Pg31:** valid XLS, **39,424 bytes**, SHA-256 `5f2ccf82699db496aabdcc7ae8ab62fc83791cc20def62cd9220f5fc5573e7d1`.
- **GovInfo 2009-12 Pg31:** returned HTML; correctly classified as unavailable/invalid XLS, not silently included.
- All results and URLs written to `manifest.json`; the utility refuses to overwrite an existing populated destination. Re-run with a *new* directory to ensure a fresh acquisition.

Not yet downloaded by this orchestrator: S&P index closes; user-obtained FRED API series `DPRIME` / `INTDSRUSM193N` (plus provider-rights check); remaining official CPI/Treasury / Moody's; historical FRASER first-publication PDFs; CRB / Dow DJ20 Heine inputs. GovInfo currently requires **explicit issue selection**, not a complete issue-range harvest. Its XLS observations have unverified availability dates, so they are not automatically injected into strategies.

A fully reproducible release needs separate **source acquisition → validation → normalization → point-in-time timestamps → signal comparison → replay** steps. A successful GET request by itself does not satisfy these gates.

## Government S&P weekly-price discovery (2026-10-11)

The GovInfo **Common Stock Prices and Yields** table includes machine-readable **weekly S&P composite index averages**, not merely fundamentals. Added `freeburg/tools/govinfo_weekly_spx.py` to parse these observations with provenance. Live extraction of the October 2011 Excel table yielded **5 weekly observations** labelled Oct 8–Nov 5, corresponding to the Friday weeks Oct 7–Nov 4.

**Crucial limitation: these are weekly AVERAGES, not Friday CLOSES.** Example: GovInfo's Oct 8 2011 weekly S&P average is **1,137.53**, whereas the research Yahoo-derived Friday close for Oct 7 was **1,155.46**. Replacing Freeburg close levels with government averages will change some trading decisions. The extractor explicitly emits `weekly_spx_average` and `WEEKLY_AVERAGE_NOT_FRIDAY_CLOSE__NO_PIT_CLAIM`, not `spx`. Furthermore, reported weeks may extend beyond the issue-month label, and the table is *published after observation*; never timestamp the figures as available on their labelled Fridays without a real publication date.

To run against authorised local GovInfo Excel files:

```bash
python -m freeburg.tools.govinfo_weekly_spx \
  --source-dir local/snapshots/2026-10-11/govinfo \
  --output local/govinfo_weekly_spx_averages.csv
```

The extractor is an **independent no-cost proxy source**, not a legal or quantitative certification of the S&P Friday-close historical dataset. This distinction prevents an attractive but false claim of exact market-price reproduction.

## 2010–2013 bounded GovInfo harvest and price-comparability audit

Executed the new `freeburg/tools/govinfo_harvest.py` on the VPS for **37 issue-months (2010-09 through 2013-09)**. **32** issues passed the strict stock-table XLS extraction; **5** were quarantined as invalid/unexpected layouts, including 2013-01 (a year-rollover/label anomaly). The valid issues produced **160 sourced weekly rows, 141 distinct Friday labels** (overlapping months account for duplicates).

Against the private S&P Friday-close benchmark, **138** labelled weeks overlap. Raw median absolute deviation was **62.93 bps**; mean **98.09 bps**, BUT these figures include a serious source outlier and are **not clean-equivalence numbers**.

**Found a concrete published-spreadsheet anomaly:** GovInfo 2013-02 Pg31 row labelled **Mar 2, 2013** contains weekly S&P index **1,837.04**, while adjacent weekly source rows are **1,515.23** and **1,540.38** and the private Friday close is **1,518.20**. This one-row departure is **~2,100 bps** and is almost certainly a typo in the published table, not proof of market movement. Preserve the original source value with a documented **anomaly flag**; do **not** silently repair it or use it as a tradeable observation. This is why a naive governmental price substitute is unsafe.

Harvest example:

```bash
python -m freeburg.tools.govinfo_harvest \
  --start 2010-09 --end 2013-09 \
  --output-dir local/govinfo_2010_2013
python -m freeburg.tools.govinfo_weekly_spx \
  --source-dir local/govinfo_2010_2013 \
  --output local/govinfo_weekly_averages.csv
```

Both commands operate on original data source files and do not convert weekly government **averages** into S&P **Friday closes** or reconstruct valid time-of-publication.

## GovInfo parser hardening / auditable outlier gate (same day)

The 2010 issues previously rejected as invalid were **valid**; their header row differs by one position. The parser now locates the S&P header within the first five rows, and handles the explicitly documented 2010/2011 New Year boundary. **Reharvest of 2010-09 through 2010-12: 4/4 success, 20 weekly rows, 18 unique Friday labels**. This corrects the earlier blanket characterization of these four as unavailable/invalid.

A separate **read-only** comparison script `freeburg/tools/audit_govinfo_prices.py` now flags grossly inconsistent weekly averages, never silently changing the source files. Against the private reference closes for the 2011–2013 subset, using a 500 basis-point audit threshold:
- **138** overlapping weeks;
- **median absolute deviation 62.9266 bps**;
- exactly **one** extreme flagged week: **2013-03-01** (GovInfo **1,837.04** versus reference Friday close **1,518.20**, difference **2,100.119 bps**);
- **zero** cross-issue conflicting values in the available overlapping observations.

A discrepancy between a weekly average and a Friday close alone is **not** proof of bad data, but a >20% isolated departure is a strong audit flag. Users must investigate it rather than automatically deleting or imputing it. No alternate dataset has been treated as equivalent to the Friday-close benchmark.

```bash
python -m freeburg.tools.audit_govinfo_prices \
  --govinfo-weekly local/govinfo_weekly_averages.csv \
  --reference-prices local/user_obtained_spx_weekly.csv \
  --threshold-bps 500
```

**Local regression suite:** 10 tests passed after header-layout and New Year fixes.
