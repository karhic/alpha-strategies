from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from causaltrader import AuditLog, DataEvent, DecisionOnlyPlanner, ReplayEngine, SimBroker
from strategy import PrimeDiscountStrategy

HERE = Path(__file__).resolve().parent
DEFAULT_EVENTS = HERE / "data" / "prime_discount_benchmark_events.jsonl"
DEFAULT_LEDGER = HERE / "runs" / "prime_discount_benchmark_ledger.jsonl"


def load_events(path: Path, end: datetime | None = None) -> list[DataEvent]:
    out = []
    for line in path.read_text().splitlines():
        row = json.loads(line); t = datetime.fromisoformat(row["event_time"])
        if end is not None and t > end: continue
        out.append(DataEvent(row["source"], row["dataset"], row["instrument"], t,
                             datetime.fromisoformat(row["available_at"]), row["payload"]))
    return out

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--events", type=Path, default=DEFAULT_EVENTS)
    ap.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    ap.add_argument("--end", default="2013-09-27T23:59:59+00:00")
    args = ap.parse_args(); args.ledger.parent.mkdir(parents=True, exist_ok=True)
    if args.ledger.exists(): args.ledger.unlink()
    audit = AuditLog(args.ledger)
    ReplayEngine(strategy=PrimeDiscountStrategy(), broker=SimBroker(),
                 events=load_events(args.events, datetime.fromisoformat(args.end)),
                 audit=audit, planner=DecisionOnlyPlanner(),
                 config={"profile":"freeburg_benchmark_decisions"}).run()
    print(args.ledger)


if __name__ == "__main__":
    main()
