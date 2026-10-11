"""Compare independently acquired FRASER historical fundamentals to frozen sleeves.

No replacement or publication clearance is implied. Using next-month issue date
is a conservative *heuristic*, NOT a verified first publication timestamp.
Run: python -m freeburg.tools.compare_fraser_fundamentals
  --fraser-dir <scratchpad/research/freeburg/data/fraser_sp500>
  --sleeve-dir <alpha-strategies/freeburg>
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import pandas as pd


def _signal(df: pd.DataFrame, sleeve: str, column: str) -> pd.Series:
    df=df.set_index("date").sort_index()
    if sleeve=="competitive":
        flags=[df[c]<df[c].shift(24) for c in
               ("tbond_10y","tbill_3m",column,"cpi")]
        cols=df[["tbond_10y","tbill_3m",column,"cpi"]]
        valid=cols.notna().all(axis=1)&cols.shift(24).notna().all(axis=1)
        return (sum(flags)>=2).where(valid)
    spread=df[column]-df["cp"]
    valid=(spread.notna()&spread.shift(50).notna()&
           df["spx"].notna()&df["spx"].shift(50).notna())
    return ((spread>spread.shift(50))&
            (df["spx"]>df["spx"].shift(50))).where(valid)


def analyze(sleeve: str, fraser_dir: Path, sleeve_dir: Path) -> dict:
    col,source_file,source_col={
        "competitive":("dividend_yield","sp500_dividend_yield_weekly_first_published.csv",
                       "dividend_yield_percent"),
        "pushen":("earnings_yield","sp500_earnings_yield_quarterly_first_published.csv",
                  "earnings_yield_percent"),
    }[sleeve]
    x=pd.read_csv(sleeve_dir/sleeve/"data/pit_weekly_inputs.csv",parse_dates=["date"])
    f=pd.read_csv(fraser_dir/source_file,parse_dates=["issue_date","period_date"])
    f[source_col]=pd.to_numeric(f[source_col],errors="coerce")
    f=f.dropna(subset=[source_col]).sort_values(["issue_date","period_date"])
    # The issue date is NOT publication timing. Delay conservatively by one month
    # for a sensitivity experiment; archive availability still needs validation.
    f["assumed_available"]=f.issue_date+pd.offsets.MonthBegin(1)
    f["assumed_available"]=f[["assumed_available","period_date"]].max(axis=1)
    f=f.sort_values(["assumed_available","period_date"]).drop_duplicates(
        subset=["assumed_available"],keep="last")
    a=pd.merge_asof(x.sort_values("date"),f[["assumed_available",source_col,"period_date"]]
                    .sort_values("assumed_available"),left_on="date",
                    right_on="assumed_available",direction="backward")
    # The scratchpad archive stops in 2010. Exclude periods after the last
    # underlying source observation: no indefinite forward-fill into 2026.
    source_end=f.period_date.max()
    a.loc[a["date"] > source_end,source_col]=float("nan")
    original=x.set_index("date")[col]
    candidate=a.set_index("date")[source_col].reindex(original.index)
    valid=original.notna()&candidate.notna()
    delta=(original-candidate).abs()
    ref=_signal(x,sleeve,col)
    alt=x.copy();alt[col]=candidate.to_numpy()
    test=_signal(alt,sleeve,col)
    common=ref.notna()&test.notna()
    bad=common&ref.ne(test)
    return {
        "sleeve":sleeve,
        "data_origin":"FRASER first-published reconstructed figures",
        "source_last_period":str(f.period_date.max().date()),
        "assumed_annual_issue_delay":"first of next month; heuristic, NOT PIT verified",
        "matched_weekly_values":int(valid.sum()),
        "mean_abs_percent_point_difference":round(float(delta[valid].mean()),5),
        "median_abs_percent_point_difference":round(float(delta[valid].median()),5),
        "percent_within_0_05_pp":round(100*float((delta[valid]<=.05).mean()),3),
        "comparable_strategy_weeks":int(common.sum()),
        "changed_strategy_decisions":int(bad.sum()),
        "changed_decisions_percent":round(100*float(bad.sum())/max(1,int(common.sum())),4),
        "first_changed_dates":[str(d.date()) for d in bad[bad].index[:12]],
        "limitations":"Frozen sleeve uses synthetic observation availability. Source may differ in "
                      "measurement definition and later observations are forward-filled "
                      "beyond archive end; do not interpret as full independent reconstruction.",
    }


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fraser-dir",type=Path,required=True)
    p.add_argument("--sleeve-dir",type=Path,required=True)
    args=p.parse_args()
    print(json.dumps([analyze(s,args.fraser_dir,args.sleeve_dir)
                      for s in ("competitive","pushen")],indent=2))


if __name__=="__main__":
    main()
