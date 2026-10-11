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
