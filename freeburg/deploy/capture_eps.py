"""Acquire current S&P quarterly as-reported EPS with documented secondary provenance.

AlphaQuery is not S&P Dow Jones Indices. The provided 'announcement date' is
vendor metadata, not proven original S&P publication timing. Today's fetch
must not be backdated as an actual historical capture.
"""
from __future__ import annotations
import argparse,hashlib,io,json
from datetime import datetime,timezone
from pathlib import Path
import pandas as pd,requests
URL="https://www.alphaquery.com/stock/SPX.X/earnings-history"
def parse(body:bytes)->pd.DataFrame:
    tables=pd.read_html(io.StringIO(body.decode("utf-8")))
    table=next((a for a in tables if {"Announcement Date","Fiscal Quarter End","Actual EPS"}.issubset(a.columns)),None)
    if table is None:raise ValueError("EPS table missing")
    out=table[["Announcement Date","Fiscal Quarter End","Actual EPS"]].copy()
    out.columns=["claimed_announcement_date","quarter_date","as_reported_eps"]
    out["claimed_announcement_date"]=pd.to_datetime(out.claimed_announcement_date,errors="raise")
    out["quarter_date"]=pd.to_datetime(out.quarter_date,errors="raise")
    out["as_reported_eps"]=pd.to_numeric(out.as_reported_eps,errors="raise")
    out=out.sort_values("quarter_date")
    if out.quarter_date.duplicated().any() or len(out)<16:raise ValueError("EPS duplicates or short series")
    if not out.quarter_date.dt.month.isin((3,6,9,12)).all():raise ValueError("Non-quarter EPS date")
    if (out.as_reported_eps<=-500).any():raise ValueError("Invalid EPS")
    return out
def capture(output:Path,now:datetime,*,raw:bytes|None=None)->dict:
    if output.exists() and any(output.iterdir()):raise FileExistsError(output)
    if now.tzinfo is None:raise ValueError("UTC-aware timestamp required")
    now=now.astimezone(timezone.utc)
    if raw is None:
        r=requests.get(URL,headers={"User-Agent":"Mozilla/5.0 Freeburg local live research"},timeout=35)
        r.raise_for_status();raw=r.content
    if len(raw)>2_000_000:raise ValueError("Unexpected HTML size")
    out=parse(raw)
    # Vendor-provided event dates are not independently authenticated:
    # do not treat future rows or subsequent revisions as earlier knowledge.
    out=out[(out.claimed_announcement_date<=pd.Timestamp(now.date())) &
            (out.quarter_date<=pd.Timestamp(now.date()))]
    if out.empty:raise ValueError("No observations publicly announced by capture time")
    output.mkdir(parents=True,exist_ok=True)
    (output/"source.html").write_bytes(raw)
    out.to_csv(output/"eps.csv",index=False)
    report={"schema":"freeburg.live.eps-secondary.v1",
      "provider":"AlphaQuery secondary S&P 500 actual EPS table",
      "source_url":URL,"capture_utc":now.isoformat(),
      "raw_sha256":hashlib.sha256(raw).hexdigest(),
      "last_quarter":str(out.quarter_date.iloc[-1].date()),
      "last_eps":float(out.as_reported_eps.iloc[-1]),"row_count":len(out),
      "source_class":"SECONDARY_UNVERIFIED_ORIGINAL_PUBLICATION_TIMING",
      "historical_date_rule":"Values visible in this HTML no earlier than actual capture timestamp",
      "first_party_s_and_p_verified":False,"ready_to_trade":False}
    (output/"manifest.json").write_text(json.dumps(report,indent=2)+"\n")
    return report
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(capture(a.output_dir,datetime.now(timezone.utc)),indent=2))
