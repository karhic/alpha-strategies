from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from causaltrader import AuditLog, DataEvent, DecisionOnlyPlanner, ReplayEngine, SimBroker

from strategy import PrimasStrategy

HERE = Path(__file__).resolve().parent
DEFAULT_EVENTS = HERE / "data" / "primas_benchmark_events.jsonl"
DEFAULT_LEDGER = HERE / "runs" / "primas_benchmark_ledger.jsonl"


def load_events(path: Path, end: datetime | None = None) -> list[DataEvent]:
    events: list[DataEvent] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            event_time = datetime.fromisoformat(row["event_time"])
            available_at = datetime.fromisoformat(row["available_at"])
            if end is not None and event_time > end:
                continue
            events.append(
                DataEvent(
                    source=row["source"],
                    dataset=row["dataset"],
                    instrument=row["instrument"],
                    event_time=event_time,
                    available_at=available_at,
                    payload=row["payload"],
                )
            )
    return events


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=Path, default=DEFAULT_EVENTS)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--end", default="2013-09-27T23:59:59+00:00")
    args = parser.parse_args()

    args.ledger.parent.mkdir(parents=True, exist_ok=True)
    if args.ledger.exists():
        args.ledger.unlink()
    end = datetime.fromisoformat(args.end) if args.end else None
    audit = AuditLog(args.ledger)
    replay = ReplayEngine(
        strategy=PrimasStrategy(),
        broker=SimBroker(),
        events=load_events(args.events, end=end),
        audit=audit,
        planner=DecisionOnlyPlanner(),
        config={"profile": "freeburg_benchmark_decisions", "lookback": 52},
    )
    replay.run()
    print(args.ledger)


if __name__ == "__main__":
    main()
