"""Build isolated replay events using independently reconstructed fundamentals.

Non-fundamental columns still come from frozen local benchmark CSVs and MUST
be replaced by independently sourced columns for a truly fresh-data replay.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import pandas as pd
from freeburg.primas.build_historical_events import _iso

DATASETS={
 "pushen":[("spx","index.sp500.level.1w","SPX"),
           ("earnings_yield","fundamentals.sp500.earnings_yield.1w","SPX"),
           ("cp","rates.commercial_paper.3m.1w","US")],
 "competitive":[("tbond_10y","rates.treasury.10y.1w","US"),
                ("tbill_3m","rates.tbill.3m.1w","US"),
                ("dividend_yield","fundamentals.sp500.dividend_yield.1w","SPX"),
                ("cpi","macro.cpi.1w","US")],
}
def build(sleeve: str, fundamental:Path, frozen:Path, output:Path):
    if output.exists():raise FileExistsError(output)
    fr=pd.read_csv(fundamental,parse_dates=["date"]).set_index("date")
    orig=pd.read_csv(frozen,parse_dates=["date"]).set_index("date")
    if sleeve not in DATASETS:raise ValueError(sleeve)
    target="earnings_yield" if sleeve=="pushen" else "dividend_yield"
    if target not in fr:raise ValueError("Source fundamentals missing")
    if sleeve=="pushen":
        orig["spx"]=fr["spx"].reindex(orig.index)
    orig[target]=fr[target].reindex(orig.index)
    names=[x[0] for x in DATASETS[sleeve]]
    valid=orig[names].notna().all(axis=1)
    events=0; weeks=0
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open("x") as file:
        for dt,row in orig.loc[valid].iterrows():
            for name,ds,inst in DATASETS[sleeve]:
                source="independently_rebuilt_fundamentals" if name==target or (sleeve=="pushen" and name=="spx") else "FROZEN_BASELINE_UNREBUILT"
                file.write(json.dumps({"source":source,"dataset":ds,
                    "instrument":inst,"event_time":_iso(dt,0),
                    "available_at":_iso(dt,20),"payload":float(row[name])},sort_keys=True)+"\n")
                events+=1
            file.write(json.dumps({"source":"weekly_clock","dataset":"clock.weekly.freeburg",
                "instrument":None,"event_time":_iso(dt,0),
                "available_at":_iso(dt,20,1),"payload":None},sort_keys=True)+"\n")
            weeks+=1
    return {"sleeve":sleeve,"weeks":weeks,"events_including_clocks":events+weeks,
            "status":"REBUILT_FUNDAMENTAL__FROZEN_MACRO_BASELINE__NOT_FULL_FRESH_PIT"}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sleeve",choices=sorted(DATASETS),required=True)
    p.add_argument("--fundamentals",type=Path,required=True)
    p.add_argument("--frozen",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    x=p.parse_args()
    print(json.dumps(build(x.sleeve,x.fundamentals,x.frozen,x.output),indent=2))
if __name__=="__main__":main()
