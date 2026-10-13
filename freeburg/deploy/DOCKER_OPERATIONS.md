# Docker deployment on the Freeburg VPS — 12 October 2026

Docker Engine **29.1.3** and Docker Compose **2.40.3** were installed
on Ubuntu 24.04 ARM64 (Hetzner VPS). A real image has been built from
`Dockerfile.freeburg`, and the `freeburg-monitor` service in
[`compose.monitor.yml`](../../compose.monitor.yml) is running under Docker
with **restart: unless-stopped**.

### Confirmed in the live container logs

- Source capture: **OK**
- Four original causal strategy classes: **agree with shadow calculation**
- Current model allocation: **25% SPY**
- IBKR Gateway connection: **OK (one paper account)**
- Paper order permission: **OFF**
- X publishing permission: **OFF**

The monitor runs every 30 minutes, with a read-only bind mount of existing
snapshot state, a read-only root filesystem, all Linux capabilities dropped,
and no X API secrets or broker order credentials. It uses the host network
solely so it can check the existing loopback Gateway at port 4002. It runs
with UID 0 only to read the existing mode-0600 root-owned snapshot manifests.
It cannot write host snapshots or call Docker's control socket.

**Do not confuse the Docker monitor with a migrated execution system.**
The existing VPS systemd timers *still* own data downloads, paper-order
attempts and X drafts. We deliberately have **not** enabled second copies
of those jobs inside Docker because doing so could double-place paper orders
or duplicate public posts. This is stage one of safe Docker migration.

### Operations

```bash
docker compose -f compose.monitor.yml ps
docker compose -f compose.monitor.yml logs --tail 25 freeburg-monitor
docker compose -f compose.monitor.yml restart freeburg-monitor
```

### Remaining for full containerization

Move the three existing systemd jobs to Docker Compose one-shot services
**one at a time**, preserving the schedule and persistent
`/var/lib/freeburg` state, then verify on a dry run before switching
off their original systemd unit. A canonical-strategy job must carry
the causaltrader engine implementation into the container, pinned to
the tested engine revision; the monitoring image doesn't need it.
The authenticated graphical IB Gateway is intentionally left on the VPS,
because restarting it can require user login and 2FA.

**Never automatically start the paper-trading service inside two separate
runtimes.** Any future switch must preserve the order-claim files and
leave exactly one scheduler responsible for orders.
