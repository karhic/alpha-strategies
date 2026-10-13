# Actual causal-engine OOS replay with matched quarterly research inputs — 12 Oct 2026

This is a further reconciliation of the original scratchpad *post-2013* OOS
decisions and the released Python strategy classes. It keeps the **original
90-day after-quarter-end availability hypothesis** fixed; this is **not**
independent first-publication-timestamp/strict PIT certification.

## Completed actual replays

I built a separate copy of the existing canonical event streams, replacing
**only** the S&P earnings-yield event for Pu Shen or the dividend-yield event
for Competitive with a TTM quarterly series derived from the existing
`sp_wayback/quarterly_first_observed_actual.csv` source:

1. Assemble the prior four quarters' reported values into trailing-12-month
   EPS or dividends per share.
2. Define *assumed availability* as the quarter-end plus 90 days.
3. As-of join the last available TTM value at each Friday decision date.
4. Divide by that week's S&P price, multiply by 100 to obtain a yield.
5. Preserve all other replay event columns, decision clock, strategy code,
   engine, and original source stream. Tag replaced inputs with a non-PIT
   source label. Write **new local event files**, not overwrite existing
   benchmarks.
6. Run the released causal engine against the altered event streams, compare
   each actual action with the original research model's cash/equity branch.

| Sleeve | Prior OOS mismatches | After isolated 90-day input overlay | Weeks compared |
|---|---:|---:|---:|
| Pu Shen | 111 | **0** | 658 |
| Competitive Returns | 36 | **0** | 658 |

Both are now **658/658 actual engine actions matching the research model**.
This resolves those discrepancies **at fixed source identities and model
assumptions**. No strategy tuning, return fitting, or override of the
strategy's emitted actions was necessary.

The two overlays use 1,955 replacement rows each over the available
post-1989 source history; early historical observations without a usable TTM
quarterly value retain their original benchmark input. This is clearly
marked, including the distinction between original frozen source and
research-90-day overlay.

### Outstanding question

We **have not proven** that the S&P annual/quarterly EPS and dividends
obtained in a much later web-captured workbook actually equal the original
figures known by those quarter-end-plus-90-day decision dates. This test
establishes **internal cross-implementation reproducibility only**, not
vintage-safe trading feasibility.

The still unresolved Triple-40 Baa continuation and actual next-session
execution/PIT timing remain separate release gates.

## Reproduce from research archive

The new repository tool
[`tools/overlay_oos_quarterly_90d.py`](tools/overlay_oos_quarterly_90d.py)
takes the existing S&P archived quarterly CSV, an unmodified original
`*_benchmark_events.jsonl` source stream and a new output path. For
Competitive it also requires a local `date,spx` weekly S&P source.

After writing new event streams, run the respective existing
`freeburg/pushen/run_replay.py` and `freeburg/competitive/run_replay.py`
with `--events <overlay_file>`, `--ledger <new_ledger>`, and `--end
2026-08-07T23:59:59+00:00`. The original weekly research-stock/cash branch
reconstruction is described in [OOS parity finding](OOS_PARITY_FINDING.md).

This code explicitly declines to call quarter-end-plus-90-day actual
published vintage timing; source snapshot availability remains an open issue.
