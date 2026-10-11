"""Produce cautiously timestamped GovInfo fundamentals-only DataEvents.

No original pricing/carry data merged; events are a separate overlay. A MODS
recordCreationDate is merely a conservative *catalog-date scenario*.
"""
import argparse,csv,json
from datetime import datetime,time,timezone
from pathlib import Path

DATASETS={"dividend_yield":"fundamentals.sp500.dividend_yield.1w",
          "earnings_yield":"fundamentals.sp500.earnings_yield.1w"}


def emit(input_file:Path,output_file:Path)->dict:
    if output_file.exists():raise FileExistsError(output_file)
    with input_file.open(newline="",encoding="utf-8") as f: rows=list(csv.DictReader(f))
    out=[]
    for row in rows:
        series=row["series"]
        if series not in DATASETS:raise ValueError(series)
        if row["availability_status"]!="ARCHIVE_RECORD_CREATION_PROXY_NOT_FIRST_PUBLIC_RELEASE":
            raise ValueError("Unsupported availability policy")
        availability=datetime.combine(
            datetime.strptime(row["earliest_scenario_date"],"%Y-%m-%d").date(),
            time(23,59),tzinfo=timezone.utc).isoformat()
        obs=datetime.combine(datetime.strptime(row["period_date"],"%Y-%m-%d").date(),
                             time(0),tzinfo=timezone.utc).isoformat()
        if availability<=obs:raise ValueError("Lookahead timestamp")
        out.append({"source":"govinfo_archive_record_date_sensitivity_NOT_PIT_CERTIFIED",
                    "dataset":DATASETS[series],"instrument":"SPX",
                    "event_time":obs,"available_at":availability,
                    "payload":float(row["value"]),
                    "provenance":{"issue":row["issue"],"source_url":row["source_url"],
                                  "source_row":row["source_row"]}})
    out.sort(key=lambda r:(r["available_at"],r["dataset"],r["event_time"]))
    output_file.parent.mkdir(parents=True,exist_ok=True)
    with output_file.open("x",encoding="utf-8") as f:
        for e in out:f.write(json.dumps(e,sort_keys=True)+"\n")
    return {"events":len(out),"output":str(output_file),
            "status":"ARCHIVE_RECORD_DATE_SENSITIVITY_NOT_VERIFIED_FIRST_RELEASE"}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--vintages",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    print(json.dumps(emit(args.vintages,args.output),indent=2))


if __name__=="__main__":main()
