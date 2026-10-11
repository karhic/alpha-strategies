"""Conservative vintage availability from official GovInfo package metadata.

A GovInfo recordCreationDate documents *catalog ingestion*, not necessarily
first public availability. Treating it as the earliest eligible date for
research is a deliberately delayed *scenario*, not verified PIT.
"""
from __future__ import annotations
import argparse
import csv
from datetime import date,timedelta
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from urllib.request import Request,urlopen

from freeburg.tools.free_data import _float,govinfo_preview,MONTHS

def metadata(issue: str, *, loader=None) -> dict:
    if not re.fullmatch(r"(?:19|20)\d\d-(?:0[1-9]|1[0-2])",issue):
        raise ValueError("Invalid YYYY-MM issue")
    url=f"https://www.govinfo.gov/metadata/pkg/ECONI-{issue}/mods.xml"
    if loader is None:
        req=Request(url,headers={"User-Agent":"Freeburg-open-research/0.3"})
        with urlopen(req,timeout=30) as resp:data=resp.read(2_000_001)
    else:data=loader(url)
    if len(data)>2_000_000:raise ValueError("Unexpected large MODS file")
    root=ET.fromstring(data)
    values={}
    for el in root.iter():
        tag=el.tag.split("}")[-1]
        if tag in ("dateIssued","recordCreationDate") and el.text:
            values.setdefault(tag,el.text.strip())
    record=values.get("recordCreationDate")
    issued=values.get("dateIssued")
    if not record or not issued:raise ValueError(f"Missing required MODS dates: {issue}")
    if date.fromisoformat(record)<date.fromisoformat(issued):
        raise ValueError(f"Metadata catalog date precedes issue date: {issue}")
    return {"issue":issue,"date_issued":issued,"record_created":record,
            "metadata_url":url,
            "availability_basis":"ARCHIVE_RECORD_CREATION_PROXY_NOT_FIRST_PUBLIC_RELEASE"}


def monthly_from_workbook(xls: Path, info: dict) -> list[dict]:
    rows=govinfo_preview(xls,max_rows=150)
    if not rows or "Common Stock Prices and Yields" not in str(rows[0][0]):
        raise ValueError("Wrong economic table")
    if not any("Earnings/price" in str(cell) for row in rows[:6] for cell in row):
        raise ValueError("Incorrect table columns")
    current_year=None
    output=[]
    for rowno,row in enumerate(rows,1):
        if len(row)<10:continue
        label=str(row[0]).strip()
        full=re.fullmatch(r"((?:19|20)\d{2}):\s*([A-Za-z]{3,9})\.?",label)
        short=re.fullmatch(r"([A-Za-z]{3,9})\.?",label)
        if full:
            current_year=int(full.group(1))
            mon=MONTHS.get(full.group(2)[:3].lower())
        elif short and current_year:
            mon=MONTHS.get(short.group(1)[:3].lower())
        else:continue
        if not mon:continue
        period=date(current_year,mon,1)
        # Reprinted historical rows are observations first seen in THIS issue only
        # until an earlier source issue is independently fetched and validated.
        if period>date.fromisoformat(info["record_created"]):continue
        div=_float(row[8]);earn=_float(row[9])
        for key,value in (("dividend_yield",div),("earnings_yield",earn)):
            if value is None:continue
            if key=="dividend_yield" and not (0<value<25):continue
            if key=="earnings_yield" and not (-30<value<50):continue
            output.append({
                "series":key,"period_date":period.isoformat(),
                "value":value,"issue":info["issue"],
                "issue_date":info["date_issued"],
                "archive_record_created":info["record_created"],
                # Never treat the issued month as availability.
                "earliest_scenario_date":info["record_created"],
                "source_row":rowno,"source_url":info["metadata_url"].replace(
                    "/metadata/pkg/","/content/pkg/").replace("/mods.xml",
                        f"/xls/ECONI-{info['issue']}-Pg31.xls"),
                "availability_status":info["availability_basis"]})
    return output


def run(xls_dir: Path, output: Path, *, use_online_metadata=True, cache_dir:Path|None=None):
    if output.exists():raise FileExistsError(output)
    files=sorted(xls_dir.glob("ECONI-????-??-Pg31.xls"))
    if not files:raise ValueError("No GovInfo XLS files")
    extracted=[];errors=[]
    for path in files:
        issue=path.name[len("ECONI-"):len("ECONI-")+7]
        try:
            xml_path=(cache_dir/("ECONI-"+issue+".mods.xml")) if cache_dir else None
            if xml_path and xml_path.exists():
                info=metadata(issue,loader=lambda url:xml_path.read_bytes())
            elif use_online_metadata:
                raw={}
                def load(url):
                    req=Request(url,headers={"User-Agent":"Freeburg-open-research/0.3"})
                    with urlopen(req,timeout=30) as r:return r.read(2_000_001)
                data=load(f"https://www.govinfo.gov/metadata/pkg/ECONI-{issue}/mods.xml")
                info=metadata(issue,loader=lambda url:data)
                if xml_path:
                    xml_path.parent.mkdir(parents=True,exist_ok=True)
                    xml_path.write_bytes(data)
            else:
                raise FileNotFoundError(f"Missing metadata cache for {issue}")
            extracted.extend(monthly_from_workbook(path,info))
        except Exception as exc:errors.append({"issue":issue,"error":str(exc)[:200]})
    if not extracted:raise ValueError(f"No rows extracted: {errors}")
    # Keep only first observed vintage for each period + indicator. The
    # archive creation time, not the nominal issue date, controls ordering.
    extracted.sort(key=lambda r:(r["series"],r["period_date"],
                                 r["earliest_scenario_date"],r["issue"]))
    first={}
    for row in extracted:first.setdefault((row["series"],row["period_date"]),row)
    chosen=sorted(first.values(),key=lambda r:(r["earliest_scenario_date"],
                                                r["series"],r["period_date"]))
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open("x",newline="",encoding="utf-8") as fh:
        writer=csv.DictWriter(fh,fieldnames=list(chosen[0]))
        writer.writeheader();writer.writerows(chosen)
    return {"input_files":len(files),"vintage_observations":len(extracted),
            "unique_first_observations":len(chosen),
            "by_series":{s:sum(x["series"]==s for x in chosen)
                         for s in ("dividend_yield","earnings_yield")},
            "errors":errors,"output":str(output),
            "status":"METADATA_DELAYED_SENSITIVITY_ONLY_NOT_CERTIFIED_PIT"}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--xls-dir",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--metadata-cache-dir",type=Path)
    p.add_argument("--offline",action="store_true")
    a=p.parse_args()
    print(json.dumps(run(a.xls_dir,a.output,
                         use_online_metadata=not a.offline,cache_dir=a.metadata_cache_dir),indent=2))

if __name__=="__main__":main()
