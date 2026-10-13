# Automated Freeburg IBKR paper trading — deployed 12 Oct 2026

**Mode: PAPER ACCOUNT ONLY. No production/live-money orders.**

The VPS now schedules a **single SPY target-weight rebalance** from the four
original Freeburg strategy decisions, plus an independent shadow calculation,
at **10:00 New York time Monday**, with **Tuesday 10:00** as a retry if
Monday's attempt failed. Systemd handles daylight saving time automatically.
No phone, VNC session, or IBKR market-data subscription is required when the
authenticated Gateway remains running.

The service installed on this VPS is:
- `freeburg-paper-trade.timer`: enabled, next run Monday, October 12,
  2026, 14:00 UTC (plus up to a 60-second randomized delay).
- `freeburg-paper-trade.service`: invokes
  `python -m freeburg.deploy.paper_live --send-paper` with
  `FREEBURG_PAPER_SEND=YES`.
- The capture timer continues to obtain the latest Friday-sourced data.
- IB Gateway communicates with IBKR independently of the user's phone.

## Execution mechanics

1. Refuse unless the source snapshot and original strategy implementation
   agree with independent calculation, all four complete, Friday decision
   is recent, and no stale source capture was used.
2. Require one account whose identifier begins `DU` (**IBKR paper prefix**).
3. Fetch actual paper equity, SPY position, buying power and outstanding
   SPY orders from IBKR Gateway on localhost:4002.
4. Fetch a fresh **SPY 1-minute intraday price from Yahoo Finance**,
   rejecting quotes more than 25 minutes old, past-session quotes, market
   holidays, or off-hours operation.
5. Calculate 0/25/50/75/100% SPY target based on four sleeves. Whole shares
   only, long-only, maximum rebalance order **30% of paper equity**.
6. Write a durable claim file **before** sending an order; do not retry
   the same Friday decision after ambiguous network failure.
7. Transmit a single DAY market order restricted to regular trading hours.
8. Record the order ID and the status obtained after a short wait.

**Warning:** This is an early **paper prototype**, not suitable for
production capital. IBKR may reject an order because Gateway API
read-only mode remains enabled; order rejection is logged in systemd and
requires operator inspection. There is no fill reconciliation/recovery
beyond the preclaim and broker-side order checks yet.

Historical macro/fundamental series in the first snapshot are a retrospective
initialization. The first actual forward run starts from the observed October
2026 snapshot, not a fully PIT-reconstructed historical archive. This is
fine for a labeled *forward paper test*, but it should never be represented
as a verified historical out-of-sample fill.

## Verify

```bash
systemctl list-timers --all | grep freeburg
cat /var/lib/freeburg/captures/latest.json
journalctl -u freeburg-paper-trade.service -n 80 --no-pager
ls -lh /var/lib/freeburg/paper_runs
```

To suspend paper order automation immediately:
```bash
sudo systemctl disable --now freeburg-paper-trade.timer
```

The Gateway listens on TCP 4002 on all interfaces; IBKR's trusted IP
restrictions and the hosting-provider firewall should be confirmed
to restrict this port to localhost. Never expose the authenticated API
over the public Internet. VNC remains accessible only through SSH tunnel.
