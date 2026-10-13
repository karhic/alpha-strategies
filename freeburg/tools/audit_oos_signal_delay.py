"""Audit weekly OOS model return decomposition and one-decision-week delay.

Inputs are the original scratchpad's weekly per-sleeve model return table
and independently fetched Fed commercial-paper yields. This is an accounting
and signal-timing stress test, NOT a certified source-vintage PIT replay.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
SLEEVES=("Primas","Triple40","PuShen","Competitive")
CASH_FACTORS={"Primas":1.0,"Triple40":0.9,"PuShen":1.0,"Competitive":0.9}

def analyze(returns:pd.DataFrame,cp_annual_percent:pd.Series,tolerance:float=1e-8)->dict:
    x=returns.copy()
    if "date" in x.columns:x=x.set_index("date")
    x.index=pd.to_datetime(x.index)
    x=x.sort_index()
    cp=cp_annual_percent.reindex(x.index)
    if x.index.has_duplicates or x[list(SLEEVES)+["stock"]].isna().any().any() or cp.isna().any():
        raise ValueError("Duplicate index or missing model inputs / commercial-paper yields")
    if len(x)<3:raise ValueError("Short sample")
    reconstructed={};shifted={};exposures={};max_residuals={}
    for sleeve in SLEEVES:
        cash=cp.clip(lower=0)*CASH_FACTORS[sleeve]/5200.
        diff_on=(x[sleeve]-x["stock"]).abs()
        diff_off=(x[sleeve]-cash).abs()
        gap=np.minimum(diff_on,diff_off)
        max_residuals[sleeve]=float(gap.max())
        if gap.max()>tolerance:
            raise ValueError(f"{sleeve} cannot be independently decomposed into stock versus CP cash; max residual={gap.max()}")
        # 0 is risk-off; 1 is risk-on. No heuristic thresholds: exact model branches.
        signal=(diff_on<diff_off).astype(int)
        recon=x["stock"]*signal+cash*(1-signal)
        if not np.allclose(recon,x[sleeve],atol=tolerance,rtol=0):
            raise AssertionError("Branch reconstruction failed")
        reconstructed[sleeve]=recon
        shifted[sleeve]=x["stock"]*signal.shift(1)+cash*(1-signal.shift(1))
        exposures[sleeve]=float(signal.mean())
    equal=pd.DataFrame(reconstructed,index=x.index).mean(axis=1)
    delayed=pd.DataFrame(shifted,index=x.index).mean(axis=1).iloc[1:]
    original=equal.iloc[1:]
    def perf(r:pd.Series)->dict:
        a=r.to_numpy(float)
        e=np.r_[1.0,np.cumprod(1+a)]
        drawdown=e/np.maximum.accumulate(e)-1
        return {"weeks":len(a),"cagr":float(e[-1]**(52/len(a))-1),
                "max_dd":float(drawdown.min()),
                "terminal_wealth":float(e[-1]),
                "raw_sharpe":float(a.mean()/a.std(ddof=1)*np.sqrt(52))}
    return {"source_classification":"OOS_MODEL_BRANCH_INVERSION_NOT_INDEPENDENT_STRATEGY_PIT",
            "all_sleeves_cash_equity_decomposition_max_abs_error":max_residuals,
            "risk_on_exposures":exposures,
            "original_658_weeks":perf(equal),
            "aligned_original_657_weeks":perf(original),
            "one_week_delayed_657_weeks":perf(delayed),
            "comparison_start":original.index[0].date().isoformat(),
            "comparison_end":original.index[-1].date().isoformat(),
            "note":"The delayed test holds last week's signal for this week's close-to-next-close return. It intentionally changes trades and represents a full-week latency stress, NOT next-open executable timing."}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--weekly-returns",type=Path,required=True)
    p.add_argument("--cp-weekly",type=Path,required=True,help="CSV with date, cp (annual %)")
    p.add_argument("--output",type=Path)
    a=p.parse_args()
    x=pd.read_csv(a.weekly_returns,parse_dates=["date"]).set_index("date")
    cp=pd.read_csv(a.cp_weekly,parse_dates=["date"]).set_index("date")["cp"]
    result=analyze(x,cp)
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True)
        if a.output.exists():raise FileExistsError(a.output)
        a.output.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
