"""Compare actual four-sleeve causal-engine actions with published OOS return branches.

This is a cross-implementation check using already frozen original inputs;
it is not independent vintage/PIT source certification.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
SLEEVES={"primas":("Primas",1.),"triple40":("Triple40",.9),"pushen":("PuShen",1.),"competitive":("Competitive",.9)}

def audit(returns,cp,ledgers):
    x=pd.read_csv(returns,parse_dates=["date"]).set_index("date").sort_index()
    q=pd.read_csv(cp,parse_dates=["date"]).set_index("date")["cp"].reindex(x.index)
    if q.isna().any():raise ValueError("Missing commercial paper observations")
    report={}
    for slug,(col,factor) in SLEEVES.items():
        actions={}
        with (ledgers/(slug+".jsonl")).open() as f:
            for line in f:
                obj=json.loads(line)
                if obj["kind"]=="strategy_action":
                    day=pd.Timestamp(obj["timestamp"]).tz_localize(None).normalize()
                    actions[day]=int(float(obj["payload"]["weight"])>.5)
        expected=x["stock"]
        cash=q.clip(lower=0)*factor/5200
        err_on=(x[col]-expected).abs()
        err_off=(x[col]-cash).abs()
        ambiguous=(err_on-err_off).abs()<1e-9
        published=(err_on<err_off).astype(int)
        replay=pd.Series(actions).reindex(x.index)
        matches=(replay==published)&~ambiguous
        mismatch=(replay!=published)&~ambiguous&replay.notna()
        report[slug]={
            "weeks":len(x),"with_action":int(replay.notna().sum()),
            "branch_ambiguous":int(ambiguous.sum()),
            "unambiguous_compared":int((replay.notna()&~ambiguous).sum()),
            "matches":int(matches.sum()),
            "mismatches":int(mismatch.sum()),
            "missing_actions":int(replay.isna().sum()),
            "first_mismatches":[d.date().isoformat() for d in x.index[mismatch][:8]],
            "source_status":"FROZEN_OR_EXISTING_SOURCE_EVENT_REPLAY_NOT_PROVEN_PIT"}
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--weekly-returns",type=Path,required=True)
    p.add_argument("--cp-weekly",type=Path,required=True)
    p.add_argument("--ledgers",type=Path,required=True)
    p.add_argument("--output",type=Path)
    a=p.parse_args();report=audit(a.weekly_returns,a.cp_weekly,a.ledgers)
    print(json.dumps(report,indent=2))
    if a.output:
        if a.output.exists():raise FileExistsError(a.output)
        a.output.write_text(json.dumps(report,indent=2)+"\n")
if __name__=="__main__":main()
