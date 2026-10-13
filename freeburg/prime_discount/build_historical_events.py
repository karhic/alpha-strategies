from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from freeburg.primas.build_historical_events import _iso

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
SPX = DATA / "spx_weekly_2026-08-07.csv"
RATES = DATA / "rate_change_events_2026-08-07.csv"
OUT = DATA / "prime_discount_benchmark_events.jsonl"


def asof_ffill(series: pd.Series, cal: pd.DatetimeIndex) -> pd.Series:
    return series.reindex(series.index.union(cal)).sort_index().ffill().reindex(cal)


def main() -> None:
    s = pd.read_csv(SPX)
    s["date"] = pd.to_datetime(s["date"])
    spx = pd.Series(pd.to_numeric(s["spx"]).to_numpy(), index=s["date"]).dropna().sort_index()

    ev = pd.read_csv(RATES)
    ev["date"] = pd.to_datetime(ev["date"])
    ev["value"] = pd.to_numeric(ev["value"], errors="coerce")
    ev = ev.dropna(subset=["date", "value"])

    prime0 = ev[ev["series"].eq("DPRIME")].drop_duplicates("date", keep="last").set_index("date")["value"]
    disc0 = ev[ev["series"].eq("INTDSRUSM193N")].drop_duplicates("date", keep="last").set_index("date")["value"]
    cal = spx.index
    prime = asof_ffill(prime0, cal)
    disc = asof_ffill(disc0, cal)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as fh:
        for d in cal:
            if pd.isna(prime.loc[d]) or pd.isna(disc.loc[d]):
                continue
            rows = [
                {"source":"frozen_2026_08_07","dataset":"index.sp500.level.1w","instrument":"SPX","event_time":_iso(d,0),"available_at":_iso(d,20,0),"payload":float(spx.loc[d])},
                {"source":"frozen_2026_08_07","dataset":"rates.bank_prime.1w","instrument":"US","event_time":_iso(d,0),"available_at":_iso(d,20,0),"payload":float(prime.loc[d])},
                {"source":"frozen_2026_08_07","dataset":"rates.discount_rate.1w","instrument":"US","event_time":_iso(d,0),"available_at":_iso(d,20,0),"payload":float(disc.loc[d])},
            ]
            if d >= pd.Timestamp("1970-01-02"):
                rows.append({"source":"benchmark_calendar","dataset":"clock.weekly.freeburg","instrument":None,"event_time":_iso(d,0),"available_at":_iso(d,20,1),"payload":None})
            for row in rows:
                fh.write(json.dumps(row, sort_keys=True) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
