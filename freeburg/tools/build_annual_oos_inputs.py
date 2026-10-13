"""Generate local weekly source returns from existing Freeburg OOS research.

Requires user's already researched edge-research-scratchpad checkout. Reads
its established OOS code; never changes strategy rules. Fetches the AGG
benchmark from Yahoo into user-local output. Do not redistribute provider
market data without confirming source rights.
"""
from __future__ import annotations
import argparse
import importlib.util
from pathlib import Path
import json
import pandas as pd
import requests


def build(research_dir: Path, output: Path,
          start: str = "2014-01-03", end: str = "2026-08-07") -> dict:
    if output.exists():
        raise FileExistsError(output)
    module_path = research_dir / "test_post2013_and_leverage_v4.py"
    if not module_path.exists():
        raise FileNotFoundError(module_path)
    spec = importlib.util.spec_from_file_location("freeburg_oos_v4", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    ret, signals, stock, bill = module.v2.build_oos(90)
    endpoint = "https://query1.finance.yahoo.com/v8/finance/chart/AGG"
    response = requests.get(endpoint, params={
        "period1": 1377907200, "period2": 1787000000,
        "interval": "1d", "events": "history"},
        headers={"User-Agent": "Mozilla/5.0 Freeburg local research"},
        timeout=70)
    response.raise_for_status()
    p = response.json()["chart"]["result"][0]
    dates = pd.to_datetime(p["timestamp"], unit="s", utc=True).tz_convert(None).normalize()
    closes = pd.Series(p["indicators"]["adjclose"][0]["adjclose"],
                       index=dates, dtype=float).dropna().sort_index()
    agg = closes.resample("W-FRI").last().pct_change().shift(-1)
    idx = ret.loc[start:end].index
    out = pd.DataFrame({
        "Primas": ret["Primas"],
        "Triple40": ret["Triple40"],
        "PuShen": ret["PuShen"],
        "Competitive": ret["Competitive"],
        "stock": stock,
        "rf": bill.clip(lower=0) / 100 / 52,
        "agg": agg}, index=idx)
    out.index.name = "date"
    if out.isna().any().any():
        raise ValueError("Missing OOS inputs: refusing to fill or drop silently")
    if len(out) < 650:
        raise ValueError(f"Unexpectedly short OOS sample: {len(out)}")
    output.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(output)
    return {"rows": len(out),
            "first": out.index.min().date().isoformat(),
            "last": out.index.max().date().isoformat(),
            "output": str(output),
            "research_source": str(module_path),
            "benchmark": "AGG Yahoo adjusted-close weekly",
            "status": "USER_LOCAL_SOURCE_SNAPSHOT_THIRD_PARTY_RIGHTS_NOT_CLEARED"}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--scratchpad-research", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    print(json.dumps(build(args.scratchpad_research, args.output), indent=2))


if __name__ == "__main__":
    main()
