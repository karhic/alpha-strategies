import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import pandas as pd
from freeburg.tools.overlay_oos_quarterly_90d import overlay

class QuarterlyOverlayTests(unittest.TestCase):
    def test_replaces_only_expected_dataset(self):
        with TemporaryDirectory() as d:
            root=Path(d)
            dates=pd.date_range("1990-03-31",periods=120,freq="QE-DEC")
            q=pd.DataFrame({"quarter_date":dates,"as_reported_eps":[10.]*120,
                            "dividends_per_share":[2.]*120})
            q.to_csv(root/"quarters.csv",index=False)
            events=[]
            for day in pd.date_range("2019-06-07",periods=5,freq="W-FRI"):
                key=day.date().isoformat()
                events.extend([
                    {"dataset":"index.sp500.level.1w","event_time":key+"T00:00:00+00:00","payload":200.,"source":"original"},
                    {"dataset":"fundamentals.sp500.earnings_yield.1w","event_time":key+"T00:00:00+00:00","payload":1.,"source":"original"},
                    {"dataset":"rates.commercial_paper.3m.1w","event_time":key+"T00:00:00+00:00","payload":3.,"source":"original"}])
            (root/"original.jsonl").write_text("".join(json.dumps(x)+"\n" for x in events))
            result=overlay(root/"quarters.csv",root/"original.jsonl",root/"overlaid.jsonl","pushen",None)
            self.assertEqual(result["overlaid_rows"],5)
            out=[json.loads(z) for z in (root/"overlaid.jsonl").read_text().splitlines()]
            self.assertEqual([z["payload"] for z in out if z["dataset"]=="rates.commercial_paper.3m.1w"],[3.]*5)
            eps=[z for z in out if z["dataset"]=="fundamentals.sp500.earnings_yield.1w"]
            self.assertTrue(all(z["payload"]==20 for z in eps))
            self.assertTrue(all("NOT_CERTIFIED_PIT" in z["source"] for z in eps))
if __name__=="__main__":unittest.main()
