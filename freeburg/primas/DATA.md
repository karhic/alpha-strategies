# Primas data contract

Primas consumes two logical weekly series:

- S&P 500 level
- 3-month commercial-paper yield

The strategy must not know the data vendor.

## Historical CP chain

The validated reconstruction used:

1. pre-April 1971: NBER Macrohistory `m13002`;
2. April 1971 through August 1997: Federal Reserve weekly 3-month prime commercial paper;
3. September 1997 onward: Federal Reserve weekly 90-day nonfinancial AA commercial paper.

Numeric missing-value sentinels must be removed before normalization.

The best published-fingerprint match used the pre-1971 monthly seed stamped at month start and carried forward to the weekly calendar. Other plausible pre-1971 conventions gave similar results and remain documented in the research archive.

## S&P input and returns

The signal uses only the weekly S&P 500 level. Dividends do not enter the timing rule.

Historical benchmark return accounting uses the S&P price return plus the dividend-return layer already reconstructed in the scratchpad. Risk-off benchmark accounting uses commercial-paper carry.

Signal generation and return accounting remain separate concerns.

## Point-in-time contract

Each normalized observation must have an economic `event_time` and an `available_at` timestamp. Historical benchmark and live/deployable data profiles may differ in availability convention, but both must feed the same strategy implementation.

## Canonical research lineage

- `research/freeburg/PRIMAS_TRIPLE40_CORRECTED_CP_DIAGNOSTIC_2026-08-12.md`
- `research/freeburg/diagnose_primas_triple40_corrected_cp.py`
- `research/freeburg/diagnose_pushen_pinnacle_interpolation.py`
- commit `6f5bd253d6883431e6ac43706ff1ebf06c84fdea`

## Live policy

Use documented current sources for S&P level and commercial-paper yield. Provider clients stay in adapters, never inside strategy logic.
