"""Compare alternate Prime/Discount historical inputs to the frozen benchmark.

Never declares a source 'exact' unless all source levels and all risk signals
agree on the requested dated sample. This does *not* certify original PIT status.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import pandas as pd
from freeburg.tools.free_data import load_prices


def _asof(source: pd.Series, cal: pd.DatetimeIndex) -> pd.Series:
    source=pd.to_numeric(source,errors='coerce').dropna().sort_index()
    source=source[~source.index.duplicated(keep='last')]
    return source.reindex(source.index.union(cal)).sort_index().ffill().reindex(cal)


def frozen_rates(path: Path, cal: pd.DatetimeIndex) -> dict[str,pd.Series]:
    """Load legacy change-event data. Use only with a local research fixture."""
    x=pd.read_csv(path,parse_dates=['date'])
    series={}
    for name,code in (('prime','DPRIME'),('discount','INTDSRUSM193N')):
        s=x[x.series.eq(code)].set_index('date')['value']
        if s.empty:raise ValueError(f"Missing legacy series {code}")
        series[name]=_asof(s,cal)
    return series


def alternative_rates(path: Path, cal: pd.DatetimeIndex) -> dict[str,pd.Series]:
    values={'prime':{},'discount':{},'spx':{}}
    alias={'rates.bank_prime.1w':'prime','rates.discount_rate.1w':'discount','index.sp500.level.1w':'spx'}
    for line in path.read_text().splitlines():
        if not line.strip():continue
        x=json.loads(line)
        key=alias.get(x.get('dataset'))
        if key:
            day=pd.Timestamp(x['event_time'][:10])
            v=float(x['payload'])
            if day in values[key] and values[key][day]!=v:
                raise ValueError(f"Duplicate conflicting {key} on {day}")
            values[key][day]=v
    result={}
    for name in values:
        if not values[name]:raise ValueError(f"No generated observations for {name}")
        result[name]=pd.Series(values[name],dtype=float).sort_index().reindex(cal)
    return result


def state(spx: pd.Series, prime: pd.Series, discount: pd.Series, n: int=50)->pd.Series:
    spread=prime-discount
    valid=(spread.rolling(n).count()==n)&(spx.rolling(n).count()==n)
    on=(spread<spread.rolling(n).mean())&(spx>spx.rolling(n).mean())
    return on.where(valid)


def comparison(price_csv: Path, benchmark_rates: Path, alternative_events: Path,
               start: str='1970-01-02', end: str='2013-09-27', window: int=50) -> dict:
    price=load_prices(price_csv)
    ix=pd.DatetimeIndex(sorted(price))
    spx=pd.Series([price[d.date()] for d in ix],index=ix,dtype=float)
    ref=frozen_rates(benchmark_rates,ix)
    alt=alternative_rates(alternative_events,ix)
    baseline=state(spx,ref['prime'],ref['discount'],window)
    candidate=state(alt['spx'],alt['prime'],alt['discount'],window)
    mask=(baseline.notna()&candidate.notna()&(ix>=pd.Timestamp(start))&(ix<=pd.Timestamp(end)))
    checked=int(mask.sum())
    if checked<1: raise ValueError('No overlapping valid decision weeks')
    differing=mask&baseline.ne(candidate)
    on_reference=int(baseline.loc[mask].sum())
    on_alternative=int(candidate.loc[mask].sum())
    def entries(series: pd.Series)->int:
        z=series.loc[mask].astype(int)
        return int(((z==1)&(z.shift(1)==0)).sum())
    level_results={}
    for key in ('spx','prime','discount'):
        reference=spx if key=='spx' else ref[key]
        test=alt[key]
        checked_levels=mask&reference.notna()&test.notna()
        delta=(reference-test).abs()
        level_results[key]={
            'compared_weeks':int(checked_levels.sum()),
            'mismatches_gt_1e_minus_8':int((checked_levels&(delta>1e-8)).sum()),
            'maximum_absolute_difference':round(float(delta.loc[checked_levels].max()),8)}
    diffs=[d.strftime('%Y-%m-%d') for d in ix[differing]]
    exact=(not diffs and all(v['mismatches_gt_1e_minus_8']==0 for v in level_results.values()))
    return {
        'comparison_period':[start,end],
        'decision_weeks':checked,
        'different_decisions':len(diffs),
        'agreement_percent':round(100*(1-len(diffs)/checked),4),
        'reference_risk_on_weeks':on_reference,
        'alternative_risk_on_weeks':on_alternative,
        'reference_entries_within_window':entries(baseline),
        'alternative_entries_within_window':entries(candidate),
        'first_different_dates':diffs[:20],
        'input_levels':level_results,
        'source_equivalence':'EXACT_WITHIN_TOLERANCE' if exact else 'ALTERNATIVE_DIFFERENT',
        'pit_verification':'NOT_CLAIMED',
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--prices',type=Path,required=True)
    p.add_argument('--reference-rates',type=Path,required=True)
    p.add_argument('--candidate-events',type=Path,required=True)
    p.add_argument('--start',default='1970-01-02')
    p.add_argument('--end',default='2013-09-27')
    a=p.parse_args()
    print(json.dumps(comparison(a.prices,a.reference_rates,a.candidate_events,a.start,a.end),indent=2))


if __name__=='__main__':
    main()
