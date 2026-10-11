# Heine-inspired modern proxy (2013–2026)

**Experimental sensitivity test — NOT a reproduction of Freeburg's historical Heine.**

The original five-condition, three-vote timing structure is retained, with two
explicit substitutions:

- Original Dow 20 bond price/24-week moving-average condition → **LQD**
  unadjusted close/24-week moving-average condition.
- Original CRB commodity index/20-week moving-average condition → **DBC**
  unadjusted close/20-week moving-average condition.

Remaining conditions use Fed H.15 20-year Treasury yield, Fed H.15 3-month
T-bill yield, and Dow Jones Utility Average (Yahoo `^DJU`), using the original
6/6/10-week moving averages. The five votes are not retuned.

Risk-on holds **LQD**, with next-week *adjusted-close* return including
distributions. Risk-off earns current 3-month T-bill yield/52. Signals are
evaluated using data stamped through the decision Friday, with the following
week's return attributed to that decision. Trades occur at modelled Friday
close, without transaction costs, slippage or implementation delays; this
simplifies real-time execution.

## Actual test (run on VPS, 12 Oct 2026)

2013-10-04 to 2026-08-07, **671 decision weeks**:

| Metric | Modern Heine proxy |
|---|---:|
| CAGR | **3.74%** |
| Maximum drawdown | **−20.50%** |
| Raw weekly Sharpe, annualized | **0.51** |
| Risk-on exposure | 49.48% |
| Risk-on entries | 71 |

For the directly overlapping **2014–2026** 658-week sample:

| Strategy portfolio | CAGR | Max DD | Raw Sharpe |
|---|---:|---:|---:|
| Existing equal-weight four sleeves | **9.21%** | −19.20% | 1.08 |
| Five sleeves including 20% modern Heine proxy | 8.22% | −18.83% | 1.12 |
| Modern Heine proxy alone | 3.87% | −20.50% | 0.52 |

Heine proxy correlation with the four-sleeve composite is only **0.185** on
the overlapping sample. It improves the *raw* Sharpe slightly, but **reduces
CAGR approximately one percentage point**. This is not a compelling reason
to displace the established four-sleeve headline.

The substitutes were selected for instrument availability and approximate
economic character, **not tuned for performance**. Nonetheless they are not
identical to the original indices (especially the historical Dow bond
average). The original Freeburg 11.5%/−4.8% published claim must **not**
be associated with these new proxy results.

## Reproduce

From the repository root after installing project Python requirements:

```bash
python -m freeburg.heine.modern_proxy
```

The script downloads the modern inputs, uses the existing Federal Reserve H.15
reader, and writes its local model return series to
`/tmp/freeburg-heine-v1/weekly.csv`. Upstream price-data access and
redistribution rights depend on providers. Note that it uses the historical
**modern substitute strategy**, not the original Dow/CRB strategy's canonical
causal trading-engine replay implementation.

**Ship decision:** retain the **four-sleeve composite** as the primary
public research result; keep modern Heine in an independently and prominently
labelled experimental section.
