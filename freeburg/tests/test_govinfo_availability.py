"""Regression tests for GovInfo vintage timing barriers."""
import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from freeburg.tools.govinfo_pit_events import emit


class GovinfoAvailabilityTests(unittest.TestCase):
    def test_no_issue_backdating_and_no_retroactive_backfill_flood(self):
        with TemporaryDirectory() as t:
            source=Path(t)/"vintages.csv"
            fields=["series","period_date","value","issue","issue_date",
                    "archive_record_created","earliest_scenario_date","source_row",
                    "source_url","availability_status"]
            rows=[]
            for period,value in (("2011-01-01",1.9),("2011-02-01",2.0)):
                rows.append({"series":"dividend_yield","period_date":period,
                             "value":value,"issue":"2011-02","issue_date":"2011-02-01",
                             "archive_record_created":"2011-03-15",
                             "earliest_scenario_date":"2011-03-15",
                             "source_row":"5","source_url":"test://",
                             "availability_status":"ARCHIVE_RECORD_CREATION_PROXY_NOT_FIRST_PUBLIC_RELEASE"})
            with source.open("w",newline="") as f:
                w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
            out=Path(t)/"events.jsonl"
            result=emit(source,out)
            self.assertEqual(result["events"],1)
            self.assertEqual(result["suppressed_reprinted_history_rows"],1)
            item=json.loads(out.read_text().strip())
            self.assertEqual(item["event_time"][:10],"2011-02-01")
            self.assertEqual(item["available_at"][:10],"2011-03-15")
            self.assertGreater(item["available_at"],item["event_time"])

    def test_reject_source_claiming_early_availability(self):
        with TemporaryDirectory() as t:
            source=Path(t)/"vintages.csv"
            source.write_text(
                "series,period_date,value,issue,issue_date,archive_record_created,"
                "earliest_scenario_date,source_row,source_url,availability_status\n"
                "earnings_yield,2013-01-01,5,2013-01,2013-01-01,2012-12-20,"
                "2012-12-20,1,test://,ARCHIVE_RECORD_CREATION_PROXY_NOT_FIRST_PUBLIC_RELEASE\n")
            with self.assertRaisesRegex(ValueError,"Lookahead timestamp"):
                emit(source,Path(t)/"out.jsonl")
