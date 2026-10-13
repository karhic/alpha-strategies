"""Tests for isolated availability-aware fundamentals overlays."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from freeburg.tools.build_vintage_overlay import build

class OverlayTests(unittest.TestCase):
    def test_replaces_unavailable_frozen_values_and_preserves_clock(self):
        with TemporaryDirectory() as t:
            t=Path(t);base=t/"base.jsonl";ov=t/"ov.jsonl";out=t/"out.jsonl"
            base.write_text("\n".join(json.dumps(x) for x in [
                {"dataset":"fundamentals.sp500.earnings_yield.1w","event_time":"2011-01-01T00:00:00+00:00","available_at":"2011-01-01T20:00:00+00:00","payload":5},
                {"dataset":"clock.weekly.freeburg","event_time":"2011-01-07T00:00:00+00:00","available_at":"2011-01-07T20:01:00+00:00","payload":None}
            ])+"\n")
            ov.write_text(json.dumps({"dataset":"fundamentals.sp500.earnings_yield.1w","event_time":"2011-01-01T00:00:00+00:00",
               "available_at":"2011-03-15T23:59:00+00:00","payload":4.2})+"\n")
            res=build(base,ov,out,"pushen")
            self.assertEqual(res["removed_frozen_fundamentals"],1)
            events=[json.loads(s) for s in out.read_text().splitlines()]
            self.assertEqual(len(events),2)
            yield_event=next(x for x in events if x["dataset"]!="clock.weekly.freeburg")
            self.assertEqual(yield_event["event_time"],yield_event["available_at"])
            self.assertEqual(yield_event["source_period_time"][:10],"2011-01-01")
            self.assertEqual(yield_event["available_at"][:10],"2011-03-15")
