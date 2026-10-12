"""Run the actual four causaltrader strategy classes on today's source snapshot.

Historical values are retrospective backfills *captured today*. Treat this
as live shadow initialization, NEVER as proof of historical PIT performance.
"""
from __future__ import annotations
import argparse,importlib,json,sys
from datetime import datetime,timezone,timedelta
from pathlib import Path
import pandas as pd
from freeburg.deploy.capture_live import h15_weekly,_fred_csv,_spx_close
from freeburg.deploy.capture_eps import parse as eps_parse
from freeburg.deploy.capture_dividends import calculate as dividend_calc

DATASETS={"spx":("index.sp500.level.1w","SPX"),
          "cp":("rates.commercial_paper.3m.1w","US"),
          "baa":("rates.moody_baa.1w","US"),
          "ten":("rates.treasury.10y.1w","US"),
          "bill":("rates.tbill.3m.1w","US"),
          "cpi":("macro.cpi.1w","US"),
          "ey":("fundamentals.sp500.earnings_yield.1w","SPX"),
          "dy":("fundamentals.sp500.dividend_yield.1w","SPX")}

def produce(folder:Path,out:Path):
    from causaltrader import DataEvent,AuditLog,DecisionOnlyPlanner,ReplayEngine,SimBroker
    market=folder/"market"
    m=json.loads((market/"manifest.json").read_text())
    if not m["market_sources_ready"]:raise ValueError("Market source freshness failure")
    now=datetime.fromisoformat(m["captured_at_utc"])
    if now.tzinfo is None:raise ValueError("Capture not timezone-aware")
    cutoff=pd.Timestamp(m["target_completed_friday"])
    px=_spx_close((market/"spx.json").read_bytes()).resample("W-FRI").last().dropna()
    px=px.loc[:cutoff]
    if len(px)<100:raise ValueError("Insufficient SPX history")
    dates=px.index
    rate=h15_weekly((market/"fed_h15.zip").read_bytes())
    raw={
      "spx":px,
      "cp":rate["cp"],
      "ten":rate["treasury_10y"],
      "bill":rate["treasury_bill_3m"],
      "baa":_fred_csv((market/"BAA.csv").read_bytes(),"BAA"),
      "cpi":_fred_csv((market/"CPIAUCSL.csv").read_bytes(),"CPIAUCSL")
    }
    # The 90-day delay only initializes the *retrospective* lookback; the
    # latest snapshot itself is actually obtained now. NOT PIT certification.
    earn=eps_parse((folder/"eps/source.html").read_bytes()).set_index("quarter_date")["as_reported_eps"]
    a=_spx_close((folder/"dividends/price.json").read_bytes())
    b=_spx_close((folder/"dividends/total_return.json").read_bytes())
    _,q=dividend_calc(a,b,now=now)
    for key,series in (("ey",earn.rolling(4).sum()),("dy",q.dividends_per_share.rolling(4).sum())):
        series.index=series.index+pd.Timedelta(days=90)
        raw[key]=series
    raw["baa"].index=raw["baa"].index+pd.offsets.MonthEnd(0)
    columns={}
    for key,series in raw.items():
        values=series.reindex(series.index.union(dates)).sort_index().ffill().reindex(dates)
        if key in ("ey","dy"):values=values/px*100
        columns[key]=values
    data=pd.DataFrame(columns,index=dates)
    if data.loc[dates[-52]:].isna().any().any():
        raise ValueError("Missing one or more recent source lookback inputs")
    engine_dir=Path(__file__).resolve().parents[1]
    out.mkdir(parents=True,exist_ok=False)
    results={}
    for name,class_name in (("primas","PrimasStrategy"),
             ("triple40","Triple40Strategy"),
             ("pushen","PuShenStrategy"),
             ("competitive","CompetitiveStrategy")):
        strategy_dir=engine_dir/name
        sys.path.insert(0,str(strategy_dir))
        try:
            sys.modules.pop("strategy",None)
            strategy_class=getattr(importlib.import_module("strategy"),class_name)
        finally:sys.path.pop(0)
        events=[]
        for day,row in data.iterrows():
            stamp=day.to_pydatetime().replace(tzinfo=timezone.utc)
            for key,(dataset,instrument) in DATASETS.items():
                if pd.isna(row[key]):continue
                events.append(DataEvent("freeburg_current_captured_backfill",dataset,instrument,
                  stamp,now,float(row[key])))
        events.append(DataEvent("freeburg_capture_decision_clock",
           "clock.weekly.freeburg",None,
           dates[-1].to_pydatetime().replace(tzinfo=timezone.utc),now+timedelta(seconds=2),None))
        audit=AuditLog(out/(name+".jsonl"))
        ReplayEngine(strategy=strategy_class(),broker=SimBroker(),events=events,
           audit=audit,planner=DecisionOnlyPlanner(),
           config={"classification":"live-shadow/backfill-captured-today"}).run()
        actions=[r for r in audit.records if r.kind=="strategy_action"]
        if len(actions)!=1:raise ValueError(f"{name}: wrong number of weekly actions {len(actions)}")
        action=actions[0].payload
        results[name]=int(action.weight)
    report={"schema":"freeburg.four.canonical-shadow.v1",
        "captured_utc":now.isoformat(),"decision_friday":cutoff.date().isoformat(),
        "states":results,"spy_target_weight":sum(results.values())/4,
        "actual_causaltrader_strategy_classes":True,
        "historical_backfill_availability":"CAPTURED_TODAY_NOT_HISTORICALLY_PIT",
        "paper_orders_authorized":False}
    (out/"signal.json").write_text(json.dumps(report,indent=2)+"\n")
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--snapshot",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    print(json.dumps(produce(a.snapshot,a.output),indent=2))
if __name__=="__main__":main()
