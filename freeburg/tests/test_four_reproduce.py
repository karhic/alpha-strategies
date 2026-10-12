"""Tests for reproducibility input validation and exact model fingerprint."""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import pandas as pd
from freeburg.tools.prepare_four_frozen_inputs import prepare
from freeburg.tools.reproduce_four_from_sources import calculate,report

ROOT=Path(__file__).resolve().parents[1]
class FourReproductionTests(unittest.TestCase):
    def test_frozen_input_preparation_checks_hashes(self):
        with TemporaryDirectory() as temp:
            out=Path(temp)/"inputs"
            manifest=prepare(ROOT,out)
            self.assertEqual(manifest["dates"],2959)
            self.assertTrue((out/"source_manifest.json").is_file())
            with self.assertRaises(FileExistsError):
                prepare(ROOT,out)
    def test_source_to_return_requires_real_quarterly(self):
        with TemporaryDirectory() as temp:
            d=Path(temp)
            prepare(ROOT,d/"inputs")
            q=d/"quarters.csv"
            pd.DataFrame({"quarter_date":["2023-03-31"],
                "as_reported_eps":[1],"dividends_per_share":[2]}).to_csv(q,index=False)
            b=d/"baa.csv";pd.DataFrame({"observation_date":["2020-01-01"],"BAA":[5]}).to_csv(b,index=False)
            a=d/"agg.csv";pd.DataFrame({"date":["2024-01-05"],"agg":[.01]}).to_csv(a,index=False)
            with self.assertRaises(ValueError):
                calculate(d/"inputs/weekly_prices.csv",d/"inputs/macro.csv",q,b,a)
if __name__=="__main__":unittest.main()
