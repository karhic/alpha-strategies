"""Source-labelled 90-day quarterly TTM earnings and dividend overlay for OOS replay.

Use with original frozen baseline event stream, retains all other original
source events and timestamps. This reproduces the historic scratchpad 90-day
quarter-end assumption, NOT archival first-publication timing.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import pandas as pd

TARGET={"pushen":("fundamentals.sp500.earnings_yield.1w","as_reported_eps"),
        "competitive":("fundamentals.sp500.dividend_yield.1w","dividends_per_share")}

def make(quarterly, original, output, sleeve):
    if sleeve not in TARGET:raise ValueError(sleeve)
    if output.exists():raise FileExistsError(output)
    ds,column=TARGET[sleeve]
    q=pd.read_csv(quarterly,parse_dates=["quarter_date"]).drop_duplicates("quarter_date",keep="last").set_index("quarter_date").sort_index()
    obs=[]
    for dt in q.index:
        ix=pd.date_range(end=dt,periods=4,freq="QE-DEC")
        if not all(x in q.index for x in ix):continue
        vals=pd.to_numeric(q.loc[ix,column],errors="coerce")
        if vals.notna().all():obs.append((dt+pd.Timedelta(days=90),float(vals.sum())))
    ttm=pd.Series(dict(obs)).sort_index()
    rows=[json.loads(line) for line in original.read_text().splitlines()]
    spx={}
    if sleeve=="pushen":
        for row in rows:
            if row["dataset"]=="index.sp500.level.1w":
                spx[row["event_time"][:10]]=float(row["payload"])
    else:
        # Competitive's frozen stream omits SPX; supply matched independent
        # weekly SPX from Primas (the same source used by model calculation).
        pass
    replacements=0
    # For competitive, read the new value via matching source-price CSV rather
    # than alter unrelated event rows; callers must supply it.
    return rows,ttm,spx,ds,column

def overlay(quarterly,original,output,sleeve,prices):
    rows,ttm,spx,ds,column=make(quarterly,original,output,sleeve)
    if sleeve=="competitive":
        px=pd.read_csv(prices,parse_dates=["date"]).set_index("date")["spx"]
        spx={d.date().isoformat():float(v) for d,v in px.items()}
    if len(ttm)<100:raise ValueError("Short quarterly series")
    idx=pd.DatetimeIndex(sorted(pd.Timestamp(r["event_time"][:10]) for r in rows if r["dataset"]==ds))
    ttm_week=ttm.reindex(ttm.index.union(idx)).sort_index().ffill().reindex(idx)
    vals=dict(zip(idx.strftime("%Y-%m-%d"),ttm_week))
    written=0;missing=0
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open("x") as f:
        for row in rows:
            if row["dataset"]==ds:
                dt=row["event_time"][:10]
                value=vals.get(dt)
                if pd.notna(value) and dt in spx and spx[dt]>0:
                    row["payload"]=float(value/spx[dt]*100)
                    row["source"]="RESEARCH_QUARTER_END_PLUS_90D_ASSUMPTION_NOT_CERTIFIED_PIT"
                    written+=1
                else:missing+=1
            f.write(json.dumps(row,sort_keys=True)+"\n")
    return {"sleeve":sleeve,"overlaid_rows":written,"unchanged_missing_rows":missing,
            "status":"SAME_RESEARCH_90D_ASSUMPTION_NOT_INDEPENDENT_PIT"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--quarterly",required=True,type=Path)
    p.add_argument("--original-events",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    p.add_argument("--sleeve",choices=sorted(TARGET),required=True)
    p.add_argument("--prices",type=Path,help="CSV date,spx required for Competitive")
    a=p.parse_args()
    if a.sleeve=="competitive" and a.prices is None:p.error("--prices required")
    print(json.dumps(overlay(a.quarterly,a.original_events,a.output,a.sleeve,a.prices),indent=2))
if __name__=="__main__":main()
