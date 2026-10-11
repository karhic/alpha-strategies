"""Smoke tests for the batch replay launcher."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from freeburg.reproduce_available import summarize, SLEEVES

class BatchReplayTests(unittest.TestCase):
    def test_five_real_sleeves_declared_heine_excluded(self):
        self.assertEqual(set(SLEEVES), {
            "primas","triple40","pushen","competitive","prime_discount"})

    def test_ledger_summary(self):
        with TemporaryDirectory() as d:
            path=Path(d)/"ledger.jsonl"
            events=[
                {"kind":"run_manifest","timestamp":"2020-01-01","payload":{}},
                {"kind":"data_event","timestamp":"2020-01-01","payload":{}},
                {"kind":"strategy_action","timestamp":"2020-01-02",
                 "payload":{"weight":1.0}}]
            path.write_text("".join(json.dumps(x)+"\n" for x in events))
            result=summarize(path)
            self.assertEqual(result["data_events"],1)
            self.assertEqual(result["strategy_decisions"],1)
            self.assertEqual(result["first_decision"],"2020-01-02")
