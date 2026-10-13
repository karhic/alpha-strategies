"""Rebuild weekly Pu Shen / Competitive fundamentals from already researched vintages.

Does not re-OCR FRASER. Reuses audited first-published source observations, and
GovInfo's actual downloaded XLS. Archive/issue timestamps are ASSUMPTIONS,
not certified original first-publication dates. A source's underlying S&P
figures have separate redistribution/commercial-use rights.
"""
from __future__ import annotations
import argparse
from datetime import timedelta
import json
from pathlib import Path

import pandas as pd
from freeburg.tools.free_data import _float, load_prices, govinfo_preview


def load_events(fraser_dir: Path, govinfo_csv: Path, xls_dir: Path,
                lag_days: int = 7) -> tuple[pd.DataFrame,pd.DataFrame,dict]:
    eps_rows, div_rows, issues = [], [], {}
    fr_eps=pd.read_csv(fraser_dir/"sp500_earnings_estimate_vintages.csv",
                       parse_dates=["issue_date","period_date","available_printed_anchor"])
    fr_eps["ttm_eps"]=pd.to_numeric(fr_eps["ttm_eps"],errors="coerce")
    fr_eps=fr_eps.dropna(subset=["ttm_eps","available_printed_anchor"])
    # Prefer raw parsed data when available on the same observation/issue date.
    fr_eps["quality"]=fr_eps["cleaning"].ne("raw_parsed").astype(int)
    fr_eps=fr_eps.sort_values(["period_date","available_printed_anchor","quality"])
    fr_eps=fr_eps.drop_duplicates("period_date",keep="first")
    for r in fr_eps.itertuples(index=False):
        if not 0 < r.ttm_eps < 1000:continue
        eps_rows.append(dict(available=r.available_printed_anchor+pd.Timedelta(days=lag_days),
            period=r.period_date,value=float(r.ttm_eps),origin="FRASER",
            url=r.source_url))
    fr_div=pd.read_csv(fraser_dir/"sp500_dividend_yield_weekly_first_published.csv",
                       parse_dates=["issue_date","period_date"])
    fr_div["dividend_yield_percent"]=pd.to_numeric(
        fr_div["dividend_yield_percent"],errors="coerce")
    fr_div=fr_div.dropna(subset=["period_date","dividend_yield_percent"])
    fr_div=fr_div.sort_values(["period_date","issue_date"]).drop_duplicates(
        "period_date",keep="first")
    for r in fr_div.itertuples(index=False):
        if not 0 < r.dividend_yield_percent < 25:continue
        # Delayed observational scenario; period may be labelled ahead of
        # nominal issue. Never emit before BOTH reporting anchors.
        available=max(r.issue_date+pd.offsets.MonthEnd(0),
                      r.period_date)+pd.Timedelta(days=lag_days)
        div_rows.append(dict(available=available,period=r.period_date,
            value=float(r.dividend_yield_percent),origin="FRASER",url=r.source_url))
    gov=pd.read_csv(govinfo_csv,parse_dates=[
        "period_date","earliest_scenario_date"])
    gov["value"]=pd.to_numeric(gov["value"],errors="coerce")
    for r in gov.itertuples(index=False):
        if pd.isna(r.value) or pd.isna(r.earliest_scenario_date):continue
        avail=r.earliest_scenario_date+pd.Timedelta(days=1)
        if avail<=r.period_date:continue
        rec=dict(available=avail,period=r.period_date,origin="GovInfo",
                 url=r.source_url)
        if r.series=="dividend_yield":
            if 0<r.value<25:div_rows.append({**rec,"value":float(r.value)})
        elif r.series=="earnings_yield":
            # Published ratio is quarterly E/P, not weekly earnings/Friday SPX.
            # Infer underlying TTM EPS using the SAME source-row monthly average.
            issue=r.issue
            if issue not in issues:
                p=xls_dir/f"ECONI-{issue}-Pg31.xls"
                if not p.exists():raise FileNotFoundError(p)
                issues[issue]=govinfo_preview(p,max_rows=100)
            rows=issues[issue]
            i=int(r.source_row)-1
            if i<0 or i>=len(rows) or len(rows[i])<10:
                raise ValueError(f"Invalid source row for {issue}: {r.source_row}")
            monthly_spx=_float(rows[i][6])
            if monthly_spx is None or not 10<monthly_spx<100000:
                continue
            eps=float(r.value)*monthly_spx/100.
            if 0<eps<5000:eps_rows.append({**rec,"value":eps})
    def cleanup(rows):
        x=pd.DataFrame(rows)
        x=x.sort_values(["available","period","origin"],kind="stable")
        # A later catalog record about an older observation must never
        # revert the active state to an older EPS/dividend reporting period.
        # For duplicate availability timestamps choose most recent period.
        x=x.drop_duplicates(["available"],keep="last")
        latest=pd.Timestamp("1900-01-01")
        selected=[]
        for r in x.itertuples(index=False):
            if r.period>=latest:
                selected.append(dict(available=r.available,period=r.period,
                                     value=r.value,origin=r.origin,url=r.url))
                latest=r.period
        return pd.DataFrame(selected).sort_values("available")
    return cleanup(eps_rows),cleanup(div_rows),{
        "fraser_earnings":len(fr_eps),"fraser_dividends":len(fr_div),
        "govinfo_source_rows":len(gov),"govinfo_workbooks_inspected":len(issues),
        "assumed_fraser_lag_days":lag_days,
        "govinfo_timing":"recordCreationDate+1day, NOT verified public release",
    }


