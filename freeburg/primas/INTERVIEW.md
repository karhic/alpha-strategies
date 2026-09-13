# Primas interview brief

## Thirty-second explanation

Primas is a two-condition weekly timing strategy from Freeburg's published work. It is risk-on only when the S&P 500 is above its 52-week moving average and 3-month commercial-paper yield is below its own 52-week moving average.

The interesting part of the project is not the Boolean rule; it is making the entire path auditable. I reconstructed the historical commercial-paper chain across discontinued Federal Reserve series, separated economic time from data-availability time, replay historical events through the same strategy implementation intended for live trading, and keep analytics downstream from an immutable execution ledger.

## Why the replication is credible

Freeburg reported about 12.1% compound annual return and -16.4% maximum drawdown. The corrected reconstruction produced about 12.08% and -16.43%, with roughly 39.5% equity exposure and 43 risk-on entries from 1970 through 2013.

The result was not obtained by parameter optimization. The rule and 52-week window were fixed by the published strategy. The main historical ambiguity was source continuity for commercial paper; plausible pre-1971 conventions were tested explicitly and produced similar results.

## Engineering points worth discussing

- same strategy implementation in replay and live;
- point-in-time `available_at` barrier rather than ad-hoc dataframe shifting;
- provider-specific acquisition isolated from signal code;
- append-only run ledger as canonical truth;
- analytics and publishing downstream from runtime;
- recorded live streams replayable for parity testing;
- failures or unresolved source substitutions documented rather than hidden.

## Questions to expect

**Why commercial paper?**
It acts as a short-rate/credit-condition input. Primas requires both positive equity trend and an easing short-rate condition.

**Did you fit the rule?**
No. The rule and window came from the published strategy. Reconstruction choices were evaluated for source plausibility and sensitivity, not selected by optimizing Sharpe.

**What is the largest remaining caveat?**
Historical source semantics change over decades. The project therefore distinguishes benchmark-replication conventions from deployable point-in-time conventions and documents both.

**How would you trust the live version?**
Archive the exact live event stream, replay it later through the same strategy version, and require identical decision fingerprints. Broker transport and public callouts are adapters/subscribers outside strategy logic.
