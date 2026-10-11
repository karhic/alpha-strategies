import csv
from datetime import date, timedelta
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import free_data as f

class FreeDataTests(unittest.TestCase):
    def test_import_prices_weekly(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'raw.csv'
            p.write_text('Date,Close\n2026-09-10,101\n2026-09-11,102\n2026-09-17,103\n')
            weekly=f.load_prices(p)
            self.assertEqual(weekly,{date(2026,9,11):102,date(2026,9,18):103})
            out=Path(t)/'out.csv'
            f.prices_to_file(p,out)
            self.assertEqual(f.price_comparison(out,out)['max_abs_bps'],0)

    def test_ma52_disagreement(self):
        with tempfile.TemporaryDirectory() as t:
            a,b=Path(t)/'a.csv',Path(t)/'b.csv'
            dt=date(2024,1,5)
            for path,last in [(a,110),(b,90)]:
                with path.open('w',newline='') as fh:
                    w=csv.writer(fh);w.writerow(['date','spx'])
                    for i in range(55):
                        w.writerow([(dt+timedelta(weeks=i)).isoformat(), last if i==54 else 100])
            self.assertEqual(f.price_comparison(a,b)['ma52_state_disagreements'],1)

    def test_govinfo_validation(self):
        self.assertTrue(f.govinfo_urls('2012-10','31')['xls'].endswith('ECONI-2012-10-Pg31.xls'))
        with self.assertRaises(ValueError):
            f.govinfo_urls('1995-03','31')

    def test_govinfo_extract_requires_month_label(self):
        rows=[['2010: Jan','2.1','5.4'],['Feb','2.0','.'],['Week ended 2010: Mar 9','2','4']]
        got=f.parse_govinfo_monthly_rows(rows,period_col=0,dividend_col=1,
            earnings_col=2,published_on=date(2010,5,12),source_url='test://')
        self.assertEqual(len(got),2)
        self.assertEqual(got[0]['period_date'],'2010-01-01')

if __name__=='__main__':
    unittest.main()
