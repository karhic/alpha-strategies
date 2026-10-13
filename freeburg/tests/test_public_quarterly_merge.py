import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import pandas as pd
from freeburg.tools.merge_public_quarterlies import merge

class PublicQuarterlyTests(unittest.TestCase):
    def test_rejects_missing_overlap(self):
        with TemporaryDirectory() as tmp:
            d=Path(tmp)
            q=pd.DataFrame({'quarter_date':pd.date_range('1988-03-31','2022-06-30',freq='QE-DEC'), 'as_reported_eps':1.0,'dividends_per_share':2.0})
            q.to_csv(d/'official.csv',index=False)
            pd.DataFrame({'quarter_date':['2025-09-30'],'as_reported_eps':[1]}).to_csv(d/'eps.csv',index=False)
            pd.DataFrame({'quarter_date':['2025-09-30'],'dividends_per_share':[2]}).to_csv(d/'div.csv',index=False)
            with self.assertRaisesRegex(ValueError,'Insufficient official overlap'):
                merge(d/'official.csv',d/'eps.csv',d/'div.csv',d/'out.csv')
