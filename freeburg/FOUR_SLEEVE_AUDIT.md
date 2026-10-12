# Freeburg 4: reproducibility and point-in-time release audit

**Scope:** Primas, Triple-40, Pu Shen, Competitive Returns. Prime/Discount and Heine are not part of the four-sleeve headline composite.

## What is actually reproducible

- The four strategy **decision rules** are implemented in Python and run through the generic `causal-trading-engine`.
- The `baseline` launcher now selects the four headline sleeves by default and emits a canonical action ledger per sleeve. It does not independently rebuild *all* original research inputs.
- Fresh S&P 500 closes can be downloaded and were verified against 2,959 matching legacy weekly observations with no price mismatch.
- The Fed H.15 and NBER commercial-paper data downloader works. The Primas and Triple-40 signal builders independently request these inputs. The historical Moody's Baa series ends in the H.15 archive in 2016, so the post-2013 Triple-40 research switches to a separately obtained continuation.
- Historical FRASER and post-2010 GovInfo S&P earnings and dividend values have been extracted and used for independent fundamental-series sensitivity tests. They **do not** produce exact decisions for Pu Shen or Competitive and rely on a pre-existing private research archive.
- The composite headline **9.21% CAGR / −19.20% max drawdown, 2014–August 2026** comes from the scratchpad's *separate* 90-day-lag forward-week return model, **not** directly from replay-ledger fills or independently reconstructed quarterly-vintage release timestamps. The README must not imply otherwise.

## Remaining risks, ordered by effect on scientific credibility

| Priority | Problem | Impact | Fix or release treatment |
| --- | --- | --- | --- |
| **Critical** | The published portfolio P&L is calculated in a separate research implementation rather than from the released causal decision ledgers and the same economic-accounting engine. | An independent clone of the project cannot automatically reproduce the headline CAGR, Sharpe and drawdowns by running the public replay command. | Build a ledger-to-accounting bridge, confirm weekly signal dates, cash-rate convention, dividends, 25/25/25/25 portfolio and weekly rebalance; assert exact parity to the published tables. Until then call the results an **independent research approximation**, not ledger-verified returns. |
| **Critical** | Weekly inputs are sometimes written with `event_time=Friday 00:00` and `available_at=Friday 20:00 UTC`, then executed at the Friday close in the economic model. | A post-close event cannot causally generate an order filled at the same Friday close. | Either shift execution and returns to the next tradable open/close, or supply documented pre-trade observation times with audited source availability. A one-week/next-session lag sensitivity is essential. |
| **High** | Pu Shen earnings and Competitive dividend signals rely on S&P-derived numbers that may have been revised or backfilled; historical release timestamps are not independently proven. | Earlier weeks could be informed by subsequently revised fundamentals. | Preserve source-vintage IDs, issue/capture date, measured release date, and conservative as-of policies; compare lag scenarios. Do not label derived archive dates as certified PIT timestamps. |
| **High** | Competitive uses BLS CPI series with a one-month availability assumption (the `MS + 1 month` construction); the source endpoint can deliver revised values. | It does not independently establish first-publication or original-vintage values. | Prefer historical CPI releases/ALFRED vintages where available; otherwise label as retrospectively revised CPI with a conservative assumed lag. |
| **High** | Pre-1971 NBER monthly CP is month-start stamped in one implementation; observations may be recorded *before* the source month ended. | Potential lookahead in the early training sample. | Delay monthly observations until after month-end unless contemporaneous provenance supports earlier stamping; compare published fingerprint after the correction. |
| **High** | The composite's four sleeves have no complete one-command fresh-input acquisition from an empty clone. FRASER pre-2010 data and source-specific CPI/Moody's/quarterly observations remain separate from the bootstrap. | A stranger cannot replicate the full published result simply from the README command. | Integrate cached-provider downloader and provenance, or require user-supplied source snapshots with an openly documented manifest; no need to restart OCR. |
| **Medium** | Price, index, vendor and published archival data redistribution terms have not been audited across all suppliers. | Source data may be user-downloadable but unsuitable for committing to a public repository. | Keep source downloads local, publish hashes, transformations and manifests; review vendor redistribution rights before committing original values. |
| **Medium** | Risk-on ETF/equity returns and risk-off rate accrual use simplified weekly cash/price/dividend accounting without explicit spread, transaction costs or realistic rebalance timing. | Actual executable performance could be lower. | Publish turnover, trading-cost stress scenarios and next-executable-session accounting. |

## Shipping classification

