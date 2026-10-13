from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
from freeburg.primas.build_historical_events import _iso
HERE=Path(__file__).resolve().parent
SRC=HERE/"data/pit_weekly_inputs.csv"
OUT=HERE/"data/competitive_benchmark_events.jsonl"
def main():
 x=pd.read_csv(SRC,parse_dates=["date"]).dropna()
 with OUT.open("w") as fh:
  for _,r in x.iterrows():
   d=pd.Timestamp(r.date)
   rows=[("rates.treasury.10y.1w","US",r.tbond_10y),("rates.tbill.3m.1w","US",r.tbill_3m),("fundamentals.sp500.dividend_yield.1w","SPX",r.dividend_yield),("macro.cpi.1w","US",r.cpi)]
   for ds,inst,v in rows: fh.write(json.dumps({"source":"frozen_pit_inputs","dataset":ds,"instrument":inst,"event_time":_iso(d,0),"available_at":_iso(d,20),"payload":float(v)},sort_keys=True)+"\n")
   fh.write(json.dumps({"source":"benchmark_calendar","dataset":"clock.weekly.freeburg","instrument":None,"event_time":_iso(d,0),"available_at":_iso(d,20,1),"payload":None},sort_keys=True)+"\n")
 print(OUT)
if __name__=="__main__": main()
