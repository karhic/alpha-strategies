"""Bound fundamentals timing without optimizing the selected lag on OOS returns.

Reconstructs unchanged weekly Pu Shen / Competitive decisions under fixed
quarter-end lags and independently archived first-capture-as-of timing.
All lagged variants use the SAME retrospective archived quarterly values,
so none of those scenarios certify vintage correctness.
"""
import argparse, json, math
from pathlib import Path
import numpy as np
import pandas as pd

NAMES={'Primas':'primas','Triple40':'triple40','PuShen':'pushen','Competitive':'competitive'}
EVENTS={'pushen':{
    'price':'index.sp500.level.1w','cp':'rates.commercial_paper.3m.1w'},
    'competitive':{
        'bond':'rates.treasury.10y.1w','bill':'rates.tbill.3m.1w',
        'cpi':'macro.cpi.1w'}
}

def events(path,keys):
    m={}
    for l in path.open():
        r=json.loads(l)
        if r['dataset'] not in keys.values():continue
        dt=pd.Timestamp(r['event_time'][:10])
        m.setdefault(dt,{})[[k for k,v in keys.items() if v==r['dataset']][0]]=float(r['payload'])
    return pd.DataFrame.from_dict(m,orient='index').sort_index()

def ttm_events(q,column,kind,lag_days=None):
    rows=[]
    capture='eps_capture_timestamp' if kind=='eps' else 'div_capture_timestamp'
    for dt in q.index:
        dates=pd.date_range(end=dt,periods=4,freq='QE-DEC')
        if not set(dates).issubset(q.index):continue
        vals=pd.to_numeric(q.loc[dates,column],errors='coerce')
        if vals.isna().any():continue
        if lag_days is None:
            # Can't claim a TTM containing observations never captured at the time.
            captures=pd.to_datetime(q.loc[dates,capture],errors='coerce')
            if captures.isna().any():continue
            at=captures.max()
        else:at=dt+pd.Timedelta(days=lag_days)
        rows.append((at,dt,float(vals.sum())))
    return pd.DataFrame(rows,columns=['available','period','value'])

def series_asof(observations,week_index):
    # For weekly decisions, use only data actually available before the
    # assumed 20:00 UTC Friday decision cutoff. A Friday 22:00 Wayback capture
    # is unavailable until the following decision.
    e=observations.sort_values(['available','period']).drop_duplicates('available',keep='last')
    left=pd.DataFrame({'cutoff':week_index+pd.Timedelta(hours=20)}).sort_values('cutoff')
    right=e.rename(columns={'available':'cutoff'}).sort_values('cutoff')
    out=pd.merge_asof(left,right,on='cutoff',direction='backward')
    return pd.Series(out.value.to_numpy(dtype=float),index=week_index),pd.Series(out.period.to_numpy(),index=week_index)

def perf(r):
    a=r.to_numpy(float);eq=np.r_[1,np.cumprod(1+a)]
    return {'cagr':float(eq[-1]**(52/len(a))-1),'max_dd':float((eq/np.maximum.accumulate(eq)-1).min()),
            'wealth':float(eq[-1]),'sharpe_raw':float(a.mean()/a.std(ddof=1)*52**.5)}

