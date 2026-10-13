"""Convert audited four-sleeve decision ledgers into a non-executing snapshot."""
from __future__ import annotations
from datetime import datetime,timedelta,timezone
import hashlib,json
from pathlib import Path
SLEEVES=("primas","triple40","pushen","competitive")

def build(ledger_dir:Path,asof:datetime,max_age_days:int=8)->dict:
    if asof.tzinfo is None:raise ValueError("Timezone required")
    now=asof.astimezone(timezone.utc)
    signals={};digests={};dates={}
    for name in SLEEVES:
        data=(ledger_dir/(name+".jsonl")).read_bytes()
        digests[name]=hashlib.sha256(data).hexdigest()
        rows=[]
        for line in data.splitlines():
            r=json.loads(line)
            if r.get("kind")!="strategy_action":continue
            p=r["payload"]
            if p.get("tag")!=name or p.get("instrument")!="SPY":continue
            at=datetime.fromisoformat(r["timestamp"].replace("Z","+00:00"))
            if at.tzinfo is None:raise ValueError("Naive event timestamp")
            if at>now:continue
            weight=float(p["weight"])
            if weight not in (0.,1.):raise ValueError("Expected binary signal")
            rows.append((at,int(weight)))
        if not rows:raise ValueError("Missing "+name+" action")
        stamp,state=max(rows)
        if now-stamp>timedelta(days=max_age_days):raise ValueError("Stale "+name+" action")
        signals[name]=state;dates[name]=stamp; 
    if len(set(dates.values()))!=1:raise ValueError("Sleeve decision timestamps differ")
    return {
        "schema":"freeburg.four.weekly-signal.v1",
        "decision_at":next(iter(dates.values())).isoformat(),
        "generated_at":now.isoformat(),
        "risk_on":signals,
        "spy_target_weight":sum(signals.values())/4,
        "source_ledger_sha256":digests,
        "provenance":"Causal strategy decisions; upstream live PIT availability NOT certified",
        "execution_enabled":False
    }
