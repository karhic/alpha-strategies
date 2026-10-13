# Fundamental-data availability: avoid lookahead *and* needless delay

**12 October 2026.** We investigated the four-sleeve 2014–August 2026
research model specifically to avoid assuming fundamentals were unavailable
long after they had actually been published.

## Two distinct questions

1. **How soon could a trader know *some* quarterly EPS/dividend figure?**
   Historical S&P releases, official first publication dates, archived issue
   editions, and independently captured point-in-time data answer this. A
   conservative but arbitrary 90-day lag can withhold information unnecessarily.
2. **When was the *particular numeric value in this retrospective workbook*
   available?** The downloaded `sp_wayback` workbook supplies a capture
   timestamp for the chosen value, but this is merely evidence that that
   particular value existed **no later than that timestamp**. It neither
   proves this value was first published on that date, nor establishes that
   it was known 90 days after the quarter ended. Later captures might contain
   subsequent revisions.

These must not be conflated: a 2017 EPS figure captured again in 2020 is
not evidence that no EPS number was published in 2017. Conversely, a 2020
capture cannot verify that this exact number appeared in 2017.

## Observed archived capture availability

For 51 quarter labels 2013 Q1 through 2025 Q3:

| Capture statistic | EPS | Dividends |
|---|---:|---:|
| Smallest delay from quarter-end | 99 days | 99 days |
| Median capture delay | 252 days | 240 days |
| Specific selected values independently captured by day 90 | 0% | 0% |
| Captured by day 120 | 23.5% | 25.5% |
| Captured by day 180 | 37.3% | 39.2% |

**These are first-observed-in-the-available-archive delays, not measured
historical official release lags.** Archive coverage is sparse and should
never be mistaken for evidence that publication took 252 days.

## Unoptimized timing sensitivity: four-sleeve composite

We varied only the fixed quarter-end availability lag used for the same
retrospectively captured S&P quarterly figures; the monthly Baa series uses
the separately documented **month-end** timing assumption throughout.
All other stock returns, T-bill/CP carry, strategy rules and baseline data
remain unchanged.

| Quarter-end assumed lag | Composite CAGR | Maximum drawdown | Pu Shen decisions changed vs 90d | Competitive changed vs 90d |
|---|---:|---:|---:|---:|
| 30 days | 8.47% | −19.20% | 34 | 6 |
| 45 days | 8.66% | −19.20% | 28 | 4 |
| 60 days | 8.74% | −19.20% | 16 | 7 |
| 75 days | 8.63% | −19.20% | 12 | 2 |
| **90 days (original)** | **8.72%** | −19.20% | 0 | 0 |
| 105 days | 8.75% | −19.20% | 10 | 7 |
| 120 days | 8.49% | −19.20% | 22 | 7 |
| 150 days | 8.65% | −19.20% | 33 | 11 |
| 180 days | 8.77% | −19.20% | 43 | 6 |

**Important:** An earlier assumed lag is not inherently a better source
model, and neither is a longer lag. These scenarios are a *sensitivity
envelope*, **not** independent PIT-valid replays, because changing the
timestamp does not remove possible revisions in the final quarterly values.
Do not choose the highest-CAGR row (180 days) based on these results.

Under the independently archived **capture-as-of** assumption, 21 Pu Shen
weeks lack enough earnings history for a comparable full-sample run. We
explicitly refused to silently forward fill from future data or report a
misleading headline as though complete.

## Recommended next work

Rather than arbitrarily use 90, 120, or 180 days:

- Build a **quarter-by-quarter source ledger** with fiscal quarter, original
  official S&P release/issue date, earliest archive proof, exact value in
  each snapshot, and whether the figure was *as reported* or revised.
- For each decision Friday use **the most recent actually available
  snapshot** (not necessarily the latest quarter or the newest hindsight
  revision). If the earliest archived capture is much later than a release,
  examine official dated releases/wayback captures to establish an earlier
  defensible version, not a guessed delay.
- Separate **earliest plausible knowledge**, **verified first observed**
  and **latest safe timing** scenarios. The goal is to keep legitimate
  information without borrowing later revisions.
- Keep a fixed sample and explicitly mark unknown/stale values; don't
  silently change sample length or optimize publication lags to P&L.
- Apply next-executable-session return accounting after the source
  provenance audit; calendar-day lag choice does not resolve Friday
  post-close fills.

The executable scenario engine is
[`tools/fundamental_availability_envelope.py`](tools/fundamental_availability_envelope.py).
It uses user-local OOS weekly returns, original replay macro event streams,
quarterly archived values, locally fetched CP rate and a month-end Baa
causal-engine ledger. No raw vendor data are committed.

**Status:** Fixed-lag sensitivity tested; accurate original quarter-by-quarter
availability and contemporaneous values **not yet certified**.
