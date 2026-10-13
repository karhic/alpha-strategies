# Current S&P 500 fundamental-data acquisition

**Live test: 12 October 2026.**

We need (a) as-reported quarterly S&P 500 EPS for Pu Shen and (b) quarterly
S&P 500 dividends per index share for Competitive Returns, both observable
from dates on which the live strategy could genuinely have acquired them.

## A working acquisition path for EPS

The current HTML table at
https://www.alphaquery.com/stock/SPX.X/earnings-history
contains quarterly actual S&P 500 EPS and vendor-declared announcement dates.
The user-local program `python -m freeburg.deploy.capture_eps
--output-dir local/captures/eps-2026-10-12` downloaded and parsed it
successfully. Latest published observation in this **12 October 2026**
snapshot was **2026 Q2, $91.38**. The preceding observation was
2026 Q1, $67.30. All 13 2022–2025 observations checked earlier match
the official-workbook values in the private research archive to EPS's
two-decimal precision.

A capture consists of immutable HTML, parsed CSV, capture timestamp,
original URL, source hash, and *explicit secondary-provider classification*.
The vendor's listed announcement dates are **not** established first
publication times, and the same retrospective page could have incorporated
revisions. Start a new real-time snapshot series from today and allow a
new observation to affect a live decision only after its first successful
local capture, not retroactively on the listed historical date.

This is useful for developing and *shadow monitoring* Pu Shen, but it does
**not** meet our first-party historical-publication verification standard.
It may also have vendor terms that need review for automated commercial use.

## Dividend source

S&P Dow Jones Indices first-party news releases publish quarterly S&P 500
dividend payments per share, generally rounded to cents:
https://press.spglobal.com/
See [the first-party dividend cross-check](../SP500_OFFICIAL_RELEASE_CROSSCHECK.md).

This source has desirable independently dated provenance; it is **not**
a canonical automated numerical feed at workbook precision. An additional
parser, release calendar, missing-publication handling and quarterly
series continuity checks are still necessary before the full four-sleeve
strategy can run unattended.

An alternative to explore is the S&P 500 total-return index `^SP500TR`,
which is accessible through Yahoo's chart endpoint. **Price versus total-
return index movements must not simply be labeled the quarterly S&P dividend
per-share series** without reconciling index-point conventions, compounding,
divisor actions and methodology. It can be a cross-check, not a hidden
replacement for the original strategy input.

## Promotion status

- Current EPS: **captured**, secondary-source, hash-audited, but not first-party.
- Current dividends: **dated official releases identified**, automated
  extraction/precision reconciliation outstanding.
- Actual four-sleeve weekly decision: **not live**.
- IBKR/X: **disconnected/disabled**.

There is no "future-data" leakage in live decisions when inputs are captured
in real time and frozen, but **revisions, source delays, after-close timestamps,
and cross-source mismatches** are still material risks. No orders should be
activated until all four live input series and actual causal decision ledgers
are validated against a forward record.
