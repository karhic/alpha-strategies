# Freeburg VPS unattended staging — 12 October 2026

## Installed and running on the user's authorized VPS

- Stable deployed checkout `/opt/freeburg` (the GitHub integration branch).
- Isolated Python environment `/opt/freeburg-venv`.
- Immutable capture state `/var/lib/freeburg/captures/`.
- `freeburg-capture.timer`: **weekdays at 23:30 UTC**, systemd calendar;
  invokes `freeburg.deploy.weekly_daemon` via a oneshot service.
- `freeburg-paper-watch.timer`: **every 30 minutes**, checks the authenticated
  IBKR paper API on localhost port 4002, read-only. Writes
  `/var/lib/freeburg/paper_connection.json`.
- Boot-enabled `freeburg-xvfb.service`, `freeburg-vnc.service` and
  `freeburg-ibgateway.service`, so **after reboot** the virtual desktop,
  loopback-only SSH-tunneled VNC viewer and Gateway login UI will launch.
  Interactive Gateway login/MFA can still be required after reboot.
- The already-running Gateway and virtual desktop were left in place to avoid
  interrupting an authenticated session; these three units were enabled
  for next boot rather than forcibly started over those processes.

## Verified

The original standalone acquisition runner fetched the Fed, FRED, Yahoo
price, EPS and index-derived dividends into immutable timestamped folders
and successfully connected to the paper Gateway **without orders**.
`freeburg-paper-watch.service` successfully checked one paper account via
IBKR API after deployment and `freeburg-capture.service` was started for
a first test of the scheduled path.

## What is NOT automatic yet

**No strategy decision or IBKR order is submitted by the scheduled services.**
The four strategies still need a correctly as-of seeded lookback and a
forward-only weekly causal data join. The order planner has explicit,
interactive paper authorization rather than an unattended default.

This is "set and forget" for **capture and connectivity checks**, **not**
for a forward-running investment strategy. Social publishing is disabled
too. This distinction prevents unintentionally sending an unverified
retrospective signal to a brokerage account.

## Inspect operation

```bash
systemctl list-timers --all | grep freeburg
systemctl status freeburg-capture.timer freeburg-paper-watch.timer --no-pager
cat /var/lib/freeburg/paper_connection.json
cat /var/lib/freeburg/captures/latest.json
journalctl -u freeburg-capture.service -n 40 --no-pager
journalctl -u freeburg-paper-watch.service -n 40 --no-pager
```

Do not expose port 4002 or port 5901 to the public Internet. The VNC
service uses `-localhost`, requiring an SSH tunnel; gateway and paper
connection must stay behind VPS firewall/network policy. Gateway may require
periodic IBKR authentication; neither current nor future code stores the
user's IBKR credentials.

## Operations dependencies

The `/etc/systemd/system/freeburg-*.service` and
`/etc/systemd/system/freeburg-*.timer` files are deployment artifacts,
not automatically installed by cloning the repo. After future updates,
refresh `/opt/freeburg` from the integration branch and restart the one-shot
jobs as appropriate; do not force-restart IB Gateway during an authenticated
paper session.
