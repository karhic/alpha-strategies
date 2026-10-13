# Live S&P dividend data via price and total-return index

**Implemented and downloaded 12 October 2026.** A recurring source is now available
without waiting for quarterly S&P press-release parsing: download **S&P 500 Price
Return** (^GSPC) and **S&P 500 Gross Total Return** (^SP500TR) daily index
levels and calculate daily dividend index points:

`DividendPoints[t] = Price[t-1] × TotalReturn[t] / TotalReturn[t-1] − Price[t]`.

Add ex-dividend date contributions across the calendar quarter. Both indices
are calculated by S&P Dow Jones Indices but retrieved through **Yahoo, a
secondary distributor**; they are **not** original first-party workbooks.
The code preserves raw files, URLs, acquisition timestamps, SHA-256 hashes,
daily derived observations, and quarterly outputs locally.

Run:
```bash
python -m freeburg.deploy.capture_dividends --output-dir local/captures/dividends-20261012
```

The source-level request and full derivation are inspectable in
[`capture_dividends.py`](capture_dividends.py). The latest **completed**
calendar quarter in the successful capture was **2026 Q3**, with about
**20.48706 dividend index points**; unlike S&P official quarterly reports,
this is a number **derived** from independently quoted index levels and
rounded market data. It is not an exact official figure.

## Historical cross-check and impact on decisions

Compared with the earlier original S&P Wayback workbook dividend series:

- **151/151** quarters have corresponding calculated index levels in the
  1988 Q1–2025 Q3 archive.
- Median absolute numerical discrepancy was about **0.00338 index points**
  across the whole period (and **0.00364** for 2014–2025).
- The largest absolute discrepancy in the 2014–2025 part was **0.08326
  index points**, and the public prices use daily rounded observations.
- Replacing **all** original quarterly dividend inputs with this formula
  produced **0/658 different Competitive Returns weekly decisions** in
  the 2014–2026 model, holding other inputs constant. The four-sleeve
  modeled CAGR moved from **8.7173588% to 8.7176211%**: **0.0262 basis
  points**. No trading signal was optimized to these comparisons.

This demonstrates the **numerical robustness of the historical Competitive
Returns decision rule to the derivative index dividend series**. It does
*not* prove the original dividends were available at our assumed historical
fixed 90-day lag, nor does it license republishing provider data.

## Next live-integration gates

The working market/macro source capture in [LIVE_DATA.md](LIVE_DATA.md)
and the EPS capture in [LIVE_FUNDAMENTALS.md](LIVE_FUNDAMENTALS.md)
are separate immutable source snapshots. The dividend capture completes the
**basic automated data acquisition** for all four sleeves' underlying
indicators. We still need a *single weekly as-of join* of their observation
series, data-age and value-revision policies, causal-engine decision
reconciliation, the current quarterly dividend transition policy, and
a persistent forward-only scheduler. All real IBKR trading and X posting
remain disabled.

The historical availability labels in vendor pages must never be used as
surrogates for the actual capture timestamp in a live decision. In particular,
Friday closing values can be used only after that closing session has
completed; any corresponding IBKR order must be scheduled after the signal
becomes knowable.
