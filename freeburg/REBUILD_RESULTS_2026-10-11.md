# Fresh-data Freeburg reconstruction — measured integration status

**Actual run: 2026-10-11 on the user's VPS**. No original research datasets overwritten. All new snapshots remain local and git-ignored.

## Completed

- Fresh S&P 500 Yahoo chart acquisition: 14,315 daily observations / 2,963 weeks, Jan 1970–Oct 2026; **0 close-level discrepancies across 2,959 overlapping benchmark weeks**.
- Fresh federal H.15 and NBER CP downloads and manifest. FRED API downloader added (requires user's free key), and legacy FRED snapshot rate reconstruction validated.
- Automatic 193-month GovInfo acquisition for Sep 2010–Sep 2026: **191/193 issues** obtained. Latest parser handles XLS, XLSX, footnotes and anomalous labels. The 2 missing months still require a fallback.
- **2,605** source vintage observations across the 191 government issues, resolved to **264** first-observed period/indicator rows (191 dividends, 73 earnings) under an explicitly labelled archive-catalog timing scenario.
- Implemented `python -m freeburg.tools.rebuild_fundamentals`, which **reuses** the archived FRASER earnings and dividends already extracted 1970–2010, and independently harvested 2010–2026 GovInfo rows. For earnings it reconstructs weekly yield as **TTM EPS / current Friday S&P level × 100**; it does **not** erroneously step-fill a printed E/P percentage.
- The rebuilt series contains **2,927 weekly earnings yields**, **2,957 weekly dividend yields**, and **2,963 price weeks**. No LLM/manual OCR rerun required.
- **Full baseline-reproduction comparison with the rebuilt sources (not the final PIT claim):**

| Sleeve | Comparable weeks | Decisions different | Agreement | Median absolute underlying yield difference |
| --- | ---: | ---: | ---: | ---: |
| Pu Shen | 2,873 | 247 | **91.40%** | ~0 percentage points |
| Competitive | 2,929 | 132 | **95.49%** | 0 percentage points |

This is a **new-source sensitivity profile**, not an assertion that the legacy published strategies failed replication. The original frozen strategies still run correctly. Mismatch concentrations and the effect of historical availability assumptions require targeted audit, not methodological rediscovery.

- Five original sleeves (Primas, Triple-40, Pu Shen, Competitive, Prime/Discount) completed decision-only replays using causal-trading-engine. Heine's exact underlying index path remains unresolved.
- 16 unit tests pass.

## Rebuild command (after obtaining source snapshots)

```bash
python -m freeburg.tools.rebuild_fundamentals \
  --prices local/freeburg-fresh-001/spx/spx_weekly.csv \
  --fraser-dir /path/to/research/freeburg/data/fraser_sp500 \
  --govinfo-vintages local/govinfo_first_observed_vintages.csv \
  --govinfo-xls-dir local/freeburg-fresh-001/govinfo \
  --output local/rebuilt_fundamentals.csv \
  --report local/rebuilt_fundamentals_report.json
```

The **FRASER first-published CSVs are still provided from the user's existing research archive**. A clean stranger's clone cannot yet recreate them from a public, redistributable ready-made artifact. That is a remaining packaging/rights/automation task, not new method discovery.

## Explicit blockers before advertising one-command exact six-sleeve reproduction

1. Replace the last unlicensed/unverified source dependency or provide a user-local fetch path.
2. Check archival FRASER extraction rights and make those files self-contained for new users.
3. Diagnose 247/132 decision differences and reconcile availability assumptions before marking fresh-data modes benchmark-equivalent.
4. Provide true first-publication timestamps where possible; archive creation dates are only a delayed scenario.
5. Exact Heine DJ20/CRB historical sources: unresolved. Label separate proxy prominently.

**The completed original benchmark, a free-download research profile, and a licensed-source substitute must remain separate modes.**
