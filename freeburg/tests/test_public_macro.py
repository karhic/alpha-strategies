import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import pandas as pd
from freeburg.tools.build_public_weekly_inputs import build

class PublicMacroValidationTests(unittest.TestCase):
    def test_invalid_zip_fail_closed(self):
        with TemporaryDirectory() as t:
            d=Path(t)
            pd.DataFrame({'date':['2014-01-03'],'spx':[100.]}).to_csv(d/'spx.csv',index=False)
            (d/'h15.zip').write_text('not a ZIP')
            (d/'cpi.csv').write_text('not valid CPI')
            with self.assertRaises(Exception):
                build(d/'spx.csv',d/'h15.zip',d/'cpi.csv',d/'out')
