"""Download a bounded, explicit range of GovInfo Economic Indicators spreadsheets.

This is a research acquisition step, NOT a point-in-time feed. Each issue is
an independent source vintage. Raw XLS files remain local to the user.
"""
from __future__ import annotations
import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import time

from freeburg.tools.acquire_fresh import acquire
from freeburg.tools.free_data import govinfo_urls
from freeburg.tools.govinfo_weekly_spx import parse_weekly_table
from freeburg.tools.free_data import govinfo_preview

def months(start: str, end: str) -> list[str]:
    s=date.fromisoformat(start+"-01")
    e=date.fromisoformat(end+"-01")
    if s>e:raise ValueError("start after end")
    out=[]
    y,m=s.year,s.month
    while (y,m)<=(e.year,e.month):
        out.append(f"{y:04d}-{m:02d}")
        m+=1
        if m==13:y,m=y+1,1
    if len(out)>120:raise ValueError("Range exceeds 120 issues; use bounded chunks")
    return out

def harvest(start: str, end: str, dest: Path, *, pause_seconds: float=0.25,
            downloader=acquire) -> dict:
    if pause_seconds<0:raise ValueError("pause must be nonnegative")
    issues=months(start,end)
    if dest.exists() and any(dest.iterdir()):
        raise FileExistsError("Require a new empty directory for each immutable harvest")
    dest.mkdir(parents=True,exist_ok=True)
    manifest={"requested_issues":issues,"status":"RESEARCH_SOURCE_VINTAGES_NO_PIT_CLAIM",
              "files":[]}
    try:
        for ix,issue in enumerate(issues):
            source=govinfo_urls(issue,"31")["xls"]
            path=dest/f"ECONI-{issue}-Pg31.xls"
            try:
                record=downloader(source,path,"xls",timeout=45)
                rows=govinfo_preview(path,max_rows=100)
                parsed=parse_weekly_table(rows,issue,source)
                record.update({"issue":issue,"status":"VALID_S_AND_P_WEEKLY_AVERAGE",
                               "weekly_rows":len(parsed),
                               "first_friday":min(x["friday"] for x in parsed),
                               "last_friday":max(x["friday"] for x in parsed)})
            except Exception as exc:
                if path.exists():path.unlink()
                record={"issue":issue,"url":source,
                        "status":"MISSING_OR_INVALID_XLS","error":str(exc)[:250]}
            manifest["files"].append(record)
            if ix<len(issues)-1:time.sleep(pause_seconds)
    finally:
        (dest/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    return manifest

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--start",required=True,help="YYYY-MM")
    p.add_argument("--end",required=True,help="YYYY-MM")
    p.add_argument("--output-dir",type=Path,required=True)
    p.add_argument("--pause-seconds",type=float,default=.25)
    args=p.parse_args()
    z=harvest(args.start,args.end,args.output_dir,pause_seconds=args.pause_seconds)
    ok=[x for x in z["files"] if x["status"]=="VALID_S_AND_P_WEEKLY_AVERAGE"]
    print(json.dumps({"total":len(z["files"]),"valid":len(ok),
      "invalid":[x["issue"] for x in z["files"] if x not in ok],
      "output_dir":str(args.output_dir),"status":z["status"]},indent=2))

if __name__=="__main__": main()
