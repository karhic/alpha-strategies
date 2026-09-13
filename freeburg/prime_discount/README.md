# Prime / Discount Spread

`spread = bank prime rate - discount rate`.

Long S&P 500 when both are true:

- spread < its 50-week moving average
- S&P 500 > its 50-week moving average

Otherwise cash.

## Results

Freeburg supplied no standalone numerical headline for this sleeve.

Canonical offline reconstruction, 1970-01-02 to 2013-09-27:

| Cash convention | CAGR | Sharpe | Max DD | Exposure | Entries |
|---|---:|---:|---:|---:|---:|
| 90% 3m T-bill | **9.86%** | **1.25** | **-15.17%** | **34.65%** | **60** |
| 100% 3m T-bill | 10.24% | 1.29 | -15.17% | 34.65% | 60 |

## Post-2003 regime break

The Federal Reserve discount-window framework changed in January 2003. A literal modern bank-prime minus primary-credit continuation becomes almost mechanically fixed; from 2013-2026 it is risk-on only about **0.15% of weeks**. It is therefore retained as a historical reconstruction, not presented as a healthy modern sleeve.

A separately labelled Freeburg-inspired `Prime - 10Y` descendant exists in the research archive, but it is **not** substituted into this historical strategy.

## Data provenance

- S&P 500: weekly Friday last price level.
- Prime rate: Federal Reserve bank prime series.
- Historical discount/adjustment-credit rate: Federal Reserve historical discount-rate series, with the January 2003 regime break recorded explicitly.
- Risk-off return: 3-month T-bill carry.

The historical signal path is structurally validated; no performance target was fitted because Freeburg did not publish one for this sleeve.
