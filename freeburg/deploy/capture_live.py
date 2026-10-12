"""Acquire immutable, timestamped Freeburg-4 source snapshots for a future live feed.

No trading, no tweets, no historical publication claims. The source documents
are downloaded to a local directory; the public repo retains only the code.
"""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import hashlib
import io
import json
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET
import pandas as pd
import requests

H15="https://www.federalreserve.gov/datadownload/Output.aspx?filetype=zip&rel=h15"
FRED={
    "BAA":"https://fred.stlouisfed.org/graph/fredgraph.csv?id=BAA&cosd=2000-01-01",
    "CPIAUCSL":"https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCSL&cosd=2000-01-01",
}
SPX="https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC"
WEEKLY={
    "cp":"RIFSPPNAAD90_N.WF",
    "treasury_10y":"RIFLGFCY10_N.WF",
    "treasury_bill_3m":"RIFSGFSM03_N.WF",
}
MAX_SIZES={"fed_h15.zip":110_000_000,"BAA.csv":2_000_000,
           "CPIAUCSL.csv":2_000_000,"spx.json":16_000_000}

def _tag(el):return el.tag.rsplit("}",1)[-1].lower()

def h15_weekly(raw:bytes)->dict[str,pd.Series]:
    """Extract only configured 3 H.15 weekly Fed series, retaining source dates."""
    found={}
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        for name in z.namelist():
            if not name.lower().endswith(".xml"):continue
            with z.open(name) as fh:
                for _,el in ET.iterparse(fh,events=("end",)):
                    if _tag(el)!="series":continue
                    identity=" ".join(f"{k}={v}" for c in el.iter() for k,v in c.attrib.items())
                    for key,needle in WEEKLY.items():
                        if needle.lower() not in identity.lower() or key in found:continue
                        vals={}
                        for e in el.iter():
                            if _tag(e) not in ("obs","observation"):continue
                            props={k.rsplit("}",1)[-1].lower():v for k,v in e.attrib.items()}
                            dt=props.get("time_period") or props.get("date") or props.get("time")
                            value=props.get("obs_value") or props.get("value")
                            try:
                                if dt and value is not None:
                                    v=float(value)
                                    if v > -9990:vals[pd.Timestamp(dt)]=v
                            except ValueError:continue
                        if vals:found[key]=pd.Series(vals).sort_index()
                    el.clear()
            if set(found)==set(WEEKLY):break
    missing=set(WEEKLY)-set(found)
    if missing:raise ValueError("Fed H15 missing required series "+str(sorted(missing)))
    return found

def _download(url:str,timeout=35)->bytes:
    """Retry transient provider failures; fail closed after three attempts."""
    import time
    last=None
    for attempt in range(3):
        try:
            r=requests.get(url,timeout=timeout,headers=({} if "fred.stlouisfed.org" in url else {"User-Agent":"Mozilla/5.0"}))
            r.raise_for_status()
            if not r.content:raise ValueError("Empty provider download")
            return r.content
        except (requests.exceptions.RequestException,ValueError) as error:
            last=error
            if attempt<2:time.sleep(2*(attempt+1))
    raise RuntimeError(f"Provider repeatedly unavailable: {url.split('?')[0]}") from last

def _persist(path:Path,body:bytes)->str:
    if len(body)>MAX_SIZES[path.name]:raise ValueError("Oversized provider response "+path.name)
    with path.open("xb") as f:f.write(body)
    return hashlib.sha256(body).hexdigest()

def _fred_csv(body:bytes,name:str)->pd.Series:
    df=pd.read_csv(io.BytesIO(body))
    date=next((k for k in ("observation_date","DATE","date") if k in df.columns),None)
    if date is None or name not in df:raise ValueError("Malformed FRED "+name+" CSV")
    frame=df[[date,name]].copy()
    frame[date]=pd.to_datetime(frame[date])
    frame[name]=pd.to_numeric(frame[name],errors="coerce")
    s=frame.dropna().set_index(date)[name].sort_index()
    if len(s)<30 or s.index.has_duplicates:raise ValueError("Insufficient FRED "+name)
    return s

def _spx_close(body:bytes)->pd.Series:
    chart=json.loads(body)["chart"]
    if not chart.get("result"):raise ValueError("Yahoo chart result missing")
    data=chart["result"][0]
    ts=pd.to_datetime(data["timestamp"],unit="s",utc=True).tz_convert(None).normalize()
    px=pd.Series(data["indicators"]["quote"][0]["close"],index=ts,dtype=float).dropna().sort_index()
    if len(px)<260 or (px<=0).any():raise ValueError("Insufficient or invalid SPX prices")
    return px

