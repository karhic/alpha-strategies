# IBKR SPY paper trading — staged order entry

A **simple paper-only order planner** is implemented in
[`ibkr_paper.py`](ibkr_paper.py). It computes a single SPY rebalance from
the four-sleeve audited signal, current paper equity and current SPY shares,
then optionally transmits a paper-market order. This is intentionally a
lightweight pilot, **not** an unattended production execution service.

### Verified in code

- Accepts only TWS paper (7497) or IB Gateway paper (4002), never the
  default live ports.
- Requires exactly one accessible IBKR account with the paper prefix
  `DU`; refuses other accounts.
- Defaults to no order submission.
- Reconciles current shares, account equity, qualified SPY contract,
  outstanding SPY API orders and available market quote.
- Calculates whole-share target from 0/25/50/75/100% sleeve allocations.
- Refuses stale signal (more than eight days) for order submission,
  outstanding SPY orders, short/fractional positions and excess notional.
- Requires a separate opt-in environment variable, explicit account number,
  and explicit `PAPER_ONLY` acknowledgement before *any* order can be sent.
- Writes a local result JSON file with action and quantity; refuses
  overwriting the same result path.

### First connection (no orders)

Install the API client into the environment:

```bash
python -m pip install ib_async
python -m freeburg.deploy.ibkr_preflight --host 127.0.0.1 --port 4002
```

**Actual VPS test:** on 12 October 2026, `ib_async` installed successfully
and the paper connection attempt returned `ConnectionRefusedError` because
neither authenticated TWS nor IB Gateway was listening on `127.0.0.1:4002`.
No brokerage credentials have been accessed and no orders were submitted.

### Dry-run rebalance after Gateway is authenticated

Supply a genuine, recent forward-looking four-sleeve signal JSON generated
from the actual causal strategy decision ledgers. **Do not use a historical
backtest signal as if it were a live one.**

```bash
python -m freeburg.deploy.ibkr_paper \
  --signal local/signals/latest.json \
  --host 127.0.0.1 --port 4002 \
  --output local/paper/2026-10-12-dryrun.json
```

No order is transmitted. The output indicates the tentative SPY shares to
buy/sell/hold. The script still reads current IBKR holdings and market data.

### Explicit paper-only submission

After validating the account and order preview, ensure the IBKR paper
account's API permits trading and deliberately issue:

```bash
IBKR_PAPER_ORDERS=YES python -m freeburg.deploy.ibkr_paper \
  --signal local/signals/latest.json \
  --host 127.0.0.1 --port 4002 \
  --confirm-account DUxxxxxxxx \
  --confirm-trading PAPER_ONLY --send-paper-order \
  --output local/paper/2026-10-12-order.json
```

Replace the account placeholder with the genuine paper-account identifier;
do not commit it or paste credentials into GitHub. The script stores a masked
identifier only. A single market order may transmit and fill immediately
when the market is open. The simple script **does not yet guarantee safe
recovery after network loss between order submission and local reporting**,
nor handle partial fills or closing foreign-currency cash balances. Always
inspect the paper-account order/activity screens.

IBKR configuration: log into **paper trading** in TWS/IB Gateway; enable
socket/API connections; port 7497 (TWS) or 4002 (Gateway). The read-only API
setting must be enabled for simple preflight, then disabled only if paper
order routing is intentional. See IBKR's own TWS API configuration guide.

### Immediate blocker

The VPS currently has **no authenticated IB Gateway or TWS session**. The
separately built market/fundamental acquisition pipelines do not yet produce
a synchronized live, actual-causal-engine four-sleeve decision ledger.
Until both are resolved, the planner can be unit tested but **cannot be
validated against real paper positions**. No orders have been placed.
