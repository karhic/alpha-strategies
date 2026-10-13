from __future__ import annotations

import io
import json
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, time, timezone
from pathlib import Path

import pandas as pd
import requests

UTC = timezone.utc
HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw"
OUT = HERE / "data" / "primas_benchmark_events.jsonl"
UA = "Mozilla/5.0 Freeburg Primas reproducible data build"
H15_ZIP = "https://www.federalreserve.gov/datadownload/Output.aspx?filetype=zip&rel=h15"
NBER_CP = "https://data.nber.org/databases/macrohistory/rectdata/13/m13002.dat"
YAHOO_SPX = "https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC?period1=0&period2=1800000000&interval=1d&events=history"


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _download(url: str, name: str) -> bytes:
    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / name
    if path.exists():
        return path.read_bytes()
    r = requests.get(url, headers={"User-Agent": UA}, timeout=120)
    r.raise_for_status()
    path.write_bytes(r.content)
    return r.content


def _fed_series(needle: str) -> pd.Series:
    raw = _download(H15_ZIP, "h15.zip")
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        for fn in zf.namelist():
            if not fn.lower().endswith(".xml"):
                continue
            with zf.open(fn) as fh:
                for _, elem in ET.iterparse(fh, events=("end",)):
                    if _local(elem.tag).lower() != "series":
                        continue
                    identity = " ".join(f"{k}={v}" for x in elem.iter() for k, v in x.attrib.items())
                    if needle.lower() not in identity.lower():
                        elem.clear()
                        continue
                    rows = []
                    for obs in elem.iter():
                        if _local(obs.tag).lower() not in {"obs", "observation"}:
                            continue
                        attrs = {k.rsplit("}", 1)[-1].lower(): v for k, v in obs.attrib.items()}
                        ds = attrs.get("time_period") or attrs.get("date") or attrs.get("time")
                        vs = attrs.get("obs_value") or attrs.get("value")
                        if ds is None or vs is None:
                            continue
                        try:
                            value = float(vs)
                        except ValueError:
                            continue
                        if value <= -9990:
                            continue
                        rows.append((pd.Timestamp(ds), value))
                    if rows:
                        return pd.Series(dict(rows)).sort_index()
                    elem.clear()
    raise KeyError(needle)


def _nber_cp() -> pd.Series:
    text = _download(NBER_CP, "nber_m13002.dat").decode("utf-8")
    x = pd.read_csv(io.StringIO(text), sep=r"\s+", header=None, names=["year", "month", "value"], engine="python")
    x = x.apply(pd.to_numeric, errors="coerce").dropna()
    x = x[(x.month >= 1) & (x.month <= 12)]
    idx = pd.to_datetime(dict(year=x.year.astype(int), month=x.month.astype(int), day=1))
    return pd.Series(x.value.to_numpy(float), index=idx).sort_index()


def _spx_weekly() -> pd.Series:
    raw = _download(YAHOO_SPX, "spx_yahoo.json")
    result = json.loads(raw)["chart"]["result"][0]
    idx = pd.to_datetime(result["timestamp"], unit="s", utc=True).tz_convert(None).normalize()
    close = result["indicators"]["quote"][0]["close"]
    return pd.Series(close, index=idx, dtype=float).dropna().sort_index().resample("W-FRI").last().dropna()


def _cp_weekly(calendar: pd.DatetimeIndex) -> pd.Series:
    monthly = _nber_cp()
    seed = monthly.reindex(monthly.index.union(calendar)).sort_index().ffill().reindex(calendar)
    old = _fed_series("H0.RIFSPPCM03_N.WF").reindex(calendar)
    modern = _fed_series("RIFSPPNAAD90_N.WF").reindex(calendar)
    cp = seed.copy()
    cp.loc[calendar >= pd.Timestamp("1971-04-09")] = old.loc[calendar >= pd.Timestamp("1971-04-09")]
    cp.loc[calendar >= pd.Timestamp("1997-09-05")] = modern.loc[calendar >= pd.Timestamp("1997-09-05")]
    return cp.ffill()


def _iso(d: pd.Timestamp, hh: int, mm: int = 0) -> str:
    return datetime.combine(d.date(), time(hh, mm), tzinfo=UTC).isoformat()


def main() -> None:
    spx = _spx_weekly()
    cal = spx.index
    cp = _cp_weekly(cal)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as fh:
        for d in cal:
            if pd.isna(cp.loc[d]):
                continue
            events = [
                {"source": "benchmark_public_sources", "dataset": "index.sp500.level.1w", "instrument": "SPX", "event_time": _iso(d, 0), "available_at": _iso(d, 20, 0), "payload": float(spx.loc[d])},
                {"source": "benchmark_public_sources", "dataset": "rates.commercial_paper.3m.1w", "instrument": "US", "event_time": _iso(d, 0), "available_at": _iso(d, 20, 0), "payload": float(cp.loc[d])},
                {"source": "benchmark_calendar", "dataset": "clock.weekly.freeburg", "instrument": None, "event_time": _iso(d, 0), "available_at": _iso(d, 20, 1), "payload": None},
            ]
            for event in events:
                fh.write(json.dumps(event, sort_keys=True) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
