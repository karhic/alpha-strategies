from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from causaltrader import AuditLog, DataEvent, DecisionOnlyPlanner, ReplayEngine, SimBroker
from freeburg.triple40.strategy import Triple40Strategy

HERE = Path(__file__).resolve().parent
DEFAULT_EVENTS = HERE / "data" / "triple40_benchmark_events.jsonl"
DEFAULT_LEDGER = HERE / "runs" / "triple40_benchmark_ledger.jsonl"


def load_events(path: Path, end: datetime | None = None) -> list[DataEvent]:
    out = []
    for line in path.read_text().splitlines():
        row = json.loads(line)
        event_time = datetime.fromisoformat(row["event_time"])
        if end is not None and event_time > end:
            continue
        out.append(DataEvent(row["source"], row["dataset"], row["instrument"], event_time,
                             datetime.fromisoformat(row["available_at"]), row["payload"]))
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--events", type=Path, default=DEFAULT_EVENTS)
    p.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    p.add_argument("--end", default="2013-09-27T23:59:59+00:00")
    a = p.parse_args()
    a.ledger.parent.mkdir(parents=True, exist_ok=True)
    if a.ledger.exists(): a.ledger.unlink()
    audit = AuditLog(a.ledger)
    replay = ReplayEngine(
        strategy=Triple40Strategy(), broker=SimBroker(),
        events=load_events(a.events, datetime.fromisoformat(a.end) if a.end else None),
        audit=audit, planner=DecisionOnlyPlanner(),
        config={"profile":"freeburg_historical","lookback":40},
    )
    replay.run()
    print(a.ledger)


if __name__ == "__main__": main()
