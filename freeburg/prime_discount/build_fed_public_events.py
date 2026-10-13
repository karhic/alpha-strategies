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

def fred_json_series(path: Path) -> pd.Series:
    """Import a *user-provided* FRED API observations JSON response.

    FRED may carry third-party data. This importer downloads nothing, and
    intentionally imposes no redistribution license on the source material.
    """
    payload=json.loads(path.read_text(encoding="utf-8"))
    observations=payload.get("observations")
    if not isinstance(observations,list) or not observations:
        raise ValueError(f"No FRED observations in {path}")
    values={}
    for obs in observations:
        raw=obs.get("value")
        try:
            v=float(raw)
        except (TypeError,ValueError):
            continue
        if not (-9990 < v < 1e100):
            continue
        t=pd.Timestamp(obs["date"]).normalize()
        if t in values and values[t]!=v:
            raise ValueError(f"Conflicting values at {t} in {path}")
        values[t]=v
    if not values:
        raise ValueError(f"No valid numeric FRED observations in {path}")
    return pd.Series(values,dtype=float).sort_index()


def fed_archived_series(directory: Path, filename: str, column: str) -> pd.Series:
    """Read the official H.15 weekly observations saved by the research archive.

    Exclude the Fed's -9999 missing-value sentinel. Archive files contain
    Wednesday-ending weekly observations; Friday decisions use last available.
    """
    path = directory / filename
    df = pd.read_csv(path, parse_dates=["week_ending"])
    s = pd.to_numeric(df[column], errors="coerce")
    s = pd.Series(s.to_numpy(), index=pd.DatetimeIndex(df["week_ending"]))
    return s.where(s > -9990).dropna().sort_index()


def make_rows(prices, bank_prime, old_discount, primary_credit,
              cutover=date(2003,1,9), end=date(2013,9,27),
              source_name='fed_h15_ALTERNATIVE_not_PIT'):
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
            out.append({'source':source_name,
                        'dataset':dataset,'instrument':instrument,
                        'event_time':_iso(ts,0),'available_at':_iso(ts,20,minute),
                        'payload':value})
    return out

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--prices',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--fed-archive-dir',type=Path,
                   help='Use local Fed H.15 raw weekly exports (no network)')
    p.add_argument('--fred-prime-json',type=Path,
                   help='User-obtained FRED observations JSON for DPRIME')
    p.add_argument('--fred-discount-json',type=Path,
                   help='User-obtained FRED observations JSON for INTDSRUSM193N')
    p.add_argument('--through',type=date.fromisoformat,default=date(2013,9,27))
    a=p.parse_args()
    if a.output.exists():
        p.error('Refusing to replace an existing file')
    prices=load_prices(a.prices)
    if bool(a.fred_prime_json) != bool(a.fred_discount_json):
        p.error('Specify both --fred-prime-json and --fred-discount-json')
    if a.fed_archive_dir and a.fred_prime_json:
        p.error('Choose one source: FRED JSON or H.15 archive')
    names=('RIFSPBLP_N.WW','H0.RIFSRD_F02_N.WW','RIFSRP_F02_N.WW')
    if a.fred_prime_json:
        prime=fred_json_series(a.fred_prime_json)
        discount=fred_json_series(a.fred_discount_json)
        rates=[prime,discount,discount]
        profile='FRED_DPRIME_IMF_INTDSRUSM193N_RETROSPECTIVE_NOT_PIT'
    elif a.fed_archive_dir:
        specs=(
            ('H15_RAW_RIFSPBLP_N_WW.csv','prime_rate'),
            ('H15_RAW_H0_RIFSRD_F02_N_WW.csv','discount_rate'),
            ('H15_RAW_RIFSRP_F02_N_WW.csv','primary_credit_rate'),
        )
        rates=[fed_archived_series(a.fed_archive_dir,*x) for x in specs]
        profile='FED_H15_ALTERNATIVE_NOT_PIT'
    else:
        rates=[_fed_series(name) for name in names]
        profile='FED_H15_ALTERNATIVE_NOT_PIT'
    rows=make_rows(prices,*rates,end=a.through,source_name=profile)
    if not rows:
        raise RuntimeError('No aligned input weeks; inspect Fed series and local prices')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('w') as fh:
        for row in rows:
            fh.write(json.dumps(row,sort_keys=True)+'\n')
    print(json.dumps({'output':str(a.output),
        'decision_weeks':sum(r['dataset']=='clock.weekly.freeburg' for r in rows),
        'status':profile},indent=2))

if __name__=='__main__':
    main()
