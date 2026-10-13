from __future__ import annotations

import json
from pathlib import Path

from freeburg.primas.build_historical_events import _spx_weekly, _cp_weekly, _fed_series, _iso

HERE = Path(__file__).resolve().parent
OUT = HERE / "data" / "triple40_benchmark_events.jsonl"


def main() -> None:
    spx = _spx_weekly()
    cal = spx.index
    cp = _cp_weekly(cal)
    baa = _fed_series("RIMLPBAAR_N.WF").reindex(cal).ffill()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as fh:
        for d in cal:
            if any(x != x for x in (spx.loc[d], cp.loc[d], baa.loc[d])):
                continue
            rows = [
                ("benchmark_public_sources", "index.sp500.level.1w", "SPX", float(spx.loc[d]), 0),
                ("benchmark_public_sources", "rates.moody_baa.1w", "US", float(baa.loc[d]), 0),
                ("benchmark_public_sources", "rates.commercial_paper.3m.1w", "US", float(cp.loc[d]), 0),
                ("benchmark_calendar", "clock.weekly.freeburg", None, None, 1),
            ]
            for source, dataset, instrument, payload, minute in rows:
                available = _iso(d, 20, minute)
                event = {
                    "source": source,
                    "dataset": dataset,
                    "instrument": instrument,
                    "event_time": _iso(d, 0),
                    "available_at": available,
                    "payload": payload,
                }
                fh.write(json.dumps(event, sort_keys=True) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
