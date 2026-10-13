import json,unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from freeburg.deploy.signals import build,SLEEVES
from freeburg.deploy.publish_x import render

class DeploymentTests(unittest.TestCase):
    def _make(self,root,states,when):
        for n in SLEEVES:
            row={"kind":"strategy_action","timestamp":when.isoformat(),
                 "payload":{"tag":n,"instrument":"SPY","weight":states[n]}}
            (root/(n+".jsonl")).write_text(json.dumps(row)+"\n")
    def test_snapshot_and_post_preview(self):
        with TemporaryDirectory() as temp:
            root=Path(temp);now=datetime(2026,10,9,20,1,tzinfo=timezone.utc)
            self._make(root,{"primas":1,"triple40":0,"pushen":1,"competitive":1},now)
            snap=build(root,now+timedelta(hours=3))
            self.assertEqual(snap["spy_target_weight"],.75)
            self.assertEqual(len(snap["source_ledger_sha256"]),4)
            self.assertIn("75%",render(snap))
            self.assertLessEqual(len(render(snap)),280)
    def test_stale_or_misaligned_fails(self):
        with TemporaryDirectory() as temp:
            root=Path(temp);when=datetime(2026,10,2,20,1,tzinfo=timezone.utc)
            self._make(root,dict.fromkeys(SLEEVES,1),when)
            with self.assertRaisesRegex(ValueError,"Stale"):
                build(root,when+timedelta(days=9))
            row={"kind":"strategy_action","timestamp":(when+timedelta(days=1)).isoformat(),
                "payload":{"tag":"primas","instrument":"SPY","weight":1}}
            (root/"primas.jsonl").write_text(json.dumps(row)+"\n")
            with self.assertRaisesRegex(ValueError,"timestamps differ"):
                build(root,when+timedelta(days=2))
    def test_invalid_weight(self):
        with TemporaryDirectory() as temp:
            root=Path(temp);t=datetime(2026,10,9,tzinfo=timezone.utc)
            self._make(root,dict.fromkeys(SLEEVES,1),t)
            x=json.loads((root/"primas.jsonl").read_text());x["payload"]["weight"]=.6
            (root/"primas.jsonl").write_text(json.dumps(x)+"\n")
            with self.assertRaisesRegex(ValueError,"binary"):
                build(root,t)
if __name__=="__main__":unittest.main()
