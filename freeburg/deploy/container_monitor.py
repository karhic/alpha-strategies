"""Non-trading container monitor: inspect latest signal, verify broker paper connection."""
import json,time
from pathlib import Path
from datetime import datetime,timezone
from freeburg.deploy.ibkr_preflight import preflight

def check():
    data={"checked_at":datetime.now(timezone.utc).isoformat(),
          "paper_order_permission":False,"x_post_permission":False}
    try:
        j=json.loads(Path("/data/captures/latest.json").read_text())
        data.update({"capture_time":j["time"],
                     "sources_ok":j.get("all_data_stages_ok",False),
                     "canonical_shadow_agrees":j.get("canonical_shadow_agrees",False),
                     "target_weight":j.get("canonical",{}).get("spy_target_weight")})
    except Exception as exc:
        data["data_error"]=type(exc).__name__+": "+str(exc)[:100]
    try:
        info=preflight("127.0.0.1",4002,96)
        data["paper_api_connected"]=info["connected"]
        data["paper_account_count"]=len(info["accounts_masked"])
    except Exception as exc:
        data["paper_api_connected"]=False
        data["broker_error"]=type(exc).__name__+": "+str(exc)[:100]
    print(json.dumps(data),flush=True)
if __name__=="__main__":
    while True:
        check()
        time.sleep(1800)
