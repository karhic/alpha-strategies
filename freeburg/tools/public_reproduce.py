"""Public download -> audited four-sleeve historical calculation.

Run inside the default Freeburg container using a separate, explicit invocation.
Publicly accessible sources may be rate-limited/unavailable; failures are fatal.
Never use results as certified point-in-time trades.
"""
from __future__ import annotations
import argparse,hashlib,json
from datetime import datetime,timezone
from pathlib import Path
from freeburg.tools.download_sp500_quarterly_wayback import harvest
from freeburg.deploy.capture_eps import capture as capture_eps
from freeburg.deploy.capture_dividends import acquire as capture_dividends
from freeburg.deploy.capture_live import _download as fetch_market, FRED
from freeburg.tools.download_spx import download as download_spx
from freeburg.tools.download_four_market_extras import fetch as market_extras
from freeburg.tools.merge_public_quarterlies import merge
from freeburg.tools.build_public_weekly_inputs import build
from freeburg.tools.reproduce_four_from_sources import calculate,report
from freeburg.tools.verify_causal_parity import frame_inputs,verify,verify_ledger_accounting


def run(root:Path,*,wayback_cache:Path|None=None):
    if root.exists() and any(root.iterdir()):raise FileExistsError('Choose an empty reproducibility destination')
    root.mkdir(parents=True,exist_ok=True)
    audit={'status':'INCOMPLETE','mode':'PUBLIC_SOURCE_RESEARCH_REBUILD_NOT_PIT',
           'started_utc':datetime.now(timezone.utc).isoformat(),'stages':{}}
    try:
        def stage(name,fn):
            print('STAGE',name,flush=True)
            result=fn()
            audit['stages'][name]='PASS'
            (root/'progress.json').write_text(json.dumps(audit,indent=2)+'\n')
            return result
        archive=stage('official_archived_s_and_p',lambda:harvest(Path('freeburg/sources/sp500_wayback_captures.json'),root/'wayback',workers=3,cache=wayback_cache))
        stage('current_source_eps',lambda:capture_eps(root/'eps',datetime.now(timezone.utc)))
        stage('index_calculated_dividends',lambda:capture_dividends(root/'dividends',now=datetime.now(timezone.utc)))
        stage('full_spx_history',lambda:download_spx(root/'spx'))
        from freeburg.deploy.capture_live import H15
        def official():
            dest=root/'h15';dest.mkdir()
            (dest/'fed_h15.zip').write_bytes(fetch_market(H15,timeout=120))
            (dest/'CPIAUCSL.csv').write_bytes(fetch_market(FRED['CPIAUCSL'],timeout=75))
        stage('official_rates_and_cpi',official)
        stage('baa_and_bond_benchmark',lambda:market_extras(root/'market'))
        quarter=root/'combined_quarters.csv'
        stage('overlap_verified_quarterly_merge',lambda:merge(root/'wayback/quarterly_first_observed_actual.csv',root/'eps/eps.csv',root/'dividends/quarterly_dividends.csv',quarter))
        stage('public_weekly_inputs',lambda:build(root/'spx/spx_weekly.csv',root/'h15/fed_h15.zip',root/'h15/CPIAUCSL.csv',root/'weekly'))
        p=root/'weekly/weekly_prices.csv';m=root/'weekly/macro.csv';b=root/'market/fred_baa_monthly.csv';g=root/'market/agg_weekly_forward.csv'
        def models():
            returns,signals,meta=calculate(p,m,quarter,b,g)
            meta['source_mode']='PUBLIC_DOWNLOADED_FALLBACK_NOT_PIT_CERTIFIED'
            meta['inputs_sha256']={key:hashlib.sha256(path.read_bytes()).hexdigest() for key,path in [('prices',p),('macro',m),('quarterly',quarter),('baa',b),('agg',g)]}
            report(returns,signals,meta,root/'backtest')
            return returns,signals,meta
        returns,signals,meta=stage('four_sleeve_research_model',models)
        def parity():
            frame=frame_inputs(p,m,quarter,b)
            verification=verify(frame,signals,root/'engine_ledgers')
            verification['accounting']=verify_ledger_accounting(root/'engine_ledgers',returns,frame)
            (root/'parity.json').write_text(json.dumps(verification,indent=2)+'\n')
        stage('actual_causal_engine_decisions_and_accounting',parity)
        audit['status']='PASS'
        audit['headline']={'cagr':meta['composite']['cagr'],'max_drawdown':meta['composite']['max_dd'],
                           'decision_count':len(signals)*4}
        return audit
    except Exception as exc:
        audit['status']='FAILED';audit['error']=type(exc).__name__+': '+str(exc)[:800]
        raise
    finally:
        (root/'progress.json').write_text(json.dumps(audit,indent=2)+'\n')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir',type=Path,default=Path('/data/historical/public-rebuild'))
    p.add_argument('--wayback-cache',type=Path,default=None)
    a=p.parse_args()
    print(json.dumps(run(a.output_dir,wayback_cache=a.wayback_cache),indent=2))
if __name__=='__main__':main()