def analyse(weekly,quarterly,pu_events,comp_events,
            baa_monthend_ledger,cp_weekly):
    wk=pd.read_csv(weekly,parse_dates=['date']).set_index('date').sort_index()
    index=wk.index
    q=pd.read_csv(quarterly,parse_dates=['quarter_date','eps_capture_timestamp','div_capture_timestamp'])
    q=q.drop_duplicates('quarter_date',keep='last').sort_values('quarter_date').set_index('quarter_date')
    p=events(pu_events,EVENTS['pushen'])
    c=events(comp_events,EVENTS['competitive'])
    if len(p)<1000 or len(c)<1000:raise ValueError('Insufficient historical rolling context')
    common=p.index.intersection(c.index)
    p=p.reindex(common);c=c.reindex(common)
    if not index.isin(common).all():raise ValueError('Sample index is missing replay input observations')
    # competitive needs same underlying weekly S&P index as Pu Shen;
    # report only as same-source model timing sensitivity.
    spx=p.price
    # zero dividend / EPS data fill not allowed for sample
    def get_signal(lag):
        eps,_=series_asof(ttm_events(q,'as_reported_eps','eps',lag),common)
        div,_=series_asof(ttm_events(q,'dividends_per_share','div',lag),common)
        ey=eps/spx*100.;dy=div/spx*100.
        spread=ey-p.cp
        pu=(spread>spread.shift(50))&(spx>spx.shift(50))
        comp=((c.bond<c.bond.shift(24)).astype(int)+(c.bill<c.bill.shift(24)).astype(int)
              +(dy<dy.shift(24)).astype(int)+(c.cpi<c.cpi.shift(24)).astype(int))>=2
        # Require component observations and lagged ones, rather than implicitly
        # treating absence as a false comparison.
        pu=pu.where(spread.notna()&spread.shift(50).notna()&spx.shift(50).notna())
        comp=comp.where(dy.notna()&dy.shift(24).notna()&c.bond.notna()&c.bond.shift(24).notna()
                       &c.bill.notna()&c.bill.shift(24).notna()&c.cpi.notna()&c.cpi.shift(24).notna())
        return pu.reindex(index),comp.reindex(index),eps.reindex(index),div.reindex(index)
    def actions(path):
        out={}
        for line in path.open():
            row=json.loads(line)
            if row['kind']=='strategy_action':
                dt=pd.Timestamp(row['timestamp']).tz_localize(None).normalize()
                out[dt]=int(float(row['payload']['weight'])>.5)
        return pd.Series(out).reindex(index)
    tri=actions(baa_monthend_ledger)
    if tri.isna().any():raise ValueError('Missing Triple-40 ledger actions')
    original_cp=pd.read_csv(cp_weekly,parse_dates=['date']).set_index('date')['cp'].reindex(index)
    cash_cp=original_cp.clip(lower=0)/5200.
    # The original research's two cash conventions are retained for each sleeve.
    # Pu/Competitive cash series decompose to actual original CP cash per research.
    results=[]
    reference_pu=(wk.PuShen-wk.stock).abs() < (wk.PuShen-cash_cp).abs()
    reference_comp=(wk.Competitive-wk.stock).abs() < (wk.Competitive-cash_cp*.9).abs()
    reference_t=(wk.Triple40-wk.stock).abs() < (wk.Triple40-cash_cp*.9).abs()
    if len(index)!=658:raise ValueError('Expected 658-week comparison sample')
    for label,lag in [('30d',30),('45d',45),('60d',60),('75d',75),('90d',90),
                      ('105d',105),('120d',120),('150d',150),('180d',180),
                      ('wayback_capture_asof',None)]:
        pu,co,eps,div=get_signal(lag)
        complete=not (pu.isna().any() or co.isna().any())
        if not complete:
            results.append({'timing':label,'available':False,'missing_pu':int(pu.isna().sum()),
                            'missing_comp':int(co.isna().sum())})
            continue
        pr=(pu.astype(float)*wk.stock+(1-pu.astype(float))*cash_cp)
        cr=(co.astype(float)*wk.stock+(1-co.astype(float))*cash_cp*.9)
        triple_ret=tri*wk.stock+(1-tri)*cash_cp*.9
        composite=(wk.Primas+triple_ret+pr+cr)/4.
        # Research original model comparisons for fixed-90d only
        result={'timing':label,'available':True,
                'pu_research_diffs':int((pu.astype(bool)!=reference_pu).sum()),
                'comp_research_diffs':int((co.astype(bool)!=reference_comp).sum()),
                'pu_risk_on':float(pu.mean()),'comp_risk_on':float(co.mean()),
                'baa_monthend_risk_on':float(tri.mean()),
                'quarterly_asof_not_vintage_certified':lag is not None,
                **perf(composite)}
        if label=='90d' and (result['pu_research_diffs'] or result['comp_research_diffs']):
            raise AssertionError(f'90d research baseline does not match original: {result}')
        results.append(result)
    # Crucial archive evidence: first capture date is not original release date,
    # but supplies a provable 'available no later than' bound for those values.
    q2=q.loc[(q.index>=pd.Timestamp('2013-01-01'))&(q.index<=pd.Timestamp('2025-09-30'))]
    capture={
        kind:{
            'quarters':len(q2),
            'min_capture_delay_days':int(((q2[col]-q2.index).dt.days).min()),
            'median_capture_delay_days':float(((q2[col]-q2.index).dt.days).median()),
            'pct_exact_values_captured_by_day90':float((((q2[col]-q2.index).dt.days)<=90).mean()),
            'pct_exact_values_captured_by_day120':float((((q2[col]-q2.index).dt.days)<=120).mean()),
            'pct_exact_values_captured_by_day180':float((((q2[col]-q2.index).dt.days)<=180).mean())}
        for kind,col in [('eps','eps_capture_timestamp'),('dividend','div_capture_timestamp')]}
    return {'source':'1970_2026_frozen_weekly_replay_inputs_and_retrospectively_archived_sp500_quarterlies',
            'fixed_Baa_scenario':'monthly_BAA_month_end_not_certified_release',
            'sample':{'from':str(index[0].date()),'to':str(index[-1].date()),'weeks':len(index)},
            'capture_coverage':capture,'scenarios':results,
            'disclaimer':'Retrospective quarterly values at a fixed lag do NOT prove those exact values were published then; archive capture dates give latest-known, not earliest actual, availability.'}

def main():
    pa=argparse.ArgumentParser()
    for n in ['weekly','quarterly','pu-events','comp-events','triple-monthend-ledger','cp-weekly','output']:
        pa.add_argument('--'+n,required=True,type=Path)
    a=pa.parse_args()
    if a.output.exists():raise FileExistsError(a.output)
    result=analyse(a.weekly,a.quarterly,a.pu_events,a.comp_events,a.triple_monthend_ledger,a.cp_weekly)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
