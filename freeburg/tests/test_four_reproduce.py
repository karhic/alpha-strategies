"""Tests for reproducibility input validation and exact model fingerprint."""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import pandas as pd
from freeburg.tools.prepare_four_frozen_inputs import prepare
from freeburg.tools.reproduce_four_from_sources import calculate,report

ROOT=Path(__file__).resolve().parents[1]

def synthetic_source_tables(root:Path)->Path:
    """Synthetic fixtures replace unredistributable historical input tables."""
    src=root/'fixtures'
    for sleeve in ('pushen','competitive'):
        (src/sleeve/'data').mkdir(parents=True,exist_ok=True)
    dates=pd.date_range('2020-01-03',periods=8,freq='W-FRI')
    pd.DataFrame({'date':dates,'spx':range(100,108), 'cp':[2.5]*8}).to_csv(
        src/'pushen/data/pit_weekly_inputs.csv',index=False)
    pd.DataFrame({'date':dates,'tbond_10y':[3.0]*8,'tbill_3m':[1.5]*8,
                  'cpi':[257.]*8}).to_csv(src/'competitive/data/pit_weekly_inputs.csv',index=False)
    return src
class FourReproductionTests(unittest.TestCase):
    def test_frozen_input_preparation_checks_hashes(self):
        with TemporaryDirectory() as temp:
            out=Path(temp)/"inputs"
            manifest=prepare(synthetic_source_tables(Path(temp)),out)
            self.assertEqual(manifest["dates"],8)
            self.assertTrue((out/"source_manifest.json").is_file())
            with self.assertRaises(FileExistsError):
                prepare(synthetic_source_tables(Path(temp)),out)
    def test_source_to_return_requires_real_quarterly(self):
        with TemporaryDirectory() as temp:
            d=Path(temp)
            prepare(synthetic_source_tables(d),d/"inputs")
            q=d/"quarters.csv"
            pd.DataFrame({"quarter_date":["2023-03-31"],
                "as_reported_eps":[1],"dividends_per_share":[2]}).to_csv(q,index=False)
            b=d/"baa.csv";pd.DataFrame({"observation_date":["2020-01-01"],"BAA":[5]}).to_csv(b,index=False)
            a=d/"agg.csv";pd.DataFrame({"date":["2024-01-05"],"agg":[.01]}).to_csv(a,index=False)
            with self.assertRaises(ValueError):
                calculate(d/"inputs/weekly_prices.csv",d/"inputs/macro.csv",q,b,a)
if __name__=="__main__":unittest.main()

class TimingAndInputIntegrityTests(unittest.TestCase):
    def test_duplicate_monthly_baa_rejected(self):
        with TemporaryDirectory() as temp:
            d=Path(temp)
            prepare(synthetic_source_tables(d),d/'frozen')
            q=d/'q.csv'
            pd.DataFrame({'quarter_date':pd.date_range('1988-03-31','2025-09-30',freq='QE-DEC'),
                          'as_reported_eps':1.0, 'dividends_per_share':2.0}).to_csv(q,index=False)
            b=d/'b.csv'
            pd.DataFrame({'observation_date':['2020-01-01','2020-01-31'],
                          'BAA':[5,6]}).to_csv(b,index=False)
            a=d/'agg.csv'
            pd.DataFrame({'date':['2024-01-05'],'agg':[.01]}).to_csv(a,index=False)
            with self.assertRaisesRegex(ValueError,'Multiple monthly BAA observations'):
                calculate(d/'frozen/weekly_prices.csv',d/'frozen/macro.csv',q,b,a)
    def test_research_outputs_must_not_be_labeled_pit_certified(self):
        import inspect
        from freeburg.tools import reproduce_four_from_sources as module
        source=inspect.getsource(module.calculate)
        self.assertIn('"historical_pit_certified":False',source)
        self.assertIn('"executable_backtest_certified":False',source)
