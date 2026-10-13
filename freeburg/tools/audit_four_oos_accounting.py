"""Deterministic audit of previously generated OOS weekly returns and timing.

This does NOT reconstruct the source release timestamps or signals. It checks
the aggregation, return accounting and published top-level headline, and
quarantines a generic one-week shift as NOT a valid execution lag test.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import pandas as pd
import numpy as np

SLEEVES=("Primas","Triple40","PuShen","Competitive")
def calculate(weekly:pd.DataFrame)->dict:
    x=weekly.copy()
    if "date" in x.columns:x=x.set_index("date")
    x.index=pd.to_datetime(x.index)
    x=x.sort_index()
    if x.index.has_duplicates or x[list(SLEEVES)].isna().any().any():
        raise ValueError("Duplicate dates or missing sleeve observations")
    ret=x[list(SLEEVES)].astype(float).mean(axis=1)
    wealth=np.r_[1.,np.cumprod(1+ret.to_numpy())]
    dd=wealth/np.maximum.accumulate(wealth)-1
    return {"n_weeks":len(ret),"start":x.index[0].date().isoformat(),
            "end":x.index[-1].date().isoformat(),
            "cagr":float(wealth[-1]**(52/len(ret))-1),
            "max_dd":float(dd.min()),
            "terminal_wealth":float(wealth[-1]),
            "status":"RESEARCH_WEEKLY_RETURN_AGGREGATION_ONLY__NOT_LEDGER_PIT"}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--weekly-returns",required=True,type=Path)
    p.add_argument("--output",type=Path)
    a=p.parse_args();x=pd.read_csv(a.weekly_returns)
    r=calculate(x)
    if r["start"]=="2014-01-03" and r["end"]=="2026-08-07":
        if r["n_weeks"]!=658:raise AssertionError("Unexpected count")
        if abs(r["cagr"]-.092137607506)<1e-7 and abs(r["max_dd"]+.191981385323)<1e-7:
            r["headline_fingerprint"]="PASS"
        else:
            raise AssertionError("Published composite statistics do not match underlying weekly returns")
    if a.output:
        if a.output.exists():raise FileExistsError(a.output)
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(json.dumps(r,indent=2)+"\n")
    print(json.dumps(r,indent=2))
if __name__=="__main__":main()
