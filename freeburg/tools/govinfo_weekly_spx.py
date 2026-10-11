"""Extract the weekly S&P *average*, not Friday close, from GovInfo E.CON.I XLS.

This is an independent proxy, NEVER a drop-in for Friday SPX close. It does not
claim exact as-published point-in-time availability or redistribution rights.
"""
from __future__ import annotations
import argparse
import csv
from datetime import date, timedelta
import json
from pathlib import Path
import re

from freeburg.tools.free_data import _float, govinfo_preview

MONTHS = {s.lower():i for i,s in enumerate(
    ("Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"),1)}


def parse_weekly_table(rows: list[list[str]], issue: str, source: str, anomalies: list[dict] | None = None) -> list[dict]:
    if not rows or "Common Stock Prices and Yields" not in str(rows[0][0]):
        raise ValueError("Wrong economic table")
    if len(rows)<4 or not any("Standard" in str(r[6]) for r in rows[:5] if len(r)>6):
        raise ValueError("Unexpected S&P column layout: inspect manually")
    in_weekly=False
    yr=None; mo=None
    found=[]
    for line_no,row in enumerate(rows,1):
        if len(row)<10:continue
        label=str(row[0]).strip()
        if label.lower().startswith("week ended"):
            in_weekly=True
            continue
        if not in_weekly:continue
        if any(x in label for x in ("Source:", "Sources:", "Effective January", "Note:", "Monthly data")):
            break
        m=re.fullmatch(r"((?:19|20)\d{2}):\s*([A-Za-z]{3,9})\s+(\d{1,2})(?:\s+[a-z])?\.?\s*",label)
        named=re.fullmatch(r"([A-Za-z]{3,9})\s+(\d{1,2})(?:\s+[a-z])?\.?\s*",label)
        bare=re.fullmatch(r"(\d{1,2})\.?\s*",label)
        if m:
            yr=int(m.group(1));mo=MONTHS.get(m.group(2)[:3].lower());day=int(m.group(3))
        elif named and yr is not None:
            newmo=MONTHS.get(named.group(1)[:3].lower())
            if mo==12 and newmo==1:yr+=1
            mo=newmo;day=int(named.group(2))
        elif bare and yr is not None and mo is not None:
            day=int(bare.group(1))
        else:
            continue
        if yr is None or mo is None:continue
        try:
            period=date(yr,mo,day)
        except ValueError:continue
        # Published issue sometimes erroneously labels January with prior year.
        if issue[:4] != str(yr) and mo == 1 and period.year == int(issue[:4])-1:
            period=date(int(issue[:4]),mo,day)
        # Some tables omit the month change on a trailing bare day.
        if period.weekday()!=5 and bare and mo is not None:
            next_month=mo+1 if mo<12 else 1
            next_year=yr if mo<12 else yr+1
            try:
                possible=date(next_year,next_month,day)
                if possible.weekday()==5: period=possible;yr=next_year;mo=next_month
            except ValueError: pass
        if period.weekday()!=5: # Source normally labels Saturday-ending weeks.
            if anomalies is not None:
                anomalies.append({"issue":issue,"source_row":line_no,
                                  "raw_label":label,
                                  "reason":f"unexpected weekday for {period}"})
                continue
            raise ValueError(f"Unexpected weekly label {period} in {issue}")
        price=_float(row[6]); div=_float(row[8])
        if price is None or price<10:
            continue
        found.append({
            "issue":issue,"week_ended_label":period.isoformat(),
            "friday":(period-timedelta(days=1)).isoformat(),
            "weekly_spx_average":round(price,6),
            "dividend_yield_percent":div if div is not None else "",
            "source_url":source,"source_row":line_no,
            "status":"WEEKLY_AVERAGE_NOT_FRIDAY_CLOSE__NO_PIT_CLAIM",
        })
    if not found:
        raise ValueError("No valid weekly prices in GovInfo table")
    return found


def extract_directory(path: Path, out: Path) -> dict:
    records=[]
    successes=0
    for file in sorted(path.glob("ECONI-????-??-Pg31.xls")):
        issue=file.name[6:13]
        source=f"https://www.govinfo.gov/content/pkg/ECONI-{issue}/xls/ECONI-{issue}-Pg31.xls"
        rows=govinfo_preview(file,max_rows=1000)
        try:
            parsed=parse_weekly_table(rows,issue,source)
        except ValueError as exc:
            raise ValueError(f"{file}: {exc}") from exc
        records.extend(parsed)
        successes+=1
    if not records:raise ValueError(f"No XLS tables in {path}")
    out.parent.mkdir(parents=True,exist_ok=True)
    if out.exists():raise FileExistsError(out)
    fields=list(records[0])
    with out.open("x",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=fields);w.writeheader();w.writerows(records)
    return {"files":successes,"rows":len(records),"unique_fridays":len(set(r["friday"] for r in records)),
            "first":min(r["friday"] for r in records),
            "last":max(r["friday"] for r in records),"output":str(out),
            "status":"RESEARCH_PROXY_NO_TRADING_TIMESTAMP"}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-dir",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(extract_directory(a.source_dir,a.output),indent=2))


if __name__=="__main__":main()
