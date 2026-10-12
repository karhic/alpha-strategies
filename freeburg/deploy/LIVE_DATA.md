# Freeburg live-source capture: operational status

**Implemented and live-tested on the authorized VPS, 12 October 2026.**
This creates **immutable data snapshots**, not trades, X posts, or a live
four-sleeve signal.

From the repository root, with `pandas`, `requests` installed:

```bash
python -m freeburg.deploy.capture_live \
  --output-dir local/captures/2026-10-12-a

python -m freeburg.deploy.assess_capture \
  --snapshot local/captures/2026-10-12-a \
  --output local/captures/2026-10-12-a/ingestion-status.json
```

The capture script downloads, *on demand*, four user-side provider files
(Federal Reserve H.15 XML ZIP, FRED BAA monthly CSV, FRED CPIAUCSL monthly
CSV and a Yahoo S&P 500 chart) and parses the six required non-fundamental
market/macro series. The manifest records the exact acquisition timestamp,
original provider URL, SHA-256 of each raw downloaded file, last observation
date/value, and per-series freshness flags. No market-data bytes are
committed. The audit fails if a downloaded file differs from its recorded
hash. Freshness thresholds are intentionally broad enough for monthly CPI
and the lagged published weekly commercial-paper series, but these thresholds
**do not certify original publication timing**.

## Verified test (2026-10-12 03:47 UTC)

| Input | Latest source observation | Freshness |
|---|---|---|
| S&P close | 2026-10-09 | Pass |
| Commercial-paper yield | 2026-09-25 | Pass (14 days behind Friday) |
| US Treasury 10Y yield | 2026-10-02 | Pass |
| Three-month T-bill yield | 2026-10-02 | Pass |
| Moody's Baa monthly | 2026-09-01 | Pass |
| CPIAUCSL monthly | 2026-08-01 | Pass |

All six market/macro inputs were successfully downloaded and the
source audit passed. Note some observations are not from the
target Friday; do **not** extrapolate or invent newer values.

### Important data semantics

- Historical data received **today** are retrospective provider datasets
  and can contain revisions. The acquisition timestamp is evidence of what
  this downloader received today, *not* proof of what was available on
  earlier dates.
- For future genuine live operations, keep successive capture snapshots
  rather than rewriting earlier values in place. At each decision Friday,
  only consume snapshots actually captured before that decision cutoff.
- A Friday close cannot be traded at Friday's close if the pipeline learns
  that closing price afterwards. Use the next executable session after the
  signal can be generated.
- Current S&P 500 quarterly as-reported EPS and dividends need a separate
  **original, dated S&P publication** and versioned ingestion. This is
  still a blocker to constructing both Pu Shen and Competitive signals from
  entirely verifiable live sources. We intentionally do **not** produce a
  synthetic substitute, freeze an old fundamental value indefinitely, or
  infer a trade from backfilled historical statistics.
- The current snapshot is **not** a weekly four-sleeve decision ledger.
  Neither the existing X publisher nor IBKR adapter is connected to
  source acquisition yet. Trades and X posting remain disabled.

The existing [deployment overview](README.md) and [PIT research audit](../FOUR_SLEEVE_AUDIT.md)
describe the remaining gates.
