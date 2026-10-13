"""Render year-by-year OOS performance tables from weekly return inputs."""
from __future__ import annotations
import argparse, math
from pathlib import Path
import numpy as np
import pandas as pd

SLEEVES={"triple40":("Triple40","Triple-40"),"pushen":("PuShen","Pu Shen"),"competitive":("Competitive","Competitive Returns")}
METRICS=[("return","Annual return"),("sharpe","Excess Sharpe"),("calmar","Calmar"),("max_dd","Maximum drawdown")]

def one_year(x,rf,ytd):
    a=x.to_numpy(float);b=rf.to_numpy(float)
    eq=np.r_[1.0,np.cumprod(1.0+a)]
    ret=float(eq[-1]-1.0)
    dd=float((eq/np.maximum.accumulate(eq)-1.0).min())
    excess=a-b;sd=float(excess.std(ddof=1))
    sh=float(excess.mean()/sd*math.sqrt(52)) if sd>.0015 else np.nan
    num=float(eq[-1]**(52/len(a))-1) if ytd else ret
    return {"return":ret,"sharpe":sh,"calmar":num/abs(dd) if dd<0 else np.nan,"max_dd":dd,"weeks":len(a)}

def display(x,key):
    if pd.isna(x):return "—"
    if key=="return":return f"{x*100:+.1f}%"
    if key=="max_dd":return f"{x*100:.1f}%"
    return f"{x:.2f}"

def render(source,slug,output):
    label,title=SLEEVES[slug]
    joined=pd.DataFrame({label:source[label],"Buy & hold":source["stock"],"60/40":0.6*source["stock"]+0.4*source["agg"]},index=source.index)
    records=[]
    for year,sub in joined.groupby(joined.index.year):
        if year<2014:continue
        if year<2026 and len(sub)<49:raise ValueError(f"Incomplete year {year}")
        for c in joined:
            records.append({"year":int(year),"series":c,**one_year(sub[c],source.loc[sub.index,"rf"],year==2026)})
    df=pd.DataFrame(records)
    report=[f"# {title}: Year-by-year out-of-sample comparison","",
            "**2014–2025 are complete calendar years; 2026 is YTD through 7 August 2026 (32 weeks).**","",
            "Four compact metric tables compare the sleeve with buy-and-hold and a weekly-rebalanced 60/40 portfolio. Machine-readable statistics: [annual comparison CSV](annual_comparison_2014_2026.csv).",""]
    for key,heading in METRICS:
        report.extend([f"## {heading}","","| Year | "+title+" | S&P buy & hold | 60/40 |","|---|---:|---:|---:|"])
        for year in sorted(df.year.unique()):
            year_data=df[df.year.eq(year)].set_index("series")
            values=[display(year_data.loc[c,key],key) for c in (label,"Buy & hold","60/40")]
            report.append(f"| {year}{' (YTD)' if year==2026 else ''} | "+" | ".join(values)+" |")
        report.append("")
    report += ["## Definitions and interpretation","",
       "- **Return:** compounded weekly returns indexed to the decision Friday; underlying holding returns are close-to-next-close and may settle in the next calendar year.",
       "- **Excess Sharpe:** mean of weekly returns minus contemporaneous nonnegative 3-month Treasury-bill carry, divided by standard deviation of those excess returns and multiplied by sqrt(52). This differs from raw-return Sharpe in the main README. Em dashes indicate weekly excess-return volatility below 0.15%, suppressing spurious huge ratios in cash-only years.",
       "- **Calmar:** annual compounded return / absolute maximum within-year drawdown, with the 2026 YTD return annualized before division. Zero drawdown makes the ratio undefined. This is an annual diagnostic, NOT a conventional 3-year rolling Calmar.",
       "- **Max drawdown:** calculated within each calendar year, resetting wealth to 1.0 at the year boundary; outstanding drawdowns from preceding years are excluded.",
       "- **S&P buy & hold:** same existing Freeburg OOS S&P weekly price-return-plus-dividend-accrual approximation, not ETF after-fee total return.",
       "- **60/40:** 60% the same S&P return plus 40% AGG adjusted-close total returns, rebalanced weekly; AGG is a broad US aggregate-bond ETF proxy rather than a Treasury-only index. Trading costs and taxes excluded.",
       "- **Method/data:** the original 90-day-lag post-2013 OOS research in edge-research-scratchpad/research/freeburg/test_post2013_and_leverage_v4.py. The AGG series was obtained from Yahoo Finance for this diagnostic; rights to raw provider data are not assumed.",
       "- **2026:** through August 7, not a full year.",
       "","Cash-heavy years often have undefined or misleadingly extreme annual risk-adjusted ratios.","",
       "## Rebuild","",
       "Use the available Freeburg tools build_annual_oos_inputs and render_annual_oos with the user's own scratchpad checkout and locally retrieved AGG observations. Source prices are not committed.",""]
    output.mkdir(parents=True,exist_ok=True)
    df.to_csv(output/"annual_comparison_2014_2026.csv",index=False)
    (output/"README.md").write_text("\n".join(report),encoding="utf-8")
    return len(df)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--weekly-returns",type=Path,required=True)
    p.add_argument("--sleeves",nargs="+",choices=sorted(SLEEVES),default=list(SLEEVES))
    p.add_argument("--output-root",type=Path,default=Path("freeburg"))
    a=p.parse_args()
    x=pd.read_csv(a.weekly_returns,parse_dates=["date"]).set_index("date")
    if x.index.has_duplicates or x.isna().any().any():raise ValueError("Missing values/duplicate weeks")
    for slug in a.sleeves:
        output=a.output_root/slug/"reports"
        if output.exists():raise FileExistsError(output)
        print(slug,render(x,slug,output))
if __name__=="__main__":main()
