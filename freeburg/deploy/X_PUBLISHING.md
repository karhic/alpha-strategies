# Freeburg weekly forward signals on X — VPS deployment

**Installed: 12 October 2026.** The VPS now has a systemd X-publishing
service and weekly timer. A validated **draft was generated** from the
Friday 9 October snapshot: Primas OFF, Triple-40 OFF, Pu Shen ON,
Competitive OFF; target **25% SPY / 75% cash**.

### Current activation status

**Automatic draft generation: ENABLED. Real X publishing: DISABLED until
an X developer account and user-authorized API keys are connected.**

An actual tweet has **not** been sent. No X credentials were found on
the VPS. The current private configuration file
`/etc/freeburg/x.env` contains only `X_ENABLE_POSTING=NO` and is
restricted to root permissions 0600.

### Source and posting rules

Every post is derived from the **same frozen market, EPS, and dividend
capture** already used by the Freeburg VPS paper-trading prototype. The
actual causaltrader strategy classes must match the independent indicator
implementation across all four sleeves. The captured Friday must be
recent, the source hash manifests must exist, and weekly 0/25/50/75/100%
SPY exposure must be internally consistent.

Posts are explicitly described as **research/paper signals**—not
unverified real-money trades or guaranteed performance. Format:

```text
Freeburg 4 | week ending 2026-10-09
Primas OFF / Triple-40 OFF
Pu Shen ON / Competitive OFF
Model allocation: 25% SPY / 75% cash
Observed: 12 Oct 2026 UTC. Research/paper signals; not investment advice.
```

The draft contains SHA-256 hashes for exact source manifests and the
strategy signal. This is an auditable forward record, with the caveat
that *initialization* uses retrospectively downloaded historical inputs.

An atomic per-Friday claim file is written **before** calling X, so a
network timeout after posting does not automatically create duplicates.
Uncertain outcomes need manual reconciliation (check X's account timeline
before authorizing retries). Existing published/claimed week files stop
subsequent weekly attempts for the same Friday.

### VPS scheduling and inspect commands

The enabled `freeburg-x.timer` runs the
`freeburg-x.service` after Friday's usual
23:30 UTC capture:

- Saturday **00:15 UTC** (primary publish window).
- Saturday **01:15 UTC** (retry only if no post claim was made).
- Monday **07:00 UTC** (late recovery when a Friday capture was unavailable).

All times are UTC. Publishing requires a successful **completed Friday**
capture; if source validation fails, **no post is sent**. A duplicate Friday
is not posted again. The first service run on 12 October completed
successfully in **draft-only** mode.

```bash
systemctl list-timers --all | grep freeburg-x
cat /var/lib/freeburg/x/drafts/2026-10-09.json
journalctl -u freeburg-x.service -n 30 --no-pager
ls /var/lib/freeburg/x/posts/
```

### User-side one-time X authorization

1. Visit the **X Developer Portal**: https://developer.x.com/en/portal/dashboard
2. Create/select an app in a developer project with **Read and Write**
   permissions and user authentication.
3. Generate app **API Key/Secret** and user **Access Token/Secret** (OAuth 1.0a
   user context); regenerate user tokens after enabling write permission.
4. Store them **only on your VPS** in `/etc/freeburg/x.env` using a
   root-only interactive editor. Do **not** send credentials to ChatGPT,
   paste them into public chats, or commit them to Git.
5. When the app has the appropriate posting API entitlement, set
   `X_ENABLE_POSTING=YES` in that environment file.
6. Trigger `systemctl start freeburg-x.service` to try the current
   *recent* Friday draft; inspect `/var/lib/freeburg/x/posts/` for
   `POSTED` and the returned X post ID.

Expected `/etc/freeburg/x.env` variable names:

```ini
X_ENABLE_POSTING=YES
X_API_KEY=your_app_key
X_API_SECRET=your_app_secret
X_ACCESS_TOKEN=your_user_access_token
X_ACCESS_TOKEN_SECRET=your_user_access_token_secret
```

Protect this file with `chmod 600 /etc/freeburg/x.env`. API quota,
access tiers and posting prices can change; check your actual X developer
dashboard for permissions and billing.

### Stop publishing

```bash
sudo systemctl disable --now freeburg-x.timer
```

### Separation from trading

X posts do not submit IBKR orders. IBKR trading failures or a disconnected
Gateway cannot alter an already archived signal, and an X API failure
cannot change SPY positions. The internal X record represents a model
target allocation, not a confirmed broker fill.
