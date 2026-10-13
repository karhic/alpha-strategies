"""Independent public-source weekly SPX, CP, rates and CPI research inputs.

Normalizations are pinned to the published research model. Downloads made
later can include historical revisions; the construction is NOT PIT-certified.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
import pandas as pd
from freeburg.deploy.capture_live import h15_weekly,_fred_csv


def build(spx_weekly:Path,h15_zip:Path,cpi_csv:Path,out:Path):
    if out.exists():raise FileExistsError(out)
    p=pd.read_csv(spx_weekly,parse_dates=['date']).set_index('date').sort_index()['spx'].astype(float)
    if p.index.has_duplicates or p.index.isna().any() or (p.index.weekday!=4).any():
        raise ValueError('SPX data must have one entry per Friday')
    series=h15_weekly(h15_zip.read_bytes())
    cpi=_fred_csv(cpi_csv.read_bytes(),'CPIAUCSL')
    # The historical macro research construction first admits a monthly CPI
    # observation at the beginning of the FOLLOWING month. This is an assumed
    # availability scenario, not verification of the actual first release.
    cpi.index=cpi.index+pd.offsets.MonthBegin(1)
    cal=p.index
    def weekly(x):return x.reindex(x.index.union(cal)).sort_index().ffill().reindex(cal)
    prices=pd.DataFrame({'spx':p,'cp':weekly(series['cp'])},index=cal).loc['2010-01-01':]
    macro=pd.DataFrame({'tbond_10y':weekly(series['treasury_10y']),
                        'tbill_3m':weekly(series['treasury_bill_3m']),
                        'cpi':weekly(cpi)},index=cal).loc['2010-01-01':]
    period=pd.date_range('2010-01-01','2026-08-14',freq='W-FRI')
    for name,frame in [('prices',prices),('macro',macro)]:
        missing=frame.reindex(period)
        if missing.isna().any().any():raise ValueError(f'{name} missing historical dates / data')
        if not frame.index.is_unique:raise ValueError(f'{name} duplicate dates')
    out.mkdir(parents=True)
    for name,frame in [('weekly_prices',prices),('macro',macro)]:
        frame.rename_axis('date').to_csv(out/(name+'.csv'),float_format='%.16g')
    inputs={'SPX_weekly':spx_weekly,'Federal_Reserve_H15':h15_zip,'FRED_CPIAUCSL':cpi_csv}
    manifest={'status':'PUBLIC_SOURCE_RETROSPECTIVE_MACRO_NOT_PIT',
              'spx_weeks':len(prices),'cpi_availability':'observation month plus 1 calendar month (model assumption)',
              'sources_sha256':{k:hashlib.sha256(v.read_bytes()).hexdigest() for k,v in inputs.items()},
              'output_sha256':{name:hashlib.sha256((out/(name+'.csv')).read_bytes()).hexdigest() for name in ('weekly_prices','macro')}}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest

if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__)
    for arg in ('spx-weekly','h15-zip','cpi-csv','output-dir'):
        a.add_argument('--'+arg,type=Path,required=True)
    x=a.parse_args()
    print(json.dumps(build(x.spx_weekly,x.h15_zip,x.cpi_csv,x.output_dir),indent=2))
