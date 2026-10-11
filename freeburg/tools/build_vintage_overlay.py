"""Safe overlay of independently timestamped GovInfo fundamentals onto weekly events.

Remove frozen benchmark fundamental events entirely, then add each GovInfo
revision at its *availability time*, not its historical observation date.
No automatic claim of complete point-in-time reproduction is made.
"""
from __future__ import annotations
import argparse,json
from datetime import datetime,timedelta,timezone
from pathlib import Path
from collections import Counter

DATASETS={"pushen":"fundamentals.sp500.earnings_yield.1w",
          "competitive":"fundamentals.sp500.dividend_yield.1w"}
def build(base:Path,overlay:Path,out:Path,sleeve:str)->dict:
    if sleeve not in DATASETS:raise ValueError(sleeve)
    if out.exists():raise FileExistsError(out)
    target=DATASETS[sleeve]
    base_events=[json.loads(s) for s in base.read_text().splitlines() if s.strip()]
    overlays=[json.loads(s) for s in overlay.read_text().splitlines() if s.strip()]
    if not base_events:raise ValueError("Missing weekly baseline events")
    if not overlays:raise ValueError("Missing availability-capped overlays")
    for ev in overlays:
        if ev["dataset"] not in DATASETS.values():raise ValueError("Unexpected overlay dataset")
        if datetime.fromisoformat(ev["available_at"])<=datetime.fromisoformat(ev["event_time"]):
            raise ValueError("Overlay contains lookahead")
    # Replace the target fundamental only; preserve unrelated benchmark inputs.
    base_remaining=[e for e in base_events if e["dataset"]!=target]
    removed=len(base_events)-len(base_remaining)
    if removed==0:raise ValueError(f"Baseline did not contain {target}")
    filtered=[e for e in overlays if e["dataset"]==target]
    if not filtered:raise ValueError(f"No {target} overlays")
    # The event timestamp must be AFTER it becomes known: the source period is
    # provenance, not a time to insert an as-yet unknown value into the store.
    promoted=[]
    for ev in filtered:
        a=datetime.fromisoformat(ev["available_at"])
        next_minute=a+timedelta(minutes=1)
        promoted.append({
            **ev,"event_time":a.isoformat(),
            "available_at":a.isoformat(),
            "source_period_time":ev["event_time"],
            "source":"govinfo_catalog_date_overlay_NOT_CERTIFIED_PIT",
        })
    # A weekly decision clock must not precede a late-input event.
    events=sorted(base_remaining+promoted,
                  key=lambda e:(e["available_at"],e["dataset"],e["event_time"]))
    # Guard actual target events never arriving before their catalog timestamp.
    for e in promoted:
        if e["event_time"]!=e["available_at"]:raise ValueError("Bad promotion")
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open("x") as fh:
        for e in events:fh.write(json.dumps(e,sort_keys=True)+"\n")
    clock=sum(e["dataset"]=="clock.weekly.freeburg" for e in base_remaining)
    return {"sleeve":sleeve,"removed_frozen_fundamentals":removed,
            "overlay_events":len(promoted),"weekly_decisions":clock,
            "total_events":len(events),
            "result":"PARTIAL_CATALOG_DATE_SENSITIVITY_NOT_FULL_PIT"}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base-events",required=True,type=Path)
    p.add_argument("--fundamental-events",required=True,type=Path)
    p.add_argument("--sleeve",choices=sorted(DATASETS),required=True)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    print(json.dumps(build(a.base_events,a.fundamental_events,a.output,a.sleeve),indent=2))
if __name__=="__main__":main()
