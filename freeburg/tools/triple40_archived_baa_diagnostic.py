"""Diagnostic Triple-40 OOS replay with archived monthly Baa trend-flag input.

Uses the original Triple40Strategy unchanged except replaces the Baa-vs-MA
predicate *after 2013* with scratchpad archived binary Baa trend indicator.
This is not a PIT-vintage-certified series. It only isolates source identity.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import pandas as pd
from causaltrader import AuditLog,DataEvent,DecisionOnlyPlanner,ReplayEngine,SimBroker,TargetWeight
from freeburg.triple40.strategy import Triple40Strategy
from freeburg.triple40.run_replay import load_events

DATASET="research.moody_baa_below_40week_ma"
class Triple40ArchivedBaaDiagnostic(Triple40Strategy):
    name="freeburg_triple40_archived_baa_diagnostic"
    version="research_only_1"
    def on_event(self,ctx,event):
        if event.dataset!=self.config.decision_dataset:return ()
        if event.event_time.date()<pd.Timestamp("2013-10-04").date():
            return super().on_event(ctx,event)
        s=ctx.data.payload_history(self.config.spx_dataset,"SPX",count=40)
        c=ctx.data.payload_history(self.config.cp_dataset,"US",count=40)
        flag=ctx.data.payload_history(DATASET,"US",count=1)
        if len(s)<40 or len(c)<40 or not flag:return ()
        on=(float(s[-1])>sum(map(float,s))/40 and
            (bool(int(flag[-1])) or float(c[-1])<sum(map(float,c))/40))
        return (TargetWeight(self.config.risk_asset,float(on),tag="triple40_research_flag",
            reason=f"Archived Baa trend flag={int(flag[-1])}; cp/stock live window; risk_on={on}"),)
def run(original:Path,flags:Path,ledger:Path,end:str):
    from datetime import datetime,time,timezone
    if ledger.exists():raise FileExistsError(ledger)
    ev=load_events(original,datetime.fromisoformat(end))
    f=pd.read_csv(flags,parse_dates=["date"]).set_index("date")["baa_below_40w_ma"]
    extra=[]
    for dt,value in f.items():
        if dt>pd.Timestamp(end[:10]):continue
        extra.append(DataEvent("ARCHIVED_MONTHLY_BAA_BINARY_FLAG_NOT_PIT",DATASET,"US",
            datetime.combine(dt.date(),time(0),timezone.utc),
            datetime.combine(dt.date(),time(20),timezone.utc),float(value)))
    # Duplicate ordering at same timestamp resolved by event source ordering in engine;
    # 20:00 flag precedes 20:01 clock.
    ledger.parent.mkdir(parents=True,exist_ok=True)
    ReplayEngine(strategy=Triple40ArchivedBaaDiagnostic(),broker=SimBroker(),
        events=ev+extra,audit=AuditLog(ledger),planner=DecisionOnlyPlanner(),
        config={"profile":"research_only_archived_baa_trend_flag_not_pit"}).run()
    return {"events_original":len(ev),"flags_injected":len(extra),"ledger":str(ledger)}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--original-events",type=Path,required=True)
    p.add_argument("--flag-csv",type=Path,required=True)
    p.add_argument("--ledger",type=Path,required=True)
    p.add_argument("--end",default="2026-08-07T23:59:59+00:00")
    a=p.parse_args();print(json.dumps(run(a.original_events,a.flag_csv,a.ledger,a.end),indent=2))
if __name__=="__main__":main()
