# Code licensing and market-data policy

Freeburg code (excluding the separately versioned CausalTrader dependency, which is installed directly from its upstream source) is
licensed under the [MIT License](LICENSE). This grant covers the project's
authored code and documentation, **not third-party source datasets**.

Original historical source CSVs formerly tracked in `freeburg/pushen/data/`,
`freeburg/competitive/data/`, and `freeburg/prime_discount/data/` have been
removed. They blend observations sourced from financial data providers,
Federal Reserve/NBER material, and historical S&P observations. The repository
intentionally does not grant anyone redistribution rights to those datasets.

**Reproducible public-data study:** download source material locally using
`docker compose run --rm freeburg freeburg.tools.public_reproduce`, or use
`docker compose up -d --build` for the live public-data monitor. Both workflows
keep downloaded market data in your local Docker volume, not Git.

**Historical sleeve archives:** older 1970–2013 archival replay helpers that
expect `*/data/pit_weekly_inputs.csv` or `prime_discount/data/*.csv` require
users to independently acquire or reconstruct those particular historical
source files. Those archived helper scripts do not run out of the box in the
public source-only checkout; their research results and methodological notes
are retained for transparency. The four-sleeve 2014–2026 reconstruction is
independently runnable using the public download command above.

Third-party data providers, exchanges and archives may impose their own access,
use and redistribution restrictions. Respect the terms of each source. A
reconstruction from modern public observations is not necessarily certified
point-in-time.
