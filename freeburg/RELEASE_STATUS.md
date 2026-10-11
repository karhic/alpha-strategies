# Freeburg release-candidate status — 11 October 2026

This project has **five completed historical decision replays** and a working
free-access data-acquisition research pipeline. It is **not** an exact
license-cleared, point-in-time, six-sleeve reproduction requiring no external
historical files. Do not represent it as such.

## Tested on the connected VPS

Install the generic engine `karhic/causal-trading-engine` into the environment;
install `freeburg/requirements-data.txt`. From this repository's root:

```bash
python -m freeburg.reproduce_available \
  --mode baseline \
  --output-dir local/replays/baseline-001
```

The output contains one canonical causal engine ledger per strategy, plus a
`run_manifest.json`. It executes **existing** strategy rules rather than a
second backtest interpretation.

| Sleeve | Benchmark strategy actions | Status |
| --- | ---: | --- |
| Primas | 2,232 | Complete benchmark replay |
| Triple-40 | 2,244 | Complete benchmark replay |
| Pu Shen | 2,197 | Complete benchmark replay |
| Competitive Returns | 2,253 | Complete benchmark replay |
| Prime/Discount | 2,283 | Complete benchmark replay |
| Heine | N/A | Rule implemented; original underlying index source not established |

### Rebuilding fundamentals and replaying them

For a user with the existing FRASER research archive and source snapshots:

```bash
python -m freeburg.reproduce_available \
  --mode sources \
  --output-dir local/replays/independent-fundamentals-001 \
  --fresh-snapshot local/freeburg-fresh-001 \
  --fraser-dir /path/to/edge-research-scratchpad/research/freeburg/data/fraser_sp500 \
  --govinfo-vintages local/govinfo_first_observed_vintages.csv \
  --govinfo-xls-dir local/freeburg-fresh-001/govinfo
```

The source mode retains **frozen macro input columns** from the original
benchmarks. It does **not** certify that FRED/BLS is independent or PIT in this
mode. Historical earnings and dividend vintage timing is a documented
sensitivity assumption. GovInfo archive catalog date is **not necessarily the
true original publication date**.

Source-mode runtime test:

| Sleeve | Rebuilt actions | Matching reference dates | Changed target weights |
| --- | ---: | ---: | ---: |
| Pu Shen | 2,197 | 2,197 | 100 (4.55%) |
| Competitive Returns | 2,253 | 2,253 | 41 (1.82%) |

Use `python -m freeburg.tools.compare_replay_actions --baseline <baseline-ledger> --rebuilt <source-ledger>`
to repeat this comparison. These are **actual causal strategy actions**
from the runtime; they supersede earlier spreadsheet-only signal comparison
figures that used a different observation window.

## Acquisition

```bash
python -m pip install -r freeburg/requirements-data.txt
python -m freeburg.bootstrap \
  --output-dir local/freeburg-fresh-001 \
  --enable-yahoo-spx \
  --govinfo-start 2010-09 --govinfo-end 2026-09
```

- Federal Reserve H15 and NBER macrohistory: user-side fresh fetch works.
- S&P ^GSPC: user-side opt-in Yahoo chart fetch works and matches the legacy
  price columns exactly across 2,959 overlapping weeks. Vendor rights **not
  cleared for redistribution**, and automated access may change.
- GovInfo: 191 of 193 issues in 2010–2026 could be downloaded and processed
  with manual parser fixes. Two issues remain missing; underlying S&P data
  retain third-party provenance and require rights analysis.
- FRED DPRIME and IMF-origin INTDSRUSM193N: downloader added, requires user's
  `FRED_API_KEY`; rate parity tested using already saved FRED snapshots,
  **not** freshly acquired FRED keys.
- Pre-2010 FRASER fundamentals: the already researched archived observations
  are consumed directly; source-archive re-download and automated extraction
  on a stranger's machine is not independently completed.
- Heine: no freely distributable exact DJ20 bond/CRB historical provider
  established. The current proxy is **not** original exact replication.

## Explicit exit gates for a full six-sleeve product

1. Verify a legally usable acquisition/redistribution route for all required
   underlying proprietary series or make the downloaded rights restrictions
   unambiguous and user-local.
2. Eliminate frozen remaining rate/CPI/CP columns from the *source* replay
   using approved independent downloads and run the entire six-sleeve sample.
3. Establish justified first-publication/vintage timings; archival dates are
   an **availability scenario**, not true historical market publication timestamps.
4. Address the Heine original bond and commodity indexes; do not present proxy
   performance as an exact historical result.
5. Verify cash/bond total returns and performance accounting downstream from
   the ledger; a decision-only replay alone does not certify CAGR or drawdown.

The **five-sleeve baseline** is a viable transparent research deliverable
right now. Calling all six sleeves perfectly reproducible from fresh free
downloads would be unsupported.
