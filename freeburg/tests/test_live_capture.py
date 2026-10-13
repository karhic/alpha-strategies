import hashlib,json,unittest
from datetime import datetime,timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from freeburg.deploy.assess_capture import assess

class CaptureAuditTests(unittest.TestCase):
    def _fixture(self,path):
        blobs={"spx.json":b"local provider payload","fed_h15.zip":b"local fed payload"}
        sources={}
        for name,body in blobs.items():
            (path/name).write_bytes(body)
            sources[name]={"sha256":hashlib.sha256(body).hexdigest(),
                "source_url":"https://example.invalid/"+name}
        manifest={"schema":"freeburg.live.market-capture.v1",
            "captured_at_utc":"2026-10-09T22:00:00+00:00",
            "target_completed_friday":"2026-10-09",
            "sources":sources,"series":{},"market_sources_ready":True,
            "fundamental_eps_dividends_ready":False,"signal_ready":False}
        (path/"manifest.json").write_text(json.dumps(manifest))
    def test_verified_live_snapshot(self):
        with TemporaryDirectory() as temp:
            path=Path(temp);self._fixture(path)
            report=assess(path)
            self.assertTrue(report["market_capture_verified"])
            self.assertFalse(report["ready_for_full_signals"])
            self.assertFalse(report["ibkr_orders_authorized"])
    def test_tampered_capture_fails(self):
        with TemporaryDirectory() as temp:
            path=Path(temp);self._fixture(path)
            with (path/"spx.json").open("ab") as f:f.write(b"tampered")
            with self.assertRaisesRegex(ValueError,"tampering"):
                assess(path)
if __name__=="__main__":unittest.main()
