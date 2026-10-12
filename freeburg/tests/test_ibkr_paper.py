"""Paper sizing should work without a broker connection."""
import json, unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from freeburg.deploy.ibkr_paper import plan,read_signal

class TestPaperOrders(unittest.TestCase):
    def test_partial_to_full(self):
        x=plan(target_weight=.75,net_liquidation=100000,spy_price=500,
               spy_position=100)
        self.assertEqual(x["action"],"BUY")
        self.assertEqual(x["quantity"],50)
        self.assertEqual(x["target_shares"],150)
    def test_partial_to_cash(self):
        x=plan(target_weight=0,net_liquidation=100000,spy_price=500,spy_position=20)
        self.assertEqual(x["action"],"SELL")
        self.assertEqual(x["quantity"],20)
    def test_repeated_snapshot(self):
        x=plan(target_weight=.5,net_liquidation=100000,spy_price=500,spy_position=100)
        self.assertEqual(x["action"],"HOLD")
    def test_open_orders_fail_closed(self):
        with self.assertRaisesRegex(ValueError,"Open SPY orders"):
            plan(target_weight=.75,net_liquidation=100000,spy_price=500,
                 spy_position=100,open_spy_orders=1)
    def test_paper_port_gate_and_signal(self):
        with TemporaryDirectory() as t:
            p=Path(t)/"signal.json"
            p.write_text(json.dumps({"schema":"freeburg.four.weekly-signal.v1",
                "spy_target_weight":.5,"risk_on":{"primas":1,"triple40":1,"pushen":0,
                "competitive":0},"execution_enabled":False}))
            self.assertEqual(read_signal(p)["spy_target_weight"],.5)
            bad=json.loads(p.read_text());bad["spy_target_weight"]=.75;p.write_text(json.dumps(bad))
            with self.assertRaises(ValueError):read_signal(p)
if __name__=="__main__":unittest.main()
