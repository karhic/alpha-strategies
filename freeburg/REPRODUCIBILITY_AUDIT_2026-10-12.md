# Four-sleeve reproducibility audit — 12 October 2026

## Reproduced now, against saved original quarterly input

We performed a complete deterministic local rerun from the checked-in source-to-return calculator in `freeburg/tools/reproduce_four_from_sources.py`, using a separately retained research quarterly CSV, checked-in frozen historical weekly price/macro sources, and freshly acquired FRED BAA/AGG market downloads. **This verifies computational reproducibility at these exact inputs, not original historical data availability or live execution.**

- Decision dates: 658 Fridays, 2014-01-03 to 2026-08-07.
- Assumptions: 90 calendar days after quarter end for historical EPS and dividends; BAA month-end observation timestamp; Friday close to next Friday close stock return; CP carry; zero costs.
- Composite: **8.7173588178% CAGR**, **-19.1981385323% maximum drawdown**, **2.8795233777x terminal wealth**.
- SPX benchmark: 13.9899544549% CAGR. Modeled 60/40: 9.3991444575% CAGR.
- `weekly_returns.csv` SHA-256: `7613e633b1af328acd9f41d4f05112209168153a87cfa41097631db8d01a85ce`.
- Quarterly private-source CSV SHA-256: `7626b7e71051d7b37363afa0c74100e6a315b6de39b8908a61792dad2cbe01c1`.
- See each `run_manifest.json` for all five input checksums. Third-party source files are deliberately **not** committed to this public-candidate repository.

## Honest certification status

**Model reproduction: verified on one VPS with the stated inputs.**

**Fully independent, unaffiliated clean-room reproduction: not yet verified.** The historic S&P quarterlies needed for exact numerical equality are not redistributed, and acquisition from public archives has gaps. Provider data can change on later download.

**Historical point-in-time signals: not certified.** A retrospective vendor snapshot can contain later revisions, regardless of a 90-day lag. Month-end BAA is a conservative sensitivity scenario, not proof of actual first-release timestamps. Some CPI and rate histories are similarly not independently vintage-verified.

**Tradable net P&L: not certified.** Historical Friday decisions depend on observations available only after the close, but the model takes Friday-close-to-next-Friday-close returns. Execution must be rebuilt from next-session tradable prices and actual order assumptions. No broker fills, taxes, spread or slippage included.

**Therefore do not present 8.717% as an independently point-in-time-certified or executable CAGR.** The 9.2138% historical month-start BAA result is a historical diagnostic with an identified lookahead mechanism, *not* the release's recommended case.

## Required evidence to close scientific certification

1. Historical data vintage table with actual first release **timestamp**, original unrevised EPS/dividend/CPI/BAA value, provider reference, and capture artifact hash for each signal observation.
2. A strict as-of replay that rejects any observation when `available_at > decision_time`, with automated proofs against leakage and differences to the retrospective research series.
3. Stock/cash/bond return accounting based on genuinely executable next-session prices, including realistic costs and handling of market holidays, dividends and splits.
4. Machine-checkable exact parity between the causal strategy engine's action ledger and the backtest/accounting system, including portfolio rebalancing and immutable code/data input digests.
5. Successful unauthenticated fresh clone and complete historical-source rebuild, subject to provider terms. Tests/CI should use permitted immutable fixtures and verify published result hashes; the source archive is currently an external dependency.

The Docker monitor clean-start proof is **operational** reproducibility for current signals, not evidence that these five scientific gates are met.
