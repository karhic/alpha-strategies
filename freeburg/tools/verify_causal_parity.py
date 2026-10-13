"""Fail-closed cross-implementation parity: the actual causaltrader classes vs
Freeburg research signal table from identical retrospective inputs.
Synthetic Friday 22:00Z availability is for deterministic model checks ONLY;
it is NOT historical first-publication-vintage proof.
"""
from __future__ import annotations
import argparse,hashlib,json,sys
from datetime import datetime,timedelta,timezone
from pathlib import Path
import pandas as pd
# Use the committed, auditable engine snapshot without a separate private install.
VENDOR=Path(__file__).resolve().parents[1]/"vendor"
if str(VENDOR) not in sys.path:sys.path.insert(0,str(VENDOR))
from freeburg.tools.reproduce_four_from_sources import _csv,_ttm,calculate,SLEEVES
from freeburg.primas.strategy import PrimasStrategy
from freeburg.triple40.strategy import Triple40Strategy
from freeburg.pushen.strategy import PuShenStrategy
from freeburg.competitive.strategy import CompetitiveStrategy
from causaltrader import DataEvent,ReplayEngine,AuditLog,DecisionOnlyPlanner,SimBroker

MAPPING={"spx":("index.sp500.level.1w","SPX"),"cp":("rates.commercial_paper.3m.1w","US"),
         "baa":("rates.moody_baa.1w","US"),"ten":("rates.treasury.10y.1w","US"),
         "bill":("rates.tbill.3m.1w","US"),"cpi":("macro.cpi.1w","US"),
         "ey":("fundamentals.sp500.earnings_yield.1w","SPX"),
         "dy":("fundamentals.sp500.dividend_yield.1w","SPX")}
STRATEGIES={"Primas":PrimasStrategy,"Triple40":Triple40Strategy,
            "PuShen":PuShenStrategy,"Competitive":CompetitiveStrategy}

def frame_inputs(prices,macro,quarterly,baa,*,lag_days=90,baa_availability="month-end"):
    if baa_availability=="month-start":raise ValueError("Unsafe BAA month-start lookahead rejected")
    p=_csv(prices,"date")[["spx","cp"]].astype(float)
    m=_csv(macro,"date")[["tbond_10y","tbill_3m","cpi"]].astype(float)
    q=_csv(quarterly,"quarter_date")
    b=_csv(baa,"observation_date")["BAA"].astype(float).dropna()
    if b.index.to_period('M').duplicated().any():raise ValueError('Duplicate monthly BAA')
    if baa_availability=="month-end":b.index=b.index+pd.offsets.MonthEnd(0)
    elif baa_availability=="next-month":b.index=b.index+pd.offsets.MonthBegin(1)
    else:raise ValueError(baa_availability)
    cal=p.index
    m=m.reindex(m.index.union(cal)).sort_index().ffill().reindex(cal)
    bw=b.reindex(b.index.union(cal)).sort_index().ffill().reindex(cal)
    ep=_ttm(q,'as_reported_eps',cal,lag_days)/p.spx*100
    di=_ttm(q,'dividends_per_share',cal,lag_days)/p.spx*100
    out=pd.DataFrame({'spx':p.spx,'cp':p.cp,'baa':bw,'ten':m.tbond_10y,'bill':m.tbill_3m,
                      'cpi':m.cpi,'ey':ep,'dy':di},index=cal)
    if out.index.has_duplicates or (out.index.weekday!=4).any():raise ValueError('Nonweekly calendar')
    return out.loc["2012-01-06":]

