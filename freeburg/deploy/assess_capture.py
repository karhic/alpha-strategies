"""Promote immutable captured source files to a safe live-ingestion status report.

Never infer first-publication timestamps from observation dates. Only the first
capture instant proves a value was in this snapshot. Do not emit all-four
signals when fundamental sources are missing.
"""
from __future__ import annotations
import argparse,hashlib,json
from datetime import datetime,timezone
from pathlib import Path
from freeburg.deploy.capture_live import h15_weekly,_fred_csv,_spx_close
def assess(snapshot:Path)->dict:
    m=json.loads((snapshot/"manifest.json").read_text())
    if m["schema"]!="freeburg.live.market-capture.v1":raise ValueError("Wrong snapshot schema")
    captured=datetime.fromisoformat(m["captured_at_utc"])
    if captured.tzinfo is None or captured>datetime.now(timezone.utc):raise ValueError("Invalid capture time")
    for name,record in m["sources"].items():
        blob=(snapshot/name).read_bytes()
        if hashlib.sha256(blob).hexdigest()!=record["sha256"]:
            raise ValueError("Source tampering detected: "+name)
    if not m["market_sources_ready"]:raise ValueError("Source freshness check failed")
    if m.get("fundamental_eps_dividends_ready") or m.get("signal_ready"):
        raise ValueError("Unexpected signal-ready assertion without independently verified input")
    return {
        "schema":"freeburg.four.ingestion-status.v1",
        "market_capture_verified":True,
        "capture_time":m["captured_at_utc"],
        "target_friday":m["target_completed_friday"],
        "series_latest":m["series"],
        "replay_safe":"CAPTURED_FROM_THIS_INSTANT_ONLY",
        "ready_for_full_signals":False,
        "missing":["S&P 500 quarterly EPS source with original publication timestamp",
                   "S&P 500 dividends source with original publication timestamp",
                   "online weekly strategy replay with causal as-of event ingestion"],
        "ibkr_orders_authorized":False,
        "x_posting_authorized":False,
    }
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--snapshot",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    r=assess(a.snapshot)
    if a.output.exists():raise FileExistsError(a.output)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,indent=2)+"\n")
    print(json.dumps(r,indent=2))
if __name__=="__main__":main()
