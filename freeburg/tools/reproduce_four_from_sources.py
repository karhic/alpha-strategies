"""Reproduce the four-sleeve 2014–2026 OOS portfolio from explicit inputs.

No private scratchpad Python dependency. No invisible network requests.
Explicitly supply acquired market snapshots and archived S&P quarterlies.
Default month-end Baa is a *timing scenario*, not certified PIT. The optional
original month-start Baa scenario is intentionally marked as lookahead.

Source columns:
--weekly-prices: date,spx,cp ; weekly Friday closes and annual CP percent.
--macro: date,tbond_10y,tbill_3m,cpi (frozen or independent as disclosed).
--quarterly: quarter_date,as_reported_eps,dividends_per_share (S&P archive).
--baa-monthly: observation_date,BAA (FRED monthly)
--agg: date,agg (decision-Friday stamped next-week total return).
"""
from __future__ import annotations
import argparse,hashlib,json,math
from pathlib import Path
import numpy as np
import pandas as pd

SLEEVES=("Primas","Triple40","PuShen","Competitive")
BEGIN="2014-01-03"
END="2026-08-07"
def _csv(path, index_col):
    df=pd.read_csv(path,parse_dates=[index_col]).set_index(index_col).sort_index()
    if df.index.has_duplicates:raise ValueError(f"Duplicate dates in {path}")
    return df

def _ttm(q,kind,cal,lag):
    if not {"as_reported_eps","dividends_per_share"}.issubset(q.columns):
        raise ValueError("Archived S&P quarterly EPS and dividends both required")
    rows=[]
    for dt in q.index:
        indices=pd.date_range(end=dt,periods=4,freq="QE-DEC")
        if not set(indices).issubset(q.index):continue
        values=pd.to_numeric(q.loc[indices,kind],errors="coerce")
        if values.isna().any():continue
        rows.append((dt+pd.Timedelta(days=lag),float(values.sum())))
    if len(rows)<50:raise ValueError("Too few complete quarterly TTM observations")
    s=pd.Series({k:v for k,v in rows},dtype=float).sort_index()
    return s.reindex(s.index.union(cal)).sort_index().ffill().reindex(cal)

def _metrics(s):
    x=s.to_numpy(float)
    if not np.isfinite(x).all() or len(x)<2:raise ValueError("Incomplete weekly returns")
    e=np.r_[1,np.cumprod(1+x)]
    dd=(e/np.maximum.accumulate(e)-1).min()
    return {"weeks":len(s),"cagr":float(e[-1]**(52/len(x))-1),
            "max_dd":float(dd),"terminal_wealth":float(e[-1]),
            "sharpe_raw":float(x.mean()/x.std(ddof=1)*math.sqrt(52))}