**Acceptable now:** public *four-sleeve research replication* with clear labels, code, documented comparisons, genuine sensitivity tests, and explicit source/execution limitations.

**Not acceptable yet:** calling this a clean-room, exact, verified PIT replication with one-command full historical P&L, or calling the 2014–2026 tables live/tradable results.

The remaining tasks are targeted engineering and provenance work. They do not require rediscovering any of the four published timing rules.

## Four-sleeve execution

```bash
python -m pip install -r freeburg/requirements-data.txt
python -m pip install -e /path/to/causal-trading-engine
python -m freeburg.reproduce_available --mode baseline --output-dir local/four-baseline-001
```

For explicitly including the non-headline historical Prime/Discount sleeve, pass `--sleeves primas triple40 pushen competitive prime_discount`.

For the independently reconstructed source-fundamentals replay, use `--mode sources` with the FRASER/GovInfo source inputs documented in [release status](RELEASE_STATUS.md). That mode is limited to Pu Shen and Competitive and still retains frozen macro columns.

## New accounting-decomposition and execution-latency check (12 October 2026)

We tested the **actual published 2014–7 Aug 2026 weekly OOS model** without
rewriting the original signal rules. For each strategy and each Friday, its
published return was compared against precisely two accounting alternatives:
(1) next-week stock price return plus dividend accrual and (2) Fed commercial
paper cash yield divided by 52 (with the documented 90% carry convention for
Triple-40 and Competitive Returns).

All **2,632 strategy-week returns** fit *exactly one of those accounting
branches*, to floating-point tolerance: maximum absolute residual at or below
**1.1 × 10⁻¹⁶**. This demonstrates that the published model's per-week return
accounting is internally consistent with the original stocks-versus-cash
rule. It is **not** an independent reconstruction of the underlying four
signal values or source publication dates; which branch was chosen is inferred
from already-computed returns, so it cannot validate trading causality.

We then froze the recovered risk-on decisions and applied a **one-full-week
positioning delay**, retaining the same Friday-to-Friday stock returns and
weekly cash alternatives. To compare like-for-like, the first OOS week is
removed from *both* baseline and delayed results.

| Metric | Existing weekly positioning | One-week-delayed positioning |
|---|---:|---:|
| Period | 2014-01-10–2026-08-07 | 2014-01-10–2026-08-07 |
| Weeks | 657 | 657 |
| CAGR | **9.20%** | **8.22%** |
| Max drawdown | **−19.20%** | **−22.10%** |
| Raw annualized weekly Sharpe | **1.08** | **0.96** |
| Terminal wealth | **3.04×** | **2.71×** |

This sensitivity shows the results depend somewhat, but **not catastrophically**,
on getting positioned promptly after observing the signal. Crucially a whole
week of latency is a deliberately harsh *stress scenario*, **not** a proper
next-market-open fill backtest. Historical timestamps and next-session fills
remain to be independently validated before claiming a complete PIT system.

### Reproduction

A simple CSV with the 2014–2026 model's weekly original returns (\`date\`,
\`Primas\`, \`Triple40\`, \`PuShen\`, \`Competitive\`, \`stock\`) is used with
a separate locally downloaded Federal Reserve commercial-paper series, columns
\`date\` and \`cp\` (annual interest-rate percentage).

\`python -m freeburg.tools.audit_oos_signal_delay --weekly-returns local/oos_weekly.csv --cp-weekly local/cp_weekly.csv --output local/delay_audit.json\`

This check was run against the source weekly returns already held on the
authorized research VPS. Do not confuse it with a clean-machine complete
input-data reconstruction. Local market source copies are not committed.

**New material finding:** [Post-2013 causal-strategy/research-model action mismatches](OOS_PARITY_FINDING.md) (256/2,632 sleeve-weeks; composite diagnostic 8.30% versus published 9.21% CAGR). This is now the primary release blocker.

**Confirmed high-priority PIT issue:** [Triple-40 monthly Baa source timing](TRIPLE40_MONTHLY_BAA_PIT_FINDING.md). The original OOS Baa month-start as-of convention uses future within-month information. Four-sleeve CAGR drops from 9.21% to 8.72% with the month-end convention, keeping everything else fixed. That reduction does *not* establish PIT certification for the other inputs.

**New earnings/dividend availability envelope:** [30–180-day versus archived-capture sensitivity](FUNDAMENTAL_AVAILABILITY_ENVELOPE.md). A 90-day lag may be overly conservative for an early published preliminary number but too optimistic for the exact hindsight-revised value. Verify earliest original releases rather than using final capture timestamps as publication dates.
