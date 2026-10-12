"""Portable one-shot capture and four-sleeve signal run.

No account needed. Failures remain inspectable in a dated run directory.
"""
from __future__ import annotations
import argparse,json
from datetime import datetime,timezone
from pathlib import Path
from freeburg.deploy.weekly_daemon import run

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--state",type=Path,default=Path("/data"))
    opt=p.parse_args()
    root=opt.state/"captures"
    root.mkdir(parents=True,exist_ok=True)
    report=run(root,check_broker=False)
    signal=report.get("canonical")
    print(json.dumps({"snapshot":report["snapshot"],"data_ok":report["all_data_stages_ok"],
                      "strategy_parity":report.get("canonical_shadow_agrees"),
                      "signal":signal,"broker_required":False,
                      "x_required":False,"orders_enabled":False},indent=2))
    if not report["all_data_stages_ok"] or report.get("canonical_shadow_agrees") is not True:
        raise SystemExit(2)
if __name__=="__main__":main()
