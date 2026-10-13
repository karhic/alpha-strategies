# Triple-40 monthly Baa source: exact OOS parity, but timing lookahead identified

**12 October 2026 — Material caution for the headline backtest.**

We recovered the actual FRED **BAA** monthly observations (2010–September
2026) using the user-local Federal Reserve chart download, rather than relying
on the archived *binary* diagnostic flag. We preserved the released
`Triple40Strategy` unchanged, overlaid the raw monthly Baa levels onto
existing weekly event streams beginning 2010, and executed the actual causal
engine through August 7, 2026.

The published post-2013 Triple-40 research used monthly Baa observations
**from their observation month's first day**. In other words a value
describing the average yield over November can appear in November's first
week, before that month's value is knowable. This **introduces lookahead
bias** in that input. It fully explains the last 20 unexplained source
discrepancies and is not a defensible production timestamp.

## Actual 658-week causal replay outcomes

| Baa treatment | Matching research decisions | Mismatches | Four-sleeve model CAGR if substituted | Four-sleeve model max DD |
|---|---:|---:|---:|---:|
| Original public H.15 weekly Baa input | 549/658 | 109 | 8.74% | −19.20% |
| Archived Boolean monthly Baa diagnostic | 638/658 | 20 | 8.99% | −19.20% |
| **Original research monthly Baa stamped month-start** | **658/658** | **0** | **9.21%** | −19.20% |
| **Conservative monthly Baa stamped month-end** | 606/658 | 52 | **8.72%** | −19.20% |
| Monthly Baa stamped start of *following* month | 608/658 | 50 | **8.80%** | −19.20% |

All four portfolio CAGR calculations apply the changed actual Triple-40
causal-engine decisions to the **existing** research-model per-week
stock/cash returns for the other three sleeves. They retain the original
dividend and cash conventions. **They are sensitivity diagnostics**, not
audited net-of-cost executable P&L; the unchanged maximum drawdown is
particular to this sample, not a claim of invariant downside risk.

FRED monthly BAA observations have observation dates, **not independently
verified first-publication timestamps**. Using month-end or the beginning
of the following month is more conservative than month-start, but does not
establish true vintage timing, nor does it guard against historical revisions
to the Baa dataset. No source data are committed.

## Interpretation

- **Internal reproduction complete at fixed original research inputs:**
  Primas, Pu Shen and Competitive had 658/658 action parity under their
  previously documented original research assumptions. Now Triple-40
  also has 658/658 action parity **when the original month-start Baa
  convention is reproduced**. Across four sleeves, that is 2,632/2,632
  decisions, **but not independent PIT validation**.
- **A proven lookahead mechanism is present in the original Triple-40
  version.** The 9.21% composite result must not be sold as PIT-clean.
- The conservative month-end Baa scenario yields **8.72%** instead of
  **9.21%** CAGR, changing this one input convention, with all else fixed.
- A further full-week execution-delay sensitivity and the 90-day
  earnings/dividends vintage caveats remain separate issues.

## Replay the original rules under each input convention

```bash
python -m freeburg.tools.overlay_triple40_monthly_baa \
  --original-events freeburg/triple40/data/triple40_benchmark_events.jsonl \
  --monthly local/fred-baa.csv \
  --availability month-end \
  --output local/triple40_baa_month_end_events.jsonl

python freeburg/triple40/run_replay.py \
  --events local/triple40_baa_month_end_events.jsonl \
  --end 2026-08-07T23:59:59+00:00 \
  --ledger local/triple40_baa_month_end_ledger.jsonl
```

The FRED CSV needs columns `observation_date,BAA`. **Never use
`--availability month-start` for a purported PIT-clean performance
series**: that option is provided only to reproduce and audit the original
historical research convention.

This finding supersedes the diagnosis in
[the earlier binary Baa-flag reconciliation](TRIPLE40_BAA_RECONCILIATION.md).
