"""X publishing must be traceable, stale-data safe and duplicate-free."""
from __future__ import annotations
import hashlib,json,os,tempfile,unittest
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
from freeburg.deploy.x_forward import validate,format_post,run

NOW=datetime(2026,10,12,6,tzinfo=timezone.utc)
STATES={"primas":0,"triple40":0,"pushen":1,"competitive":0}

def fixture(root:Path):
    snap=root/"capture"; snap.mkdir()
    for d in ("market","canonical","eps","dividends"):
        (snap/d).mkdir()
        (snap/d/"manifest.json").write_text('{"test":"source"}')
    (snap/"canonical/signal.json").write_text('{"test":"canonical"}')
    state={
        "time":"2026-10-12T05:01:38+00:00",
        "snapshot":str(snap),
        "all_data_stages_ok":True,"canonical_shadow_agrees":True,
        "canonical":{"schema":"freeburg.four.canonical-shadow.v1",
                     "captured_utc":"2026-10-12T05:01:38+00:00",
                     "decision_friday":"2026-10-09","states":STATES,
                     "spy_target_weight":.25,
                     "actual_causaltrader_strategy_classes":True,
                     "paper_orders_authorized":False},
        "shadow":{"schema":"freeburg.four.weekly-shadow.v1",
                  "decision_friday":"2026-10-09",
                  "spy_target_weight":.25,"states":STATES}
    }
    latest=root/"latest.json"
    latest.write_text(json.dumps(state))
    return latest,root/"out"

class XForwardTests(unittest.TestCase):
    def test_preview(self):
        with tempfile.TemporaryDirectory() as tmp:
            latest,out=fixture(Path(tmp))
            result=run(latest,out,now=NOW)
            self.assertEqual(result["status"],"DRAFT")
            self.assertEqual(result["model_weight"],.25)
            self.assertIn("25% SPY",result["text"])
            self.assertLess(len(result["text"]),280)
            self.assertTrue((out/"drafts/2026-10-09.json").exists())
    def test_no_credentials_means_no_post(self):
        with tempfile.TemporaryDirectory() as tmp:
            latest,out=fixture(Path(tmp))
            with patch.dict(os.environ,{"X_ENABLE_POSTING":"NO"}):
                result=run(latest,out,now=NOW,post=True)
            self.assertEqual(result["status"],"DRAFT_X_POSTING_NOT_AUTHORIZED")
            self.assertFalse((out/"posts/2026-10-09.json").exists())
    def test_opt_in_and_duplicate(self):
        with tempfile.TemporaryDirectory() as tmp:
            latest,out=fixture(Path(tmp))
            called=[]
            def mock_send(message):
                called.append(message)
                return {"id":"123"}
            fake={"X_ENABLE_POSTING":"YES",
                  "X_API_KEY":"test","X_API_SECRET":"test",
                  "X_ACCESS_TOKEN":"test","X_ACCESS_TOKEN_SECRET":"test"}
            with patch.dict(os.environ,fake):
                first=run(latest,out,now=NOW,post=True,api_send=mock_send)
                repeat=run(latest,out,now=NOW,post=True,api_send=mock_send)
            self.assertTrue(first["posted"])
            self.assertEqual(first["post_id"],"123")
            self.assertTrue(repeat["duplicate_prevented"])
            self.assertEqual(len(called),1)
    def test_failure_never_retries_ambiguous_post(self):
        with tempfile.TemporaryDirectory() as tmp:
            latest,out=fixture(Path(tmp))
            fake={"X_ENABLE_POSTING":"YES",
                  "X_API_KEY":"test","X_API_SECRET":"test",
                  "X_ACCESS_TOKEN":"test","X_ACCESS_TOKEN_SECRET":"test"}
            calls=[]
            def bad(message):
                calls.append(message);raise TimeoutError("uncertain")
            with patch.dict(os.environ,fake):
                failed=run(latest,out,now=NOW,post=True,api_send=bad)
                retry=run(latest,out,now=NOW,post=True,api_send=bad)
            self.assertEqual(failed["status"],"POSTING_UNCERTAIN_MANUAL_RECONCILIATION_REQUIRED")
            self.assertTrue(retry["duplicate_prevented"])
            self.assertEqual(len(calls),1)
    def test_stale_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            latest,out=fixture(Path(tmp))
            with self.assertRaisesRegex(ValueError,"latest Friday"):
                run(latest,out,now=datetime(2026,10,16,6,tzinfo=timezone.utc))

if __name__=="__main__":unittest.main()
