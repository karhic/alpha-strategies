import unittest
from datetime import datetime,timezone
from freeburg.deploy.paper_live import validate_capture,in_trade_window,spy_price

class AutoPaperTests(unittest.TestCase):
    def _state(self):
        a={"primas":0,"triple40":0,"pushen":1,"competitive":0}
        return {"all_data_stages_ok":True,"canonical_shadow_agrees":True,
          "canonical":{"schema":"freeburg.four.canonical-shadow.v1",
            "states":a,"decision_friday":"2026-10-09",
            "spy_target_weight":.25,"actual_causaltrader_strategy_classes":True,
            "paper_orders_authorized":False,"captured_utc":"2026-10-12T04:52:30+00:00"},
          "shadow":{"schema":"freeburg.four.weekly-shadow.v1",
             "decision_friday":"2026-10-09","states":a,"spy_target_weight":.25}}
    def test_recent_agreement_passes(self):
        d,w=validate_capture(self._state(),datetime(2026,10,12,14,0,tzinfo=timezone.utc))
        self.assertEqual((d,w),("2026-10-09",.25))
    def test_mismatch_rejected(self):
        x=self._state();x["shadow"]["spy_target_weight"]=.50
        with self.assertRaises(ValueError):validate_capture(x,datetime(2026,10,12,14,0,tzinfo=timezone.utc))
    def test_monday_new_york_daylight(self):
        self.assertTrue(in_trade_window(datetime(2026,10,12,14,0,tzinfo=timezone.utc)))
        self.assertFalse(in_trade_window(datetime(2026,10,12,5,0,tzinfo=timezone.utc)))
    def test_stale_rejected(self):
        with self.assertRaises(ValueError):
            validate_capture(self._state(),datetime(2026,10,20,14,0,tzinfo=timezone.utc))
if __name__=="__main__":unittest.main()
