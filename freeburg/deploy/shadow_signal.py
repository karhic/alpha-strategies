"""As-of current four-sleeve *shadow* decisions from captured source files.

Uses the same numeric strategy predicates as the released causal strategy
classes. Does not backdate source revisions or authorize order entry.
"""
from __future__ import annotations
import argparse,json
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import pandas as pd
from freeburg.deploy.capture_live import h15_weekly,_fred_csv,_spx_close
from freeburg.deploy.capture_eps import parse as parse_eps
from freeburg.deploy.capture_dividends import calculate as dividend_calculate

def calculate(root:Path)->dict:
    market=root/"market"; eps=root/"eps"; div=root/"dividends"
    m=json.loads((market/"manifest.json").read_text())
    if not m["market_sources_ready"]:raise ValueError("Stale market input")
    captured=datetime.fromisoformat(m["captured_at_utc"])
    e=json.loads((eps/"manifest.json").read_text())
    v=json.loads((div/"manifest.json").read_text())
    if abs((datetime.fromisoformat(e["capture_utc"])-captured).total_seconds())>3600:
        raise ValueError("EPS captured at different time")
    if abs((datetime.fromisoformat(v["acquired_at_utc"])-captured).total_seconds())>3600:
        raise ValueError("Dividends captured at different time")
    spx=_spx_close((market/"spx.json").read_bytes()).resample("W-FRI").last().dropna()
    rates=h15_weekly((market/"fed_h15.zip").read_bytes())
    cp=rates["cp"].reindex(rates["cp"].index.union(spx.index)).sort_index().ffill().reindex(spx.index)
    b=_fred_csv((market/"BAA.csv").read_bytes(),"BAA")
    # Monthly yield can be safely taken from capture time for current decision,
    # but its retrospective history may contain revisions. Availability audit
    # covers only current capture, not historical series.
    b.index=b.index+pd.offsets.MonthEnd(0)
    bw=b.reindex(b.index.union(spx.index)).sort_index().ffill().reindex(spx.index)
    eps_q=parse_eps((eps/"source.html").read_bytes()).set_index("quarter_date")["as_reported_eps"]
    p_raw=_spx_close((div/"price.json").read_bytes())
    tr_raw=_spx_close((div/"total_return.json").read_bytes())
    _,quarterly=dividend_calculate(p_raw,tr_raw,now=captured)
    dq=quarterly["dividends_per_share"]
    # The current capture establishes the latest values were obtainable now,
    # not that historical vendor dates were initial publication timestamps.
    et=eps_q.rolling(4).sum().dropna()
    dt=dq.rolling(4).sum().dropna()
    week=spx.index[spx.index<=pd.Timestamp(m["target_completed_friday"])]
    if not len(week):raise ValueError("No completed Friday")
    qeps=et.reindex(et.index.union(week)).sort_index().ffill().reindex(week)
    qdiv=dt.reindex(dt.index.union(week)).sort_index().ffill().reindex(week)
    cpi=_fred_csv((market/"CPIAUCSL.csv").read_bytes(),"CPIAUCSL")
    ci=cpi.reindex(cpi.index.union(week)).sort_index().ffill().reindex(week)
    tb=rates["treasury_bill_3m"].reindex(rates["treasury_bill_3m"].index.union(week)).sort_index().ffill().reindex(week)
    ten=rates["treasury_10y"].reindex(rates["treasury_10y"].index.union(week)).sort_index().ffill().reindex(week)
    t=week[-1];s=spx.loc[week]
    if len(week)<80 or pd.isna(qeps.loc[t]) or pd.isna(qdiv.loc[t]):raise ValueError("Insufficient history")
    ey=qeps/s*100;dy=qdiv/s*100
    spread=ey-cp.loc[week]
    checks={
      "primas":bool((s.iloc[-1]>s.iloc[-52:].mean()) and (cp.loc[week].iloc[-1]<cp.loc[week].iloc[-52:].mean())),
      "triple40":bool((s.iloc[-1]>s.iloc[-40:].mean()) and
                       ((bw.loc[week].iloc[-1]<bw.loc[week].iloc[-40:].mean()) or
                        (cp.loc[week].iloc[-1]<cp.loc[week].iloc[-40:].mean()))),
      "pushen":bool(spread.iloc[-1]>spread.iloc[-51] and s.iloc[-1]>s.iloc[-51]),
      "competitive":bool(sum([
          ten.iloc[-1]<ten.iloc[-25],
          tb.iloc[-1]<tb.iloc[-25],
          dy.iloc[-1]<dy.iloc[-25],
          ci.iloc[-1]<ci.iloc[-25]])>=2)
    }
    return {
      "schema":"freeburg.four.weekly-shadow.v1",
      "decision_friday":t.date().isoformat(),
      "captured_at":captured.isoformat(),
      "states":{k:int(v) for k,v in checks.items()},
      "spy_target_weight":sum(checks.values())/4,
      "risk_class":"SHADOW_ONLY_NO_ORDER_SUBMISSION",
      "methodology":"Current-source numeric strategy predicates; full causal-engine signal parity is NOT yet certified",
      "historical_revision_caveat":"Historical lookbacks can include retrospective revisions. Not a PIT backtest.",
      "execution_enabled":False
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--snapshot",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    result=calculate(a.snapshot)
    if a.output.exists():raise FileExistsError(a.output)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
