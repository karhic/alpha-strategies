# Freeburg four-sleeve execution timing stress

**2026-10-12 — additional diagnostic, not an independently certified PIT backtest.**

The four headline sleeve simulations use weekly source observations and a
Friday close-to-next-Friday return convention. At least some reconstructed
replay events have an `available_at` timestamp after the assumed Friday
trading close. Consequently a report based on *same-Friday close execution*
has a defensible causal-timing objection even if the week-specific signals
are perfectly calculated.

We tested an intentionally conservative **one-whole-trading-week signal delay**
with fixed original trading rules. The equity/cash regimes were inferred from
existing separate-research weekly returns; defensive cash was reconstructed
using H.15 commercial-paper carry, at the historical 90% convention for
Triple-40 and Competitive. The same source window is used, **January 10,
2014–August 7, 2026** (657 holding-week decisions), for both alternatives.

| Metric | Same-week model | One-week-late sensitivity |
| --- | ---: | ---: |
| CAGR | **9.20%** | **8.22%** |
| Maximum drawdown | **−19.20%** | **−22.10%** |
| Raw Sharpe | **1.08** | **0.96** |

This is a genuine *negative robustness result*: moving the signal forward
by one full weekly observation costs about **0.98 percentage points CAGR**
and increases maximum drawdown by **2.90 percentage points**. The signal
rules and portfolio allocation were not optimized against the later sample.

Source conversion inferred equity exposures from each sleeve's modelled
equity versus cash return (there were no near-equality ties within
0.001% absolute weekly return in this sample).

This **does not** prove a next-Monday-open implementation works. It is a
*whole-week lag stress*, not actual exchange timestamps, daily execution
prices, independently verified releases, or complete transaction accounting.
The latter remain release-audit items.

Reproduce from the user's local weekly research source file:

```bash
python -m freeburg.tools.one_week_late_sensitivity \
  --weekly-returns local/oos_weekly.csv \
  --output local/one_week_late_report.json
```

The script uses the same public Fed H.15 downloader as Primas and does not
commit raw market data.