def calculate(prices,macro,quarterly,baa,agg, *,
              lag_days=90,baa_availability="month-end",start=BEGIN,end=END):
    if lag_days<0:raise ValueError("Negative quarterly lag")
    if baa_availability not in ("month-end","month-start","next-month"):
        raise ValueError(baa_availability)
    p=_csv(prices,"date")[["spx","cp"]].astype(float)
    m=_csv(macro,"date")[["tbond_10y","tbill_3m","cpi"]].astype(float)
    q=_csv(quarterly,"quarter_date")
    required=pd.date_range("1988-03-31","2025-09-30",freq="QE-DEC")
    got=q.reindex(required)
    missing=got[["as_reported_eps","dividends_per_share"]].isna().any(axis=1)
    if missing.any():
        raise ValueError(f"Incomplete S&P quarterly archive: {int(missing.sum())} "
                         "quarter(s) missing EPS or dividends before 2025 Q3")
    b=_csv(baa,"observation_date")["BAA"].astype(float).dropna()
    ab=_csv(agg,"date")["agg"].astype(float)
    # Missing prices or macro may not be interpreted as negative signals.
    cal=p.index
    if not (cal.weekday==4).all():raise ValueError("Price source needs Friday-stamped weekly observations")
    if not cal.isin(m.index).all():
        # A macro observation can be known from earlier week; this does not
        # establish release timing for the actual macro value.
        m=m.reindex(m.index.union(cal)).sort_index().ffill().reindex(cal)
    else:m=m.reindex(cal)
    if baa_availability=="month-end":
        b.index=b.index+pd.offsets.MonthEnd(0)
    elif baa_availability=="next-month":
        b.index=b.index+pd.offsets.MonthBegin(1)
    baa_w=b.reindex(b.index.union(cal)).sort_index().ffill().reindex(cal)
    eps=_ttm(q,"as_reported_eps",cal,lag_days)
    dividends=_ttm(q,"dividends_per_share",cal,lag_days)
    dy=dividends/p.spx*100
    ey=eps/p.spx*100
    s=pd.DataFrame(index=cal)
    p52=p.spx.rolling(52).mean()
    c52=p.cp.rolling(52).mean()
    s["Primas"]=(p.spx>p52)&(p.cp<c52)
    stock40=p.spx>p.spx.rolling(40).mean()
    cp40=p.cp<p.cp.rolling(40).mean()
    baa40=baa_w<baa_w.rolling(40).mean()
    s["Triple40"]=stock40&(baa40|cp40)
    spread=ey-p.cp
    s["PuShen"]=(spread>spread.shift(50))&(p.spx>p.spx.shift(50))
    predicates=pd.DataFrame({
        "long_treasury":m.tbond_10y<m.tbond_10y.shift(24),
        "treasury_bill":m.tbill_3m<m.tbill_3m.shift(24),
        "dividend_yield":dy<dy.shift(24),
        "cpi":m.cpi<m.cpi.shift(24)})
    s["Competitive"]=predicates.sum(axis=1)>=2
    valid=pd.DataFrame({
        "Primas":p52.notna()&c52.notna(),
        "Triple40":p.spx.rolling(40).mean().notna()&
                    p.cp.rolling(40).mean().notna()&baa_w.rolling(40).mean().notna(),
        "PuShen":spread.notna()&spread.shift(50).notna()&p.spx.shift(50).notna(),
        "Competitive":m.tbond_10y.notna()&m.tbond_10y.shift(24).notna()&
                      m.tbill_3m.notna()&m.tbill_3m.shift(24).notna()&
                      dy.notna()&dy.shift(24).notna()&m.cpi.notna()&m.cpi.shift(24).notna(),
        })
    out_idx=cal[(cal>=pd.Timestamp(start))&(cal<=pd.Timestamp(end))]
    if not out_idx.equals(pd.date_range(start,end,freq="W-FRI")):
        raise ValueError("Missing Friday source dates in requested period")
    missing=~valid.reindex(out_idx).all(axis=1)
    if missing.any():raise ValueError(f"Missing historical signal inputs: {missing[missing].index[:8].tolist()}")
    close_next=p.spx.pct_change().shift(-1)+dy.clip(lower=0)/5200.
    cash=p.cp.clip(lower=0)/5200.
    returns=pd.DataFrame(index=out_idx)
    for name in SLEEVES:
        f=1 if name in ("Primas","PuShen") else .9
        returns[name]=np.where(s.loc[out_idx,name],close_next.loc[out_idx],cash.loc[out_idx]*f)
    returns["stock"]=close_next.reindex(out_idx)
    returns["rf"]=(m.tbill_3m.clip(lower=0)/5200).reindex(out_idx)
    returns["agg"]=ab.reindex(out_idx)
    if returns.isna().any().any():raise ValueError("Incomplete weekly return, including next-week and AGG")
    signals=s.loc[out_idx,SLEEVES].astype(int).copy()
    returns.index.name="date";signals.index.name="date"
    composite=returns[list(SLEEVES)].mean(axis=1)
    benchmark=.6*returns.stock+.4*returns["agg"]
    return returns,signals,{
        "sample_start":str(out_idx.min().date()),"sample_end":str(out_idx.max().date()),
        "sample_weeks":len(out_idx),"model":"simulated research, not independently certified PIT",
        "lag_days":lag_days,"baa_availability":baa_availability,
        "timing_warning":"MONTH_START_BAA_FULL_MONTH_LOOKAHEAD" if baa_availability=="month-start" else
                "Baa availability convention is an assumption, not documented original release timing",
        "earnings_warning":"archive retrospective quarterly values may be revised; fixed-lag does not validate PIT",
        "execution_warning":"Friday close price is used after Friday-stamped signals, not executable next-open accounting",
        "composite":_metrics(composite),
        "sp500":_metrics(returns.stock),
        "60_40":_metrics(benchmark)
    }

def report(returns,signals,meta,outdir):
    from freeburg.tools.render_annual_oos import one_year
    outdir=Path(outdir)
    if outdir.exists() and any(outdir.iterdir()):
        raise FileExistsError("Output directory must be new/empty")
    outdir.mkdir(parents=True,exist_ok=True)
    returns.to_csv(outdir/"weekly_returns.csv")
    signals.to_csv(outdir/"weekly_decisions.csv")
    comps=pd.DataFrame({"Freeburg 4":returns[list(SLEEVES)].mean(axis=1),
                        "S&P 500":returns.stock,
                        "60/40":.6*returns.stock+.4*returns["agg"]})
    rows=[]
    for y,group in comps.groupby(comps.index.year):
        for n in comps:
            rows.append({"year":int(y),"series":n,
                        **one_year(group[n],returns.loc[group.index,"rf"],y==2026)})
    pd.DataFrame(rows).to_csv(outdir/"annual_comparison.csv",index=False)
    raw=outdir/"weekly_returns.csv"
    meta["weekly_returns_sha256"]=hashlib.sha256(raw.read_bytes()).hexdigest()
    (outdir/"run_manifest.json").write_text(json.dumps(meta,indent=2)+"\n")
    return meta

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for opt in ("weekly-prices","macro","quarterly","baa-monthly","agg","output-dir"):
        p.add_argument("--"+opt,required=True,type=Path)
    p.add_argument("--lag-days",type=int,default=90)
    p.add_argument("--baa-availability",choices=["month-end","month-start","next-month"],default="month-end")
    a=p.parse_args()
    r,s,m=calculate(a.weekly_prices,a.macro,a.quarterly,a.baa_monthly,a.agg,
                    lag_days=a.lag_days,baa_availability=a.baa_availability)
    report(r,s,m,a.output_dir)
    print(json.dumps(m,indent=2))
if __name__=="__main__":main()
