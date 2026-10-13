"""Conservative next-week-execution sensitivity of Freeburg four OOS returns.

Infers historical binary exposures by matching weekly sleeve returns against
their common equity return, then delays the exposure by one observation.
Reprices defensive weeks using the recorded cash accrual (extracted from each
sleeve's OOS return when originally defensive) or a documented CP-based proxy.
This is a sensitivity, NOT an audit of exact historical execution fills.
"""
from __future__ import annotations
import argparse, json, math
from pathlib import Path
import numpy as np
import pandas as pd
from freeburg.primas.build_historical_events import _cp_weekly


SLEEVES=("Primas","Triple40","PuShen","Competitive")
def performance(r):
    y=r.to_numpy(float)
    wealth=np.r_[1.,np.cumprod(1+y)]
    return {"cagr":float(wealth[-1]**(52/len(y))-1),
            "max_drawdown":float((wealth/np.maximum.accumulate(wealth)-1).min()),
            "raw_sharpe":float(y.mean()/y.std(ddof=1)*math.sqrt(52)),
            "weeks":len(y)}
def build(source:Path,output:Path):
    x=pd.read_csv(source,parse_dates=["date"]).set_index("date")
    cols=list(SLEEVES)
    if x[cols+["stock","rf"]].isna().any().any():raise ValueError("Missing inputs")
    # Actual CP weekly yield, not refitted using the OOS equity curve.
    cp=_cp_weekly(x.index).reindex(x.index).ffill().clip(lower=0)/5200
    defensive={"Primas":cp,"Triple40":.9*cp,"PuShen":cp,"Competitive":.9*cp}
    baseline=x[cols].mean(axis=1)
    shifted=pd.DataFrame(index=x.index)
    counts={}
    for name in cols:
        now=x[name]
        # Equity return is the exact strategy model's shared equity leg. As
        # diagnostic use discrepancy from defensive return when ambiguous.
        distance=(now-x["stock"]).abs()
        cash_distance=(now-defensive[name]).abs()
        original_on=distance<cash_distance
        near=(distance-cash_distance).abs()<0.00001
        counts[name]={"inferred_equity_weeks":int(original_on.sum()),
                      "near_ties_within_1bp":int(near.sum())}
        # Shift signals by one week; first week's state is unknown, exclude it.
        delayed=original_on.shift(1)
        shifted[name]=pd.Series(np.where(delayed==True,x["stock"],defensive[name]),index=x.index)
    shifted=shifted.iloc[1:]
    baseline=baseline.iloc[1:]
    late=shifted.mean(axis=1)
    result={"source":str(source),"evaluation_start":str(shifted.index.min().date()),
            "evaluation_end":str(shifted.index.max().date()),
            "classification":counts,"baseline":performance(baseline),
            "one_week_late":performance(late),
            "limitations":[
                "Signal states inferred from modeled weekly returns rather than direct causal ledger.",
                "Cash repricing uses public weekly CP yield with 90% carry for Triple40/Competitive.",
                "This is one whole week slower, not a true next-session execution simulation.",
                "Near ties and cash-proxy source differences may slightly alter signal classification.",
                "All inputs are from the same original simulated OOS research, not independently PIT-certified."
            ]}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2)+"\n")
    return result
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--weekly-returns",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    print(json.dumps(build(a.weekly_returns,a.output),indent=2))
if __name__=="__main__":main()
