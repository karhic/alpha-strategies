"""Read-only paper API health check, no order intent or credentials required."""
from __future__ import annotations
import argparse,json
from datetime import datetime,timezone
from pathlib import Path
from freeburg.deploy.ibkr_preflight import preflight
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,default=Path("/var/lib/freeburg/paper_connection.json"))
    a=p.parse_args()
    report={"checked_utc":datetime.now(timezone.utc).isoformat(),"connected":False,
            "paper_orders_enabled":False}
    try:
        result=preflight("127.0.0.1",4002,71)
        report.update({"connected":True,"paper_account_count":len(result["accounts_masked"]),
                       "account_masked":result["accounts_masked"]})
    except Exception as exc:
        report["error"]=str(exc)[:300]
    a.output.parent.mkdir(parents=True,exist_ok=True)
    tmp=a.output.with_suffix(".tmp")
    tmp.write_text(json.dumps(report,indent=2)+"\n")
    tmp.replace(a.output)
    print(json.dumps(report,indent=2))
    if not report["connected"]:raise SystemExit(1)
if __name__=="__main__":main()
