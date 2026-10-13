"""Overlay source-observed FRED monthly Moody's Baa on original Triple-40 events.

Monthly FRED observations are dated the first day of their observation month,
NOT necessarily released on that date. Month-start reproduces old research
but is inherently hindsight-contaminated. Month-end/next-month mark
conservative publication assumptions, not validated release timestamps.
"""
import argparse,json
from pathlib import Path
import pandas as pd

def overlay(original,monthly,output,availability):
    if output.exists():raise FileExistsError(output)
    m=pd.read_csv(monthly,parse_dates=["observation_date"]).set_index("observation_date")["BAA"].dropna()
    if availability=="month-end":m.index=m.index+pd.offsets.MonthEnd(0)
    elif availability=="next-month":m.index=m.index+pd.offsets.MonthBegin(1)
    elif availability!="month-start":raise ValueError(availability)
    rows=[json.loads(x) for x in original.read_text().splitlines()]
    dates=pd.DatetimeIndex(sorted({pd.Timestamp(r["event_time"][:10]) for r in rows
                  if r["dataset"]=="rates.moody_baa.1w"}))
    series=m.reindex(m.index.union(dates)).sort_index().ffill().reindex(dates)
    lookup=series.to_dict()
    n=0
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open("x") as f:
        for row in rows:
            if row["dataset"]=="rates.moody_baa.1w":
                dt=pd.Timestamp(row["event_time"][:10])
                if dt>=pd.Timestamp("2010-01-01") and dt in lookup and pd.notna(lookup[dt]):
                    row["payload"]=float(lookup[dt])
                    row["source"]="FRED_BAA_MONTHLY_"+availability.upper().replace("-","_")+"_RESEARCH_TIMING_NOT_CERTIFIED_PIT"
                    n+=1
            f.write(json.dumps(row,sort_keys=True)+"\n")
    return {"modified_baa_rows":n,"month_start_lookahead":availability=="month-start"}
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--original-events",type=Path,required=True)
    p.add_argument("--monthly",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--availability",choices=["month-start","month-end","next-month"],required=True)
    a=p.parse_args()
    print(overlay(a.original_events,a.monthly,a.output,a.availability))
