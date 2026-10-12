# Four-sleeve post-2013 cross-implementation parity finding — 12 October 2026

**Major release blocker discovered:** the public causal trading-engine strategies
and the older scratchpad return-model signals **do not all agree** in OOS.
The original README headline 9.21% CAGR, −19.20% maximum drawdown is internally
reproducible from the historical research model, but is **not** reproduced by
the existing four strategy event ledgers.

## Actual comparison

All four original strategy classes were re-executed on the VPS using existing
benchmark event JSONL streams, with replay `--end 2026-08-07T23:59:59+00:00`.
The established scratchpad's modelled weekly stock/cash returns were independently
classified into its binary risk-on/risk-off branches using verified Federal
Reserve commercial-paper interest and the common modelled equity returns. There
were **zero ambiguous branch-classifications**. Source streams remain legacy or
frozen and are not newly certified PIT.

| Sleeve | OOS weeks | Action matches | Action mismatches |
|---|---:|---:|---:|
| Primas | 658 | **658** | **0** |
| Triple-40 | 658 | 549 | **109** |
| Pu Shen | 658 | 547 | **111** |
| Competitive Returns | 658 | 622 | **36** |
| **Total** | **2,632** | **2,376** | **256** |

Primas is an exact same-input/same-rule continuation. For the other sleeves,
mismatch causes include input lineage/timing and, for Triple-40, its later
Moody's Baa continuation. **Do not assume** all divergences are innocuous or
fundamental vintage revisions without date-by-date analysis.

A preliminary 658-week ledger-*decision*-driven portfolio, with the old
scratchpad's common stock/cash weekly P&L assumptions applied to the new
strategy target weights, returned **8.30% CAGR, −19.20% maximum drawdown,
2.74× terminal wealth**, compared with the published original research-model
**9.21% CAGR, −19.20%, 3.05×**. This is a diagnostic, not an alternative
certified strategy/PIT backtest; the return engine and source availability
remain as described in the four-sleeve audit.

## Consequences

1. **Freeze the headline as an explicitly labeled research-model result** rather
   than representing it as reproduced by the causal engine. This difference is
   now material and quantified.
2. Prioritize tracing the **256 mismatched dates** back to actual per-series
   snapshots. Determine whether disagreements result from alternate inputs,
   rolling-window conventions, observation timestamps, different economic
   proxies, or real implementation errors.
3. No tuning or picking whichever version backtests better. Preserve both
   originals and publish a pre-specified corrected series only after
   contemporaneous-source validity and timestamp correctness are established.
4. Continue shipping progress through reproducible audit tools and caveats,
   not another historical-source archaeological project.

## Reproduce

Generate existing benchmark decision ledgers with the repository's four
`run_replay.py` entrypoints using `--end` beyond 2013. Acquire the
legacy research weekly returns and an independent Federal Reserve commercial
paper weekly snapshot locally, then run:

```bash
python -m freeburg.tools.audit_oos_action_parity \
  --weekly-returns local/oos_weekly.csv \
  --cp-weekly local/cp_weekly.csv \
  --ledgers local/oos_ledgers \
  --output local/oos_action_parity.json
```

The tool asserts branch identifiability by first decomposing the published
weekly strategy return into the two possible holding returns. Both source
series and generated replay ledgers remain local and are not vendor-rights
cleared for redistribution.

## Source-level investigation

The follow-up [OOS root-cause triage](OOS_ROOT_CAUSE_TRIAGE.md) identifies a direct original-90-day-EPS-source explanation for **all 111 Pu Shen** divergences; a **monthly-versus-weekly Moody Baa source** accounts for most Triple-40 divergences (109 down to 20); and the 90-day quarterly dividend lineage accounts for most Competitive divergences (36 down to 8 when other frozen macro series are held fixed). These are **diagnostics, not PIT certification**.

## Third strategy narrowed

An actual [Triple-40 archived Baa-flag diagnostic replay](TRIPLE40_BAA_RECONCILIATION.md) confirmed **638/658 OOS decisions** matching, versus the original released-source replay’s 549/658. The remaining **20 weeks** all hinge on the Baa predicate; do not infer the old research flag from desired outcomes. Original strategy code and headline results remain unchanged.
