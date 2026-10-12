"""Portable in-container UTC scheduler; run immediately and weekdays 23:30 UTC."""
from datetime import datetime,timedelta,timezone
from pathlib import Path
import json,time,traceback
from freeburg.deploy.weekly_daemon import run

def next_tick(now):
    target=now.replace(hour=23,minute=30,second=0,microsecond=0)
    if target<=now:target+=timedelta(days=1)
    while target.weekday()>=5:target+=timedelta(days=1)
    return target

def main():
    state=Path("/data/captures")
    state.mkdir(parents=True,exist_ok=True)
    while True:
        try:
            r=run(state,check_broker=False)
            print(json.dumps({"data_ok":r["all_data_stages_ok"],
                              "canonical_agrees":r.get("canonical_shadow_agrees"),
                              "snapshot":r["snapshot"]}),flush=True)
        except Exception as exc:
            print(json.dumps({"error":type(exc).__name__+": "+str(exc)[:300]}),flush=True)
        now=datetime.now(timezone.utc)
        delay=max(30,(next_tick(now)-now).total_seconds())
        print("next UTC capture:",next_tick(now).isoformat(),flush=True)
        time.sleep(delay)
if __name__=="__main__":main()
