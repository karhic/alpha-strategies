"""Portable scheduler: capture now, then on US weekdays 23:30 UTC.

Retries failed provider downloads after 45 minutes rather than losing a week.
No brokerage accounts or credentials are used.
"""
from datetime import datetime,timedelta,timezone
from pathlib import Path
import json,time
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
        success=False
        try:
            r=run(state,check_broker=False)
            success=r["all_data_stages_ok"] and r.get("canonical_shadow_agrees") is True
            print(json.dumps({"ok":success,"snapshot":r["snapshot"],
                              "target":r.get("canonical",{}).get("spy_target_weight")}),flush=True)
        except Exception as exc:
            print(json.dumps({"error":type(exc).__name__+": "+str(exc)[:300]}),flush=True)
        now=datetime.now(timezone.utc)
        delay=max(30,(next_tick(now)-now).total_seconds()) if success else 2700
        print("Next capture:",(now+timedelta(seconds=delay)).isoformat(),flush=True)
        time.sleep(delay)
if __name__=="__main__":main()
