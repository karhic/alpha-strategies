# Run Freeburg anywhere with Docker

Default installation requires Docker Compose and an Internet connection, but **no IBKR or X account**.

```sh
git clone --branch agent/freeburg-free-data-20261011 --single-branch https://github.com/karhic/alpha-strategies.git
cd alpha-strategies
docker compose up -d --build
docker compose logs -f freeburg
docker compose run --rm freeburg freeburg.deploy.status
```

The container captures Fed, FRED, Yahoo and AlphaQuery source snapshots, computes all four research signals using original causaltrader classes and checks an independent implementation. It runs once on startup and schedules capture at 23:30 UTC weekdays. State persists in the Compose-managed `freeburg-state` volume across restarts; it requires no access to the host filesystem, IBKR Gateway, privileged Docker socket or X API keys. No paper/live orders or public posts are sent.

```sh
docker compose run --rm freeburg freeburg.deploy.portable_once
docker compose down  # retains the state volume
docker compose down -v  # deletes source records: use ONLY if intentionally resetting
```

Note that first-run historical lookback is retrospectively fetched and **not** independently PIT-certified. Feeds can change or become unavailable; the run records failures and refuses full-signal readiness rather than silently substituting values. This project uses secondary data sources with provider-specific access terms. The `causaltrader` package is installed from an immutable, pinned public source revision during the Docker build. See `freeburg/requirements-engine.txt`.

**Publication access:** the GitHub repository and engine must be publicly readable for the literal HTTPS clone command to work for unauthenticated visitors. Private GitHub checkouts require the user's normal GitHub authentication and cannot be presented as zero-login public reproducibility.
