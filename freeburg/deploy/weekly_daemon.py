"""Run one immutable live data capture and log whether IBKR paper API is alive."""
from __future__ import annotations
import argparse,json
from datetime import datetime,timezone
from pathlib import Path
from freeburg.deploy.capture_live import capture as market_capture
from freeburg.deploy.capture_eps import capture as eps_capture
from freeburg.deploy.capture_dividends import acquire as dividends_capture
from freeburg.deploy.assess_capture import assess

def run(root:Path, *, check_broker:bool=True)->dict:
    now=datetime.now(timezone.utc)
    folder=root/now.strftime("%Y%m%dT%H%M%S%fZ")
    folder.mkdir(parents=True,exist_ok=False)
    result={"time":now.isoformat(),"snapshot":str(folder),"broker_connected":False,
            "paper_orders_enabled":False,"stages":{}}
    for name,fn in (("market",lambda:market_capture(folder/"market",now)),
                    ("eps",lambda:eps_capture(folder/"eps",now)),
                    ("dividends",lambda:dividends_capture(folder/"dividends",now=now))):
        try:
            value=fn()
            result["stages"][name]={"ok":True,"status":value.get("readiness",value.get("market_sources_ready"))}
        except Exception as ex:
            result["stages"][name]={"ok":False,"error":type(ex).__name__+": "+str(ex)[:250]}
    if check_broker:
        try:
            from freeburg.deploy.ibkr_preflight import preflight
            result["broker"]=preflight("127.0.0.1",4002,71)
            result["broker_connected"]=result["broker"]["connected"]
        except Exception as ex:
            result["broker_error"]=type(ex).__name__+": "+str(ex)[:200]
    result["signal_ready"]=False
    if all(stage["ok"] for stage in result["stages"].values()):
        try:
            from freeburg.deploy.shadow_signal import calculate as shadow
            result["shadow"]=shadow(folder)
            (folder/"shadow_signal.json").write_text(json.dumps(result["shadow"],indent=2)+"\n")
            result["shadow_signal_ready"]=True
        except Exception as ex:
            result["shadow_signal_ready"]=False
            result["shadow_error"]=type(ex).__name__+": "+str(ex)[:300]

    result["all_data_stages_ok"]=all(s["ok"] for s in result["stages"].values())
    (folder/"run_status.json").write_text(json.dumps(result,indent=2)+"\n")
    latest=root/"latest.json"
    tmp=root/".latest.tmp"
    tmp.write_text(json.dumps(result,indent=2)+"\n")
    tmp.replace(latest)
    print(json.dumps(result,indent=2))
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=Path("/var/lib/freeburg/captures"))
    p.add_argument("--no-broker",action="store_true")
    args=p.parse_args()
    run(args.root,check_broker=not args.no_broker)
if __name__=="__main__":main()
