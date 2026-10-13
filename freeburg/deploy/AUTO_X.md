# Freeburg automated X / Twitter signal posts

**Deployed on the VPS, 12 October 2026.**

This publishes the same *four-sleeve forward signal* generated from live
source captures and validated twice: once by the original causaltrader
strategy classes, and once independently by the numerical reference.
A failure of data acquisition or disagreement between engines prevents posts.

## Current status

- VPS timer `freeburg-x.timer` **enabled**, scheduled Friday 23:50 UTC
  following the normal 23:30 UTC capture, plus Monday 08:30 UTC fallback.
- Service `freeburg-x.service` already **successfully generated a test draft**.
- Output: `/var/lib/freeburg/x/drafts/2026-10-09.json`.
- **No X post has been sent.** Posting is gated behind an owner-configured
  X developer app with write permissions and its four user-auth credentials.
  Running the service without credentials only creates a local draft.

## First draft (2026-10-09 decision)

> Freeburg 4 | week ending 2026-10-09
>
> Primas OFF / Triple-40 OFF
>
> Pu Shen ON / Competitive OFF
>
> Model allocation: 25% SPY / 75% cash
>
> Observed: 12 Oct 2026 UTC. Research/paper signals; not investment advice.

The JSON includes cryptographic SHA-256 hashes of the exact source
snapshot manifest, the canonical engine's output and each raw provider
manifest. Every post is thus linked to a stored as-of source record.

## Enable public posting

1. Create/authorize your own X developer application with **Read and Write**
   permission for the account that will publish Freeburg signals. Make sure
   its API billing/access plan permits `POST /2/tweets`.
2. Obtain consumer API key+secret and OAuth 1.0a user access token+secret.
3. On the VPS, create a root-owned `/etc/freeburg/x.env` with permissions
   `0600` containing:

   ```dotenv
   X_ENABLE_POSTING=YES
   X_API_KEY=...
   X_API_SECRET=...
   X_ACCESS_TOKEN=...
   X_ACCESS_TOKEN_SECRET=...
   ```

   Never add this file to Git; never send keys to a chat. The systemd unit
   imports the file optionally via `EnvironmentFile=-/etc/freeburg/x.env`.
4. Install `tweepy` into `/opt/freeburg-venv` if missing.
5. Restart only `freeburg-x.service` to attempt the current week's post,
   or let the enabled timer run. The `x_forward.py` caller will not
   attempt to send if authorization or credentials are missing.

## Duplicate/uncertain-failure handling

- One post per Friday decision: `/var/lib/freeburg/x/posts/YYYY-MM-DD.json`.
- Before calling X, write a durable `CLAIMED_BEFORE_X_REQUEST` record.
- If X times out or returns ambiguous success, preserve
  `POSTING_UNCERTAIN_MANUAL_RECONCILIATION_REQUIRED` without automatically
  sending the tweet twice. Inspect X and manually reconcile.
- Monday's timer acts as a fallback only if the same Friday has not already
  been posted or claimed.

## Diagnostics

```bash
systemctl list-timers --all | grep freeburg
systemctl status freeburg-x.timer --no-pager
journalctl -u freeburg-x.service -n 40 --no-pager
ls /var/lib/freeburg/x/drafts /var/lib/freeburg/x/posts
```

**Known limitation:** these are forward paper/research signals generated
from an initial retrospectively downloaded historical lookback.
They are not a fully PIT-certified historical record. Source revisions
and data-provider outages remain possible; the system blocks absent or
disagreeing signals rather than fabricating data.
