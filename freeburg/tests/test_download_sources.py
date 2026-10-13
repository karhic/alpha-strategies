"""No-network regression tests for fresh market-data providers."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from datetime import datetime,timezone,timedelta
from freeburg.tools.download_spx import parse,download as spx_download
from freeburg.tools.download_fred import download as fred_download

class FakeResponse:
    status=200
    def __init__(self,blob):self.blob=blob
    def __enter__(self):return self
    def __exit__(self,*a):pass
    def read(self,n):return self.blob[:n]

def response(body):
    return lambda request,timeout:FakeResponse(json.dumps(body).encode())

class SourceDownloadTests(TestCase):
    def test_yahoo_price_and_weekly_conversion(self):
        dates=[datetime(2026,1,5,tzinfo=timezone.utc),
               datetime(2026,1,9,tzinfo=timezone.utc),
               datetime(2026,1,12,tzinfo=timezone.utc)]
        data={"chart":{"result":[{"timestamp":[int(d.timestamp()) for d in dates],
              "indicators":{"quote":[{"close":[101,105,110]}]}}]}}
        with TemporaryDirectory() as td:
            z=spx_download(Path(td)/"spx",expected_min=3,transport=response(data))
            self.assertEqual(z["rows_weekly"],2)
            self.assertTrue((Path(td)/"spx/spx_weekly.csv").exists())
            self.assertNotIn("licensed",z["status"].lower())

    def test_fred_series_and_no_key_in_manifest(self):
        k="a"*32
        def transport(request,timeout):
            return FakeResponse(json.dumps({"observations":[{"date":"1950-01-01","value":"2.2"}]}).encode())
        with TemporaryDirectory() as td:
            z=fred_download(Path(td)/"fred",api_key=k,opener=transport)
            self.assertEqual(len(z["results"]),2)
            self.assertNotIn(k,(Path(td)/"fred/manifest.json").read_text())
            self.assertEqual(z["results"][0]["observations_numeric"],1)

    def test_reject_invalid_key(self):
        with TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                fred_download(Path(td)/"fred",api_key="invalid")
