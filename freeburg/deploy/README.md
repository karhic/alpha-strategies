# Freeburg 4 — deployment staging (NOT live trading)

The public research backtest is a **simulated, not fully PIT-certified** study.
Deployment has intentionally separate gates.

## Stage 0: Container
```bash
docker compose -f compose.freeburg.yml build
docker compose -f compose.freeburg.yml run --rm freeburg
```
Offline health check only. No account credentials are needed. Docker/Podman
must be installed by the operator; this repository does not silently install
privileged services on their machine.

## Stage 1: Existing causal-engine ledger -> weekly signal
Supply four canonical **recent, real as-of Friday** JSONL action ledgers,
named `primas.jsonl`, `triple40.jsonl`, `pushen.jsonl`,
`competitive.jsonl`. Each must have the *same* most recent decision time.
The snapshot refuses to proceed if any are missing, stale (>8 days), or
inconsistent. `spy_target_weight` is 0%, 25%, 50%, 75%, or 100%, with
25% equally allocated to each active sleeve.

Produce a **draft X post**, no network/posting:
```bash
PYTHONPATH=. python -m freeburg.deploy.publish_x \
  --ledger-dir local/real-asof-ledgers \
  --output-dir local/x-drafts
```
A draft records source-ledger hashes. Actual posting is *off by default*,
requires `--post`, `X_ENABLE_POSTING=YES` and explicit user-owned X API
credentials. Do not commit credentials. **Do not use archive research ledgers
as live signals**: their historical fundamental observations were not
confirmed to be available at the apparent decision time.

## Stage 2: Read-only IBKR PAPER preflight
Run IB Gateway/TWS with paper trading enabled on the operator's own machine,
configure read-only API, and verify the account independently:
```bash
pip install ib_async
PYTHONPATH=. python -m freeburg.deploy.ibkr_preflight \
  --host 127.0.0.1 --port 4002 --client-id 71
```
4002 (Gateway) and 7497 (TWS) are standard paper default ports, but can
be changed in the IBKR UI. The preflight **cannot submit orders** and
masks account identifiers in output. It requires a separately running
and authenticated IBKR application; containerizing the authenticated
Gateway with its login/MFA lifecycle is a separate task.

## **Not implemented / deployment blockers**

- Live as-of fundamental source and release-time pipeline for all four
  sleeves, independent of historical later-revised data.
- IBKR event-driven target-to-order reconciliation, buying-power checks,
  idempotent order IDs, fill handling, restart recovery, and approval controls.
- Verified user paper account/contract permissions, cash currency, market
  data entitlements and SPY order-routing policy.
- Live market-schedule and after-Friday-close decision triggers.
- End-to-end paper rehearsal followed by **separately approved** production
  trade/order authorization.

A backtested `target_spy_weight` is **NOT an instruction to send an order**.
No live or paper orders are routed by these tools.

## Security and operations
Never store secrets, API tokens, Gateway passwords or MFA codes in Git.
Store local `local/` state on a persistent volume, with restricted filesystem
permissions. Social publishing failure must not affect trading. Every signal
snapshot includes provenance and hash pointers for later verification.
