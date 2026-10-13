import unittest
from datetime import datetime,timezone
from pathlib import Path
import pandas as pd
from freeburg.deploy.capture_dividends import calculate

class DividendIndexTests(unittest.TestCase):
    def test_constant_price_cash_dividend_identity(self):
        dates=pd.bdate_range("2023-01-02","2025-07-01")
        pr=pd.Series(100.,index=dates)
        gross=pd.Series([100.*1.001**i for i in range(len(dates))],index=dates)
        daily,q=calculate(pr,gross,now=datetime(2025,7,10,tzinfo=timezone.utc))
        self.assertEqual(len(q),10)
        self.assertAlmostEqual(float(daily.dividend_points.iloc[0]),.1,places=6)
    def test_future_date_refused(self):
        dates=pd.bdate_range("2023-01-02","2025-07-01")
        price=pd.Series(100.,index=dates)
        with self.assertRaisesRegex(ValueError,"later than capture"):
            calculate(price,price,now=datetime(2025,6,1,tzinfo=timezone.utc))
if __name__=="__main__":unittest.main()
