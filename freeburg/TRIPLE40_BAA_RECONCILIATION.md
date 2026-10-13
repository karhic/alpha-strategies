# Triple-40 archived Baa compatibility experiment

**Executed 12 October 2026** against the published 2014–August 2026
research-model weekly positions. This is a **diagnostic**, not a rewritten
production strategy or PIT-certified return series.

The unmodified released Triple-40 uses weekly historical H.15 Moody's Baa,
which stops in 2016, and cannot provide the same trend condition as the
scratchpad's post-2013 monthly continuation. We built an **isolated
diagnostic strategy**, leaving the original production strategy unchanged.
For the post-2013 period it consumes the saved binary monthly Baa-trend
indicator and otherwise uses the genuine original causal-engine market-input
history and 40-week stock/CP lookbacks.

Actual engine replay:

| Variant | Matched OOS decisions | Mismatched |
|---|---:|---:|
| Original public Triple-40 source replay | 549/658 | **109** |
| Archived monthly Baa-flag diagnostic engine replay | **638/658** | **20** |

**The 20 residual disagreement weeks have been isolated:**
2016-11-11, 2016-11-18, 2016-11-25; 2017-05-05, 2017-05-12,
2017-05-19, 2017-05-26; 2019-02-15, 2019-02-22; 2023-01-27;
2023-04-07, 2023-04-14, 2023-04-21, 2023-04-28; 2023-07-07;
2024-05-03, 2024-05-10, 2024-05-17, 2024-05-24, 2024-06-28.

In all 20, the S&P 40-week condition is bullish, but CP is not bullish,
making the **Baa trend input decisive**. The saved binary flag appears
inconsistent with the Baa trend decision embedded in the original research
model for those weeks. We cannot fix this by forcing the archived flag to
match: that would amount to circularly fitting inputs to reported outcomes.

**Source caveat:** the separate FRED BAA monthly endpoint was not reachable
from the authorized VPS during this test; two download attempts timed out.
The existing historical H.15 data can be downloaded, but its continuation
alone is insufficient for 2017 onward. Moody's Baa data carry explicit
redistribution restrictions.

**Decision:** retain this test as a diagnostic and do not substitute a
synthetic or inferred original Baa trend flag in the production replay.
The reproducible OOS outcome remains conditional until a vetted original
monthly Baa series can be acquired and its release-as-of convention fixed.

To reproduce with user-local snapshots, run
`python -m freeburg.tools.triple40_archived_baa_diagnostic`
with `--original-events`, `--flag-csv`, and `--ledger`, and compare
the resulting ledger against the original research model positions.
