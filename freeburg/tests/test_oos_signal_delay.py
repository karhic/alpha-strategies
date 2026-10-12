import unittest
import numpy as np
import pandas as pd
from freeburg.tools.audit_oos_signal_delay import analyze,SLEEVES,CASH_FACTORS

class DelayAuditTests(unittest.TestCase):
    def test_branch_reconstruction(self):
        dates=pd.date_range("2024-01-05",periods=60,freq="W-FRI")
        cp=pd.Series(4.,index=dates)
        stock=pd.Series(.012*np.sin(np.arange(60))+.002,index=dates)
        x=pd.DataFrame({"stock":stock},index=dates)
        for j,s in enumerate(SLEEVES):
            cash=cp/5200*CASH_FACTORS[s]
            signal=(np.arange(60)+j)%3==0
            x[s]=np.where(signal,stock,cash)
        z=analyze(x,cp)
        self.assertEqual(z["original_658_weeks"]["weeks"],60)
        self.assertEqual(z["one_week_delayed_657_weeks"]["weeks"],59)
        self.assertLess(max(z["all_sleeves_cash_equity_decomposition_max_abs_error"].values()),1e-15)
        self.assertNotEqual(z["one_week_delayed_657_weeks"]["terminal_wealth"],z["aligned_original_657_weeks"]["terminal_wealth"])
    def test_reject_unexplained_return(self):
        ix=pd.date_range("2024-01-05",periods=6,freq="W-FRI")
        cp=pd.Series(4.,index=ix)
        x=pd.DataFrame({"stock":.01},index=ix)
        for s in SLEEVES:x[s]=.01
        x.loc[ix[2],"Primas"]=.006
        with self.assertRaises(ValueError):analyze(x,cp)
if __name__=="__main__":unittest.main()
