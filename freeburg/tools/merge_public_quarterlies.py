"""Build historical quarterly inputs from public S&P archive + current live sources.

Up to and including the latest downloaded S&P archived quarter use exactly
archived first-observed figures. For newer quarters, use the live research
pipeline: AlphaQuery EPS and S&P PR/TR index dividend-points identity.
This is public-source numerical reproduction, NOT source-vintage PIT proof.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
import pandas as pd

START='1988-03-31'
END='2025-09-30'

def merge(archive:Path,eps:Path,div:Path,output:Path,*,overlap_eps_tol=0.011,overlap_div_tol=0.10):
    if output.exists():raise FileExistsError(output)
    a=pd.read_csv(archive,parse_dates=['quarter_date']).set_index('quarter_date').sort_index()
    e=pd.read_csv(eps,parse_dates=['quarter_date']).set_index('quarter_date').sort_index()
    d=pd.read_csv(div,parse_dates=['quarter_date']).set_index('quarter_date').sort_index()
    for label,frame in (('archived S&P',a),('secondary EPS',e),('PR/TR dividends',d)):
        if frame.index.isna().any() or frame.index.has_duplicates:raise ValueError('Duplicate/missing quarter dates: '+label)
    historical=a[['as_reported_eps','dividends_per_share']].loc[START:END].copy()
    if historical.empty:raise ValueError('Missing archived S&P history')
    cutoff=historical.index.max()
    if cutoff<pd.Timestamp('2022-06-30') or cutoff>=pd.Timestamp(END):
        # The current path explicitly cross-validates the published 17-archive
        # overlap; do not silently switch to future archive coverage.
        raise ValueError('Unexpected official archive cutoff; review provenance and rerun')
    required=pd.date_range(START,END,freq='QE-DEC')
    verified=required[required<=cutoff]
    if historical.reindex(verified).isna().any().any():raise ValueError('Gaps in historical official S&P quarters')
    # Validate provider equality against authenticated archived overlap.
    # Avoid checking pre-2014 data when current EPS service has no coverage.
    joined=historical.join(e[['as_reported_eps']].rename(columns={'as_reported_eps':'eps_secondary'}),how='left')
    joined=joined.join(d[['dividends_per_share']].rename(columns={'dividends_per_share':'div_index_derived'}),how='left')
    epserr=(joined.as_reported_eps-joined.eps_secondary).abs().dropna()
    diverr=(joined.dividends_per_share-joined.div_index_derived).abs().dropna()
    if len(epserr)<20 or len(diverr)<30:raise ValueError('Insufficient official overlap to validate secondary data')
    if epserr.max()>overlap_eps_tol:raise ValueError('Secondary EPS disagrees with official archived history')
    if diverr.max()>overlap_div_tol:raise ValueError('Index-derived dividends disagree with official archived history')
    late=required[required>cutoff]
    if len(late)<1:raise ValueError('No quarters requiring public secondary fallback')
    second=e.reindex(late)['as_reported_eps']; dividends=d.reindex(late)['dividends_per_share']
    if second.isna().any() or dividends.isna().any():raise ValueError('Public-secondary fallback missing required late quarter')
    if (second<=-500).any() or (dividends<0).any():raise ValueError('Invalid quarterly values')
    fallback=pd.DataFrame({'as_reported_eps':second,'dividends_per_share':dividends},index=late)
    combined=pd.concat([historical.reindex(verified),fallback]).sort_index().rename_axis('quarter_date')
    if not combined.index.equals(required):raise ValueError('Incomplete/unexpected output calendar')
    combined.to_csv(output)
    record={'schema':'freeburg.public-quarterly-rebuild.v1','classification':'RETROSPECTIVE_COMPUTATIONAL_RECONSTRUCTION_NOT_PIT',
       'archived_s_and_p_quarters':len(verified),'last_archived_quarter':cutoff.strftime('%Y-%m-%d'),
       'secondary_source_quarters':len(late),'first_secondary_quarter':late[0].strftime('%Y-%m-%d'),
       'last_quarter':late[-1].strftime('%Y-%m-%d'),
       'eps_provider':'AlphaQuery S&P 500 actual EPS HTML (same as forward monitor)',
       'dividend_provider':'S&P price/total-return index closes via Yahoo (same as forward monitor)',
       'official_overlap':{'EPS_n':int(len(epserr)),'max_abs_EPS':float(epserr.max()),
          'dividend_n':int(len(diverr)),'max_abs_dividend_points':float(diverr.max())},
       'inputs_sha256':{n:hashlib.sha256(f.read_bytes()).hexdigest() for n,f in [('official_archive',archive),('secondary_eps',eps),('derived_dividends',div)]},
       'quarterly_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
       'warning':'Sources downloaded today can contain retrospective revisions. 90-day modeling lag does not certify true first-release timing.'}
    (output.parent/(output.stem+'.manifest.json')).write_text(json.dumps(record,indent=2)+'\n')
    return record

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--official-archive',required=True,type=Path)
    p.add_argument('--secondary-eps',required=True,type=Path)
    p.add_argument('--index-dividends',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args()
    print(json.dumps(merge(a.official_archive,a.secondary_eps,a.index_dividends,a.output),indent=2))
if __name__=='__main__':main()
