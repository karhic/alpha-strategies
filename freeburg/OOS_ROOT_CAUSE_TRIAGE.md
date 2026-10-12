# OOS discrepancy root-cause triage — 12 October 2026

This is a targeted root-cause analysis of the **256 mismatched strategy-weeks**
between the shipped causal-engine decisions and the published post-2013 research
model. No strategy rules were optimized or changed.

## Findings from the original input histories

| Sleeve | Original decision mismatches | Source investigation |
|---|---:|---|
| **Primas** | **0** | Exact continuation of the research model. |
| **Pu Shen** | **111** | Reconstructing earnings yield from the same archived quarterly *as-reported EPS*, **90-day after quarter end**, with current-week SPX prices **perfectly reproduces the research-model decisions: 0 differences**. The frozen public replay's earnings-yield stream differs (e.g., 2014-01-03 frozen 4.724% versus quarter-lag model 5.153%). This is an **input version/timing mismatch**, not evidence that the strategy rule itself changed. |
| **Triple-40** | **109** | **Moody's Baa input cadence/continuation** is the primary identifiable difference. Using the archived post-2013 **monthly Baa-below-40w condition** rather than the repo replay's H.15 weekly Baa condition cuts the difference from 109 to **20 weeks**. The residual 20 weeks need separate inspection of the stored diagnostic flag, its rolling lookback and how the monthly rate is timestamped. |
| **Competitive Returns** | **36** | Reconstructing the dividend yield from the same archived quarterly TTM dividends with **90-day lag**, but retaining other frozen event inputs, yields **8 differences versus the original research model** (and 44 versus replay). Most discrepancies therefore arise from **fundamental vintages/timing and other macro input consistency**; the last eight need further isolation. |

## Important qualifications

The Pu Shen 90-day reconstruction uses retrospective archived quarterly values
with a **fixed 90-day availability assumption**, not audited original release
dates. Perfect match to the old research model establishes its arithmetic and
data lineage, **not** that the model satisfies strict PIT.

The Triple-40 monthly Baa test uses an existing archived research **binary
diagnostic flag**, not an independently fetched and as-of certified Moody's Baa
monthly observation series. It identifies an explanation for the gap, not a
completed source-quality verification.

For Competitive Returns, we have not independently reproduced all of its CPI
and 10Y yield vintages/observation timing. Do not present the 8 residual
decisions as necessarily price noise or harmless.

## Suggested precise next steps

1. Port the already-implemented quarterly 90-day earnings/dividend series into
   **user-selected baseline OOS events**, preserving separate source names and
   never replacing the original historical frozen ledger without an audit.
2. Isolate the 20 remaining Triple-40 weeks by comparing the original monthly
   Baa levels (not only the saved boolean) and 40-week history.
3. Compare Competitive's individual four predicates on the 8 remaining
   disagreements before deciding whether this is an implementation error.
4. Run the unified 4-strategy causal replay using the *same* source histories,
   and separately test conservative first-publication/next-session timing.
5. Keep the headline labelled original research-model result until the
   independent decision and accounting paths converge *for defensible reasons*.

The full weekly event histories and intermediate diagnostics were run on the
authorized VPS. The source data's original availability and redistribution
rights remain unverified.
