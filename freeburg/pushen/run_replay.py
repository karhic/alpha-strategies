from __future__ import annotations
import argparse,json
from datetime import datetime
from pathlib import Path
from causaltrader import AuditLog,DataEvent,DecisionOnlyPlanner,ReplayEngine,SimBroker
from strategy import PuShenStrategy
HERE=Path(__file__).resolve().parent
def load(path,end):
 out=[]
 for line in path.read_text().splitlines():
  r=json.loads(line); t=datetime.fromisoformat(r["event_time"])
  if t<=end: out.append(DataEvent(r["source"],r["dataset"],r["instrument"],t,datetime.fromisoformat(r["available_at"]),r["payload"]))
 return out
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--events",type=Path,default=HERE/"data/pushen_benchmark_events.jsonl"); ap.add_argument("--ledger",type=Path,default=HERE/"runs/pushen_benchmark_ledger.jsonl"); ap.add_argument("--end",default="2013-09-27T23:59:59+00:00"); a=ap.parse_args(); a.ledger.parent.mkdir(parents=True,exist_ok=True); a.ledger.unlink(missing_ok=True)
 ReplayEngine(strategy=PuShenStrategy(),broker=SimBroker(),events=load(a.events,datetime.fromisoformat(a.end)),audit=AuditLog(a.ledger),planner=DecisionOnlyPlanner(),config={"profile":"freeburg_pit_decisions"}).run(); print(a.ledger)
if __name__=="__main__": main()