def verify(frame:pd.DataFrame,expected:pd.DataFrame,ledgers:Path):
    ledgers.mkdir(parents=True,exist_ok=False)
    results={}
    for name,cls in STRATEGIES.items():
        events=[]
        for date,row in frame.iterrows():
            f=datetime(date.year,date.month,date.day,21,0,tzinfo=timezone.utc)
            a=f+timedelta(hours=1)
            for key,(ds,inst) in MAPPING.items():
                v=row[key]
                if pd.notna(v):events.append(DataEvent('RETROSPECTIVE_FROZEN_INPUT_NOT_PIT',ds,inst,f,a,float(v)))
            events.append(DataEvent('RESEARCH_DECISION_CLOCK','clock.weekly.freeburg',None,
                         f,a+timedelta(minutes=1),None))
        ledger=ledgers/(name.lower()+'.jsonl')
        audit=ReplayEngine(strategy=cls(),broker=SimBroker(),events=events,
                           audit=AuditLog(ledger),planner=DecisionOnlyPlanner(),
                           config={'PIT_CERTIFIED':False,'purpose':'cross-implementation parity'}).run()
        actions={}
        for r in audit.records:
            if r.kind!='strategy_action':continue
            day=pd.Timestamp(r.timestamp).tz_localize(None).normalize()
            if day in actions:raise ValueError(f'Duplicate {name} action on {day}')
            weight=float(r.payload.weight)
            if weight not in (0.0,1.0):raise ValueError('Nonbinary weight')
            actions[day]=int(weight)
        got=pd.Series(actions,dtype=int).reindex(expected.index)
        bad=got.isna()|(got!=expected[name].astype(int))
        results[name]={'expected':len(expected),'generated':len(got)-int(got.isna().sum()),
                       'mismatches':int(bad.sum()),'first_mismatch':[str(x.date()) for x in got.index[bad][:8]],
                       'ledger_sha256':hashlib.sha256(ledger.read_bytes()).hexdigest()}
    if any(v['mismatches'] for v in results.values()):
        raise ValueError('Causal engine fails parity: '+json.dumps(results))
    return {'parity':'PASS','weeks':len(expected),'decisions':len(expected)*len(SLEEVES),
            'status':'MODEL_INPUT_PARITY_ONLY_NOT_HISTORICAL_PIT','sleeves':results}

def verify_ledger_accounting(ledgers:Path,returns:pd.DataFrame,frame:pd.DataFrame,*, tolerance=1e-12):
    """Independent account bridge from emitted causal-engine decisions to research P&L.

    This asserts historical Friday-close research parity ONLY. Executable
    post-close entries require independent next-session prices, not supplied.
    """
    cash_factors={"Primas":1.0,"Triple40":.9,"PuShen":1.0,"Competitive":.9}
    modelled={}
    delayed={}
    for name in SLEEVES:
        actions={}
        for line in (ledgers/(name.lower()+'.jsonl')).read_text().splitlines():
            r=json.loads(line)
            if r.get('kind')!='strategy_action':continue
            date=pd.Timestamp(r['timestamp']).tz_localize(None).normalize()
            if date in actions:raise AssertionError('Duplicate ledger decision')
            v=float(r['payload']['weight'])
            if v not in (0.,1.):raise AssertionError('Nonbinary causal ledger weight')
            actions[date]=v
        sig=pd.Series(actions).reindex(returns.index)
        if sig.isna().any():raise AssertionError('Missing ledger action')
        cash=frame.cp.reindex(returns.index).clip(lower=0)*cash_factors[name]/5200.
        out=returns.stock*sig+cash*(1-sig)
        maxerr=float((out-returns[name]).abs().max())
        if maxerr>tolerance:raise AssertionError(f'Ledger return does not match published research return: {name}: {maxerr}')
        modelled[name]=out
        delayed[name]=returns.stock*sig.shift(1)+cash*(1-sig.shift(1))
    original=pd.DataFrame(modelled).mean(axis=1)
    lag=pd.DataFrame(delayed).mean(axis=1).iloc[1:]
    from freeburg.tools.reproduce_four_from_sources import _metrics
    return {'ledger_research_accounting':'PASS','max_abs_composite_error':float((original-returns[list(SLEEVES)].mean(axis=1)).abs().max()),
            'research_friday_close_metrics':_metrics(original),
            'one_full_week_signal_delay_stress':_metrics(lag),
            'warning':'Neither series is certified PIT, fillable next-session execution, or net of costs.'}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for v in ('weekly-prices','macro','quarterly','baa-monthly','agg','output-dir'):
        ap.add_argument('--'+v,required=True,type=Path)
    ap.add_argument('--lag-days',type=int,default=90)
    ap.add_argument('--baa-availability',choices=['month-end','next-month'],default='month-end')
    a=ap.parse_args()
    if a.output_dir.exists():raise FileExistsError(a.output_dir)
    ret,expected,meta=calculate(a.weekly_prices,a.macro,a.quarterly,a.baa_monthly,a.agg,
                  lag_days=a.lag_days,baa_availability=a.baa_availability)
    frame=frame_inputs(a.weekly_prices,a.macro,a.quarterly,a.baa_monthly,
                       lag_days=a.lag_days,baa_availability=a.baa_availability)
    report=verify(frame,expected,a.output_dir/'ledgers')
    report["accounting"]=verify_ledger_accounting(a.output_dir/'ledgers',ret,frame)
    report['source_inputs_sha256']={n:hashlib.sha256(getattr(a,n).read_bytes()).hexdigest()
                 for n in ('weekly_prices','macro','quarterly','baa_monthly','agg')}
    (a.output_dir/'parity_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