def asof(events:pd.DataFrame, days:pd.DatetimeIndex,
         value_name:str)->tuple[pd.Series,pd.Series,pd.Series]:
    left=pd.DataFrame({"date":pd.DatetimeIndex(days).as_unit("ns")})
    right=events[["available","period","value","origin"]].rename(
        columns={"available":"date"}).sort_values("date")
    right["date"]=pd.to_datetime(right["date"]).astype("datetime64[ns]")
    merged=pd.merge_asof(left,right,on="date",direction="backward",
                         allow_exact_matches=True)
    value=pd.Series(merged["value"].to_numpy(),index=days,name=value_name)
    source=pd.Series(merged["origin"].to_numpy(),index=days)
    period=pd.Series(merged["period"].to_numpy(),index=days)
    return value,source,period


def build(prices:Path,fraser_dir:Path,govinfo_csv:Path,xls_dir:Path,
          output:Path,metadata:Path,lag_days=7)->dict:
    if output.exists() or metadata.exists():
        raise FileExistsError("Use new output files; never overwrite an audited run")
    p=load_prices(prices)
    days=pd.DatetimeIndex(sorted(pd.Timestamp(d) for d in p))
    spx=pd.Series([p[d.date()] for d in days],index=days,dtype=float,name="spx")
    eps,div,inputs=load_events(fraser_dir,govinfo_csv,xls_dir,lag_days)
    earnings,earn_src,earn_period=asof(eps,days,"ttm_eps")
    dividend,div_src,div_period=asof(div,days,"dividend_yield")
    ey=100*earnings/spx
    result=pd.DataFrame({"date":days,"spx":spx.to_numpy(),
                         "earnings_yield":ey.to_numpy(),
                         "dividend_yield":dividend.to_numpy(),
                         "eps_source":earn_src.to_numpy(),
                         "div_source":div_src.to_numpy(),
                         "eps_period":earn_period.to_numpy(),
                         "div_period":div_period.to_numpy()})
    output.parent.mkdir(parents=True,exist_ok=True)
    result.to_csv(output,index=False)
    report={"source_earnings_events":len(eps),"source_dividend_events":len(div),
       "weeks":len(result),"weeks_with_earnings":int(ey.notna().sum()),
       "weeks_with_dividend":int(dividend.notna().sum()),
       "earliest_earnings_week":str(ey.first_valid_index().date()) if ey.first_valid_index() else None,
       "earliest_dividend_week":str(dividend.first_valid_index().date()) if dividend.first_valid_index() else None,
       "output":str(output),
       "status":"RECONSTRUCTED_RESEARCH_AVAILABILITY_SCENARIO_NOT_CERTIFIED_PIT",
       "inputs":inputs}
    metadata.write_text(json.dumps(report,indent=2)+"\n")
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--prices",required=True,type=Path)
    p.add_argument("--fraser-dir",required=True,type=Path)
    p.add_argument("--govinfo-vintages",required=True,type=Path)
    p.add_argument("--govinfo-xls-dir",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    p.add_argument("--report",required=True,type=Path)
    p.add_argument("--fraser-lag-days",type=int,default=7)
    args=p.parse_args()
    if args.fraser_lag_days<0: p.error("Negative FRASER lag rejected")
    print(json.dumps(build(args.prices,args.fraser_dir,args.govinfo_vintages,
                           args.govinfo_xls_dir,args.output,args.report,
                           args.fraser_lag_days),indent=2))


if __name__=="__main__":main()