def _summary(series:pd.Series,asof:datetime)->dict:
    t=pd.Timestamp(asof.date())
    eligible=series[series.index<=t]
    if eligible.empty:raise ValueError("Series has no observations by acquisition date")
    return {"last_observation":eligible.index[-1].date().isoformat(),
            "last_value":float(eligible.iloc[-1]),"total_observations":len(eligible)}

def capture(dest:Path,now:datetime,*,h15_local:Path|None=None,spx_local:Path|None=None,
            baa_local:Path|None=None,cpi_local:Path|None=None)->dict:
    if now.tzinfo is None:raise ValueError("UTC-aware acquisition time required")
    now=now.astimezone(timezone.utc)
    if dest.exists() and any(dest.iterdir()):raise FileExistsError("Snapshot destination not empty")
    dest.mkdir(parents=True,exist_ok=True)
    spec=[
        ("fed_h15.zip",H15,h15_local),
        ("BAA.csv",FRED["BAA"],baa_local),
        ("CPIAUCSL.csv",FRED["CPIAUCSL"],cpi_local),
        ("spx.json",SPX+f"?period1=1672444800&period2={int(now.timestamp())+86400}&interval=1d&events=history",spx_local),
    ]
    hashes={}
    for name,url,local in spec:
        body=local.read_bytes() if local is not None else _download(url)
        hashes[name]={"sha256":_persist(dest/name,body),"source_url":url,
                      "source_kind":"EXPLICIT_LOCAL_INPUT" if local else "PROVIDER_DOWNLOAD"}
    data=h15_weekly((dest/"fed_h15.zip").read_bytes())
    data.update({
        "BAA":_fred_csv((dest/"BAA.csv").read_bytes(),"BAA"),
        "CPIAUCSL":_fred_csv((dest/"CPIAUCSL.csv").read_bytes(),"CPIAUCSL"),
        "spx":_spx_close((dest/"spx.json").read_bytes()),
    })
    latest={name:_summary(series,now) for name,series in data.items()}
    # An acquired file contains revised historical data. Only snapshot its
    # presently known observations with the actual acquisition timestamp.
    # A completed Friday price may only be used after the US market close,
    # conservatively Saturday UTC at the earliest.
    completed_friday=(pd.Timestamp(now.date()) if now.weekday()==4 and now.hour>=22
                     else pd.Timestamp(now.date())-pd.offsets.Week(weekday=4))
    reference=completed_friday.date()
    asof=pd.Timestamp(reference)
    checks={
        "fed_cp_recent":data["cp"].index.max() >= asof-pd.Timedelta(days=21),
        "fed_10y_recent":data["treasury_10y"].index.max() >= asof-pd.Timedelta(days=14),
        "fed_bill_recent":data["treasury_bill_3m"].index.max() >= asof-pd.Timedelta(days=14),
        "spx_close_recent":data["spx"].index.max() >= asof-pd.Timedelta(days=3),
        "baa_recent":data["BAA"].index.max() >= asof-pd.Timedelta(days=90),
        "cpi_recent":data["CPIAUCSL"].index.max() >= asof-pd.Timedelta(days=100),
    }
    manifest={
        "schema":"freeburg.live.market-capture.v1",
        "captured_at_utc":now.isoformat(),
        "target_completed_friday":reference.isoformat(),
        "sources":hashes,"series":latest,"freshness_checks":checks,
        "age_days_by_series":{k:int((asof-s.index.max()).days) for k,s in data.items()},
        "market_sources_ready":all(checks.values()),
        "fundamental_eps_dividends_ready":False,
        "signal_ready":False,
        "broker_trading_allowed":False,
        "source_provenance":"Official Federal Reserve H15, FRED-hosted BAA/CPI, Yahoo SPX market data. Hindsight-history not PIT",
        "blocker":"Current-date S&P quarterly EPS and dividends require a separately captured, authentic dated first-party workbook.",
    }
    (dest/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    return manifest

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-dir",required=True,type=Path)
    p.add_argument("--h15-local",type=Path)
    p.add_argument("--spx-local",type=Path)
    p.add_argument("--baa-local",type=Path)
    p.add_argument("--cpi-local",type=Path)
    a=p.parse_args()
    result=capture(a.output_dir,datetime.now(timezone.utc),h15_local=a.h15_local,
                   spx_local=a.spx_local,baa_local=a.baa_local,cpi_local=a.cpi_local)
    print(json.dumps({k:v for k,v in result.items() if k!="sources"},indent=2))
    if not result["market_sources_ready"]:raise SystemExit("Some market feeds are stale; no signal generated")
if __name__=="__main__":main()
