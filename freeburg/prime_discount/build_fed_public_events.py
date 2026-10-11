"""Alternative Fed H.15 source for Prime/Discount (not a PIT-certified feed).

Run as a module from the repository root. Never overwrite frozen benchmark inputs.
"""
from __future__ import annotations
import argparse
from datetime import date
import json
from pathlib import Path
import pandas as pd
from freeburg.primas.build_historical_events import _fed_series, _iso
from freeburg.tools.free_data import load_prices

def align_past(series: pd.Series, dates: pd.DatetimeIndex) -> pd.Series:
    s=pd.to_numeric(series,errors='coerce').dropna().sort_index()
    s.index=pd.DatetimeIndex(s.index).tz_localize(None)
    s=s[~s.index.duplicated(keep='last')]
    return s.reindex(s.index.union(dates)).sort_index().ffill().reindex(dates)

def make_rows(prices, bank_prime, old_discount, primary_credit,
              cutover=date(2003,1,9), end=date(2013,9,27)):
    dates=pd.DatetimeIndex(sorted(d for d in prices if d<=end))
    bank,old,new=[align_past(s,dates) for s in (bank_prime,old_discount,primary_credit)]
    out=[]
    for ts in dates:
        d=ts.date()
        discount=old.loc[ts] if d<cutover else new.loc[ts]
        if pd.isna(bank.loc[ts]) or pd.isna(discount):
            continue
        for dataset, instrument, value, minute in (
            ('index.sp500.level.1w','SPX',prices[d],0),
            ('rates.bank_prime.1w','US',float(bank.loc[ts]),0),
            ('rates.discount_rate.1w','US',float(discount),0),
            ('clock.weekly.freeburg',None,None,1)):
            out.append({'source':'fed_h15_ALTERNATIVE_not_PIT',
                        'dataset':dataset,'instrument':instrument,
                        'event_time':_iso(ts,0),'available_at':_iso(ts,20,minute),
                        'payload':value})
    return out

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--prices',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--through',type=date.fromisoformat,default=date(2013,9,27))
    a=p.parse_args()
    if a.output.exists():
        p.error('Refusing to replace an existing file')
    prices=load_prices(a.prices)
    names=('RIFSPBLP_N.WW','H0.RIFSRD_F02_N.WW','RIFSRP_F02_N.WW')
    rates=[_fed_series(name) for name in names]
    rows=make_rows(prices,*rates,end=a.through)
    if not rows:
        raise RuntimeError('No aligned input weeks; inspect Fed series and local prices')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('w') as fh:
        for row in rows:
            fh.write(json.dumps(row,sort_keys=True)+'\n')
    print(json.dumps({'output':str(a.output),
        'decision_weeks':sum(r['dataset']=='clock.weekly.freeburg' for r in rows),
        'status':'ALTERNATIVE_NOT_PIT_NO_PARITY_CLAIM'},indent=2))

if __name__=='__main__':
    main()
