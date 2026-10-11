"""Flag GovInfo weekly price anomalies against *user-owned local* reference closes.

This is auditing only: source rows are never corrected. A weekly average is not
a Friday close. Thresholds are diagnostic, not a license to drop inconvenient data.
"""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
from statistics import median
from freeburg.tools.free_data import load_prices


def audit(source_csv: Path, reference_csv: Path, threshold_bps: float=500.) -> dict:
    if threshold_bps<=0:raise ValueError("Positive threshold required")
    reference=load_prices(reference_csv)
    seen={}
    with source_csv.open(newline="",encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            day=r["friday"]
            price=float(r["weekly_spx_average"])
            seen.setdefault(day,[]).append((r["issue"],price))
    diffs=[]; conflicting=[]
    for day,obs in sorted(seen.items()):
        unique={round(x[1],6) for x in obs}
        if len(unique)>1:conflicting.append({"date":day,"issue_prices":obs})
        from datetime import date
        reference_value=reference.get(date.fromisoformat(day))
        if reference_value is None:continue
        value=median(v for _,v in obs)
        error_bps=(value/reference_value-1)*10000
        diffs.append((day,value,reference_value,error_bps))
    if not diffs:raise ValueError("No reference overlap")
    flagged=[{"date":d,"weekly_average":round(v,5),"reference_close":round(ref,5),
              "absolute_bps":round(abs(delta),3),"issues":[x[0] for x in seen[d]]}
             for d,v,ref,delta in diffs if abs(delta)>threshold_bps]
    return {
        "overlap_weeks":len(diffs),
        "median_abs_bps":round(median(abs(x[3]) for x in diffs),4),
        "max_abs_bps":round(max(abs(x[3]) for x in diffs),4),
        "threshold_bps":threshold_bps,
        "flagged_weeks":sorted(flagged,key=lambda x:-x["absolute_bps"]),
        "cross_issue_conflicts":conflicting[:30],
        "status":"INDEPENDENT_AUDIT_NOT_A_CORRECTION_OR_SIGNAL_EQUIVALENCE",
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--govinfo-weekly",type=Path,required=True)
    p.add_argument("--reference-prices",type=Path,required=True)
    p.add_argument("--threshold-bps",type=float,default=500.)
    args=p.parse_args()
    print(json.dumps(audit(args.govinfo_weekly,args.reference_prices,args.threshold_bps),indent=2))

if __name__=="__main__":main()
