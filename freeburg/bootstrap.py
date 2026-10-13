"""Single entry point for acquiring Freeburg's currently verifiable inputs.

Examples:
  python -m freeburg.bootstrap --output-dir /tmp/freeburg-snapshot
  python -m freeburg.bootstrap --output-dir /tmp/freeburg-full \
      --enable-yahoo-spx --fred-from-api \
      --govinfo-start 2010-09 --govinfo-end 2026-09

Price vendor and third-party rates require the user's independent review of
terms. Full six-sleeve reproduction is NOT claimed by this acquisition tool.
"""
from __future__ import annotations
import argparse
from datetime import date
import json
import os
from pathlib import Path
from freeburg.tools.acquire_fresh import run as acquire_official
from freeburg.tools.download_spx import download as acquire_spx
from freeburg.tools.download_fred import download as acquire_fred
from freeburg.tools.govinfo_harvest import harvest

def start(snapshot:Path, *, enable_yahoo_spx=False, fred_from_api=False,
          govinfo_start=None, govinfo_end=None, pause_seconds=.25)->dict:
    if snapshot.exists() and any(snapshot.iterdir()):
        raise FileExistsError("Provide an empty directory for a new immutable snapshot")
    if (govinfo_start is None)!=(govinfo_end is None):
        raise ValueError("Supply both GovInfo start and end issue months")
    if fred_from_api and not os.getenv("FRED_API_KEY"):
        raise ValueError("FRED_API_KEY is required for fresh FRED API downloads")
    snapshot.mkdir(parents=True,exist_ok=True)
    report={"snapshot_date":date.today().isoformat(),
            "mode":"ACQUISITION_ONLY_NOT_COMPLETE_SIX_SLEEVE_REPLICATION",
            "components":{},"blockers":[]}
    try:
        report["components"]["official"]=acquire_official(
            snapshot/"official",govinfo_issue=[],include_base=True)
        if enable_yahoo_spx:
            report["components"]["spx"]=acquire_spx(snapshot/"spx")
        else:
            report["blockers"].append("No S&P closes: enable opt-in vendor download or supply local close CSV")
        if fred_from_api:
            report["components"]["fred"]=acquire_fred(
                snapshot/"fred",api_key=os.environ["FRED_API_KEY"])
        else:
            report["blockers"].append("No independent FRED DPRIME/IMF series: supply FRED_API_KEY")
        if govinfo_start and govinfo_end:
            # Don't assume any one large archive request succeeds; chunk into
            # immutable blocks of at most 120 issues.
            start_y,start_m=map(int,govinfo_start.split("-"))
            end_y,end_m=map(int,govinfo_end.split("-"))
            total=(end_y-start_y)*12+end_m-start_m+1
            if total<=0:raise ValueError("GovInfo end precedes start")
            manifest=[]
            for offset in range(0,total,120):
                last=min(total-1,offset+119)
                def ym(i):
                    z=(start_y*12+start_m-1)+i
                    return f"{z//12:04d}-{z%12+1:02d}"
                lo,hi=ym(offset),ym(last)
                block=harvest(lo,hi,snapshot/"govinfo"/f"{lo}_to_{hi}",
                              pause_seconds=pause_seconds)
                manifest.append({
                    "from":lo,"through":hi,"issues":len(block["files"]),
                    "validated":sum(v["status"].startswith("VALID_") for v in block["files"]),
                    "invalid":[v["issue"] for v in block["files"]
                               if not v["status"].startswith("VALID_")]})
            report["components"]["govinfo_batches"]=manifest
        else:
            report["blockers"].append("GovInfo vintage range not requested")
        report["blockers"].extend([
            "Historical FRASER PDF extracts: reuse existing audited archive, new-user full download not finished",
            "Heine historical Dow bond & CRB licensed/index data remain unsourced",
            "FRED and vendor data rights must be checked before redistribution",
            "PIT first-release verification and exact six-sleeve strategy replay not completed"])
    finally:
        (snapshot/"bootstrap_manifest.json").write_text(
            json.dumps(report,indent=2)+"\n",encoding="utf-8")
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-dir",required=True,type=Path)
    p.add_argument("--enable-yahoo-spx",action="store_true",
                   help="You have reviewed Yahoo source terms; fetch locally only")
    p.add_argument("--fred-from-api",action="store_true",
                   help="Use user-owned FRED_API_KEY (never stored)")
    p.add_argument("--govinfo-start",help="YYYY-MM")
    p.add_argument("--govinfo-end",help="YYYY-MM")
    p.add_argument("--pause-seconds",type=float,default=.25)
    args=p.parse_args()
    result=start(args.output_dir,enable_yahoo_spx=args.enable_yahoo_spx,
                 fred_from_api=args.fred_from_api,govinfo_start=args.govinfo_start,
                 govinfo_end=args.govinfo_end,pause_seconds=args.pause_seconds)
    print(json.dumps({"snapshot":str(args.output_dir),
                      "components":list(result["components"]),
                      "blockers":result["blockers"]},indent=2))
if __name__=="__main__":main()
