import json
from pathlib import Path
import tempfile
import unittest

try:
    from freeburg.prime_discount.build_fed_public_events import fred_json_series
    from freeburg.prime_discount.compare_sources import comparison
except ImportError as exc:
    raise ImportError("Install pandas and requests before running Prime/Discount tests") from exc


class HistoricalParityTests(unittest.TestCase):
    def test_fred_json_missing_and_duplicates(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'fred.json'
            p.write_text(json.dumps({'observations':[
                {'date':'2001-01-01','value':'2.25'},
                {'date':'2001-02-01','value':'.'},
                {'date':'2001-03-01','value':'2.5'},
            ]}))
            s=fred_json_series(p)
            self.assertEqual(len(s),2)
            self.assertEqual(float(s.iloc[1]),2.5)

    def test_comparator_identical_and_changed(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            prices=root/'prices.csv'
            rates=root/'rates.csv'
            events=root/'events.jsonl'
            prices.write_text('date,spx\n'+''.join(f'2020-{m:02d}-03,100\n' for m in range(1,13)))
            # Use explicit weekly Fridays for deterministic 50-week comparisons.
            from datetime import date,timedelta
            dates=[date(2020,1,3)+timedelta(weeks=i) for i in range(70)]
            prices.write_text('date,spx\n'+''.join(f'{dt},{100+i*.2}\n' for i,dt in enumerate(dates)))
            rates.write_text('date,series,value\n2019-12-01,DPRIME,5\n2019-12-01,INTDSRUSM193N,2\n')
            rows=[]
            for i,dt in enumerate(dates):
                vals={
                    'index.sp500.level.1w':100+i*.2,
                    'rates.bank_prime.1w':5,
                    'rates.discount_rate.1w':2}
                for ds,v in vals.items():
                    rows.append({'event_time':dt.isoformat()+'T00:00:00+00:00',
                                 'dataset':ds,'payload':v})
            events.write_text(''.join(json.dumps(row)+'\n' for row in rows))
            same=comparison(prices,rates,events,'2020-01-01','2021-12-31')
            self.assertEqual(same['source_equivalence'],'EXACT_WITHIN_TOLERANCE')
            self.assertEqual(same['different_decisions'],0)
            # Inject known input-level deviation: exact equivalence must now fail.
            rows[1]['payload']=8
            events.write_text(''.join(json.dumps(row)+'\n' for row in rows))
            changed=comparison(prices,rates,events,'2020-01-01','2021-12-31')
            self.assertEqual(changed['source_equivalence'],'ALTERNATIVE_DIFFERENT')


if __name__ == '__main__':
    unittest.main()
