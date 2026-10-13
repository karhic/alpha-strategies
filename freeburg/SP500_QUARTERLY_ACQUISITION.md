> **13 October update:** A **fresh empty-directory Docker source acquisition** successfully recovered all 21 archived S&P workbooks, including the four previously intermittent captures; the one-command full 2014–2026 public-source replay then passed **2,632/2,632 causal-engine parity checks and accounting checks**. The 13-quarter AlphaQuery/index-mathematics fallback remains available if the newest archive is temporarily inaccessible. Results are retrospective research scenarios, not certified first-release PIT trades. See [Docker command](REPRODUCE_FOUR.md).

# Re-acquiring the missing historical S&P earnings/dividend source

**Status: acquisition pipeline implemented and live-tested, 12 October 2026.**

We traced the 151-quarter S&P data archive behind the original Freeburg
post-2013 research to just **21 independently archived Wayback captures** of
S&P's historical quarterly workbook. This public repository now includes
**capture timestamps and original URLs only**, not the source workbooks or
their proprietary figures, in
[`sources/sp500_wayback_captures.json`](sources/sp500_wayback_captures.json).

The acquisition program
[`tools/download_sp500_quarterly_wayback.py`](tools/download_sp500_quarterly_wayback.py)
downloads these specific archived sources **on the user's machine**, parses
the original S&P `SECTOR EPS` historical-actual cutoff and `QUARTERLY DATA`
tabs, normalizes quarter-end trading dates to calendar quarter ends, and
retains the **earliest surviving archived capture** for reported EPS and
quarterly dividends separately. It outputs both a historical-quarter CSV
consumable by the standalone Freeburg-4 model and a source/hash/provenance
manifest. The binary workbooks and their extracted observations remain
untracked user-local files.

## Tested results

On 12 October 2026, the tool actually recovered **17 of the 21 archived
workbooks** through the Wayback Machine and produced complete quarterly
reported-EPS and dividend fields **1988 Q1–2022 Q2** (**138 quarters**).

**All 138 recovered quarters matched both numerical columns of the original
private research archive EXACTLY** (zero differences). This is meaningful
independent source re-acquisition and confirms that a stranger with provider
access need not already possess our private dataset to obtain the same values.

The **four 2023–2026 Wayback snapshots** were temporarily inaccessible due
to a connection-refused response from `web.archive.org` on the test machine:

- 2023-06-09 20:26:08
- 2024-05-07 05:03:18
- 2025-05-28 10:16:33
- 2026-01-28 17:02:14

These four captures supply the most recent **13 quarters, 2022 Q3–2025 Q3**,
which are needed to reproduce the full 2014–2026 study. Source acquisition
therefore **is not yet a guaranteed one-command clean download**, despite the
confirmed success for the first 138 quarters.

A separately and legally acquired copy of the missing archived XLSX may be
supplied as `<14_digit_timestamp>.xlsx` in a local
`--snapshot-cache` folder. Failed captures can be retried independently;
the tool does not fabricate values, substitute revised live-workbook data or
pretend incomplete data match the research original.

## Source-quality standard for public claims

**Source of record:** an original S&P Dow Jones Indices workbook, either served
from S&P itself or captured by the Internet Archive with its original
`spindices.com` / `spglobal.com` source address and capture timestamp.
The Internet Archive is an archival *transport*, not a new market-data
publisher. GitHub mirrors and unsourced copies are **not acceptable as
authoritative inputs** even when their numbers agree.

**Evidence that a reader should be able to verify:** the source URL,
capture timestamp, downloaded-file SHA-256, sheet, selected quarter, extracted
reported-EPS and dividends-per-share values, the historical-actual designation,
the extraction code version, and dates at which each figure was *assumed*
available to the trading model. Keep observation periods, archive capture
times, and actual publication times in separate columns.

**Cross-check:** compare each extracted observation against a second dated,
official source when possible; discrepancies are flagged, not silently
resolved by choosing the better-performing value. Matching 138 quarters to
our own previously assembled archive proves consistent re-acquisition from
the same original records, **not independent confirmation of original
publication timing or PIT correctness**.

**Incomplete inputs:** if an official capture cannot be obtained, mark
the corresponding quarter **unverified and unavailable for exact
reproduction**. Do not silently substitute GitHub data, a current revised
workbook, or forward-filled data. Distinct proxy-source scenarios can be
published separately, with their own performance figures and provenance.

This is the provenance standard for a public Freeburg claim; the current
full-period results must remain explicitly qualified until all necessary
source quarters meet it.

## Additional independent EPS cross-check (12 October 2026)

A separate professional-data publisher, [AlphaQuery's S&P 500 EPS history](https://www.alphaquery.com/stock/SPX.X/earnings-history), reports actual quarterly S&P 500 EPS figures for the missing interval. We compared its 13 rows for **2022 Q3–2025 Q3** directly against the values independently extracted in our original S&P Wayback research archive.

**All 13 of 13 quarterly EPS amounts match exactly to two decimals** (the EPS precision used by the underlying research workbook). Examples: 2022 Q3 **44.41**, 2023 Q3 **47.65**, 2024 Q4 **57.69**, 2025 Q3 **63.52**.

**Source classification:** this is independent *corroboration*, not the official historical S&P snapshot. Its listed announcement dates are vendor metadata and are **not** independently verified S&P original-release timestamps; the figures may have been revised later. Under the project's first-party-only provenance standard, these corroborated numbers **do not replace the missing original workbooks** in the exact-release path.

This materially reduces concern about simple transcription or spreadsheet-processing errors, but the strict clean-room **source-of-record acquisition remains incomplete**. An alternative reproducibility mode could use this provider with explicit source labels and sensitivity tests, never as an unmarked substitution.

## Instructions

From the repository root:

```bash
python -m pip install -r freeburg/requirements-data.txt

python -m freeburg.tools.download_sp500_quarterly_wayback \
  --manifest freeburg/sources/sp500_wayback_captures.json \
  --output-dir local/four/wayback-acquired \
  --workers 3 \
  --accept-source-terms
```

For missing snapshots already acquired through an authorized route:

```bash
python -m freeburg.tools.download_sp500_quarterly_wayback \
  --manifest freeburg/sources/sp500_wayback_captures.json \
  --snapshot-cache local/wayback-archive-workbook-cache \
  --output-dir local/four/wayback-with-cache \
  --accept-source-terms
```

Supply
`local/four/wayback-acquired/quarterly_first_observed_actual.csv`
as `--quarterly` to
[`reproduce_four_from_sources.py`](tools/reproduce_four_from_sources.py).
The reproduction tool **must refuse** silently incomplete quarter histories.

This is source re-acquisition, **not proof of original release timing**:
archive timestamps prove figures had appeared by the captures, but do not
prove the exact values existed at quarter-end plus 90 days. Historical
workbooks may contain revisions. S&P's workbooks may be subject to
third-party terms; no source workbooks or extracted values have been committed.

**Next engineering issue:** improve accessibility and documented fallback
for the four newest missing Wayback capture URLs, not repeat the 1970s
historical research.
