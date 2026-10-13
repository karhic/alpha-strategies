"""Build S&P 500 quarterly dividend-point observations from PR/TR index levels.

Underlying indices are calculated by S&P Dow Jones Indices; Yahoo is a
SECONDARY distributor of the daily levels. S&P index-mathematics identity:

    dividend_points[t] = PR[t-1] * TR[t] / TR[t-1] - PR[t]

No historical publication date is inferred from retrospective observations.
New captures are immutable and qualified for future shadow signals no earlier
than the actual local acquisition timestamp. Trading is NOT authorized.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import pandas as pd
import requests
from freeburg.deploy.capture_live import _spx_close

ROOT = "https://query1.finance.yahoo.com/v8/finance/chart/"
SOURCES = {"price": ROOT + "%5EGSPC", "total_return": ROOT + "%5ESP500TR"}
MAX_BYTES=8_000_000
SP_MATH_URL="https://www.spglobal.com/spdji/en/methodology/article/index-mathematics-methodology/"
SP_DIVIDEND_POINTS_URL="https://www.spglobal.com/spdji/en/education/article/faq-sp-500-dividend-points-index/"

def calculate(price: pd.Series, total_return: pd.Series, *, now:datetime) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Derive completed-quarter index dividend points from matched daily closes."""
    if now.tzinfo is None:raise ValueError("Snapshot time must be timezone-aware")
    daily=pd.concat({"price":price, "total_return":total_return},axis=1).dropna().sort_index()
    if daily.index.has_duplicates or len(daily)<400:
        raise ValueError("Need 400+ matched daily price and gross-total-return closes")
    if daily.isna().any().any() or (daily<=0).any().any():
        raise ValueError("Nonpositive daily index close")
    if daily.index.max()>pd.Timestamp(now.date()):
        raise ValueError("Source includes observations later than capture date")
    if (daily.index.to_series().diff().dropna()>pd.Timedelta(days=7)).any():
        raise ValueError("Source has a gap longer than 7 days")
    daily["dividend_points"]=daily.price.shift(1)*(daily.total_return/daily.total_return.shift(1))-daily.price
    daily=daily.dropna()
    if (daily["dividend_points"].abs()>20).any():
        raise ValueError("Implausible daily dividend adjustment (>20 index points)")
    # Aggregate cash dividend points on their index ex-dividend dates.
    q=daily.resample("QE-DEC").agg(dividends_per_share=("dividend_points","sum"),
                                   daily_observations=("dividend_points","size"),
                                   first_trade_date=("price",lambda s:s.index.min()),
                                   last_trade_date=("price",lambda s:s.index.max()))
    # A quarter isn't final until two calendar days after its end. Require
    # near-quarter-end closes and enough daily rows to avoid partial quarters.
    q=q[(q.index+pd.Timedelta(days=2)<pd.Timestamp(now.date())) &
        ((q.index-q.last_trade_date)<=pd.Timedelta(days=6)) &
        (q.daily_observations>=40)]
    if q.empty:raise ValueError("No complete quarters")
    q.index.name="quarter_date";daily.index.name="trade_date"
    return daily,q

def fetch_json(url:str,at:datetime)->bytes:
    end=int(at.timestamp())+86400
    response=requests.get(url,params={"period1":568080000,"period2":end,
                                       "interval":"1d","events":"history"},
                          timeout=65,headers={"User-Agent":"Mozilla/5.0 Freeburg independent index research"})
    response.raise_for_status()
    if not 1000<len(response.content)<MAX_BYTES:raise ValueError("Unexpected daily chart size")
    return response.content

def acquire(out:Path, *, now:datetime, supplied:dict[str,bytes]|None=None)->dict:
    if out.exists() and any(out.iterdir()):raise FileExistsError("Choose an empty immutable snapshot folder")
    if now.tzinfo is None:raise ValueError("Capture time must have UTC offset")
    now=now.astimezone(timezone.utc)
    sources={}
    bodies={}
    # Download and validate all sources before creating output files.
    for key,url in SOURCES.items():
        raw=supplied[key] if supplied is not None else fetch_json(url,now)
        if len(raw)>MAX_BYTES:raise ValueError("Source file too large")
        bodies[key]=raw
        sources[key]={"url":url,"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw),
                      "transport":"user_local_input" if supplied is not None else "Yahoo public chart"}
    series={key:_spx_close(raw) for key,raw in bodies.items()}
    daily,quarters=calculate(series["price"],series["total_return"],now=now)
    if quarters.index.max()<pd.Timestamp(now.date())-pd.Timedelta(days=150):
        raise ValueError("Recent quarter missing in derived index dividend series")
    out.mkdir(parents=True,exist_ok=True)
    for key,raw in bodies.items():
        (out/(key+".json")).write_bytes(raw)
    daily.to_csv(out/"daily_dividend_points.csv",float_format="%.12g")
    quarters.to_csv(out/"quarterly_dividends.csv",float_format="%.12g")
    manifest={
        "schema":"freeburg.live.sp500-dividend-point-capture.v1",
        "acquired_at_utc":now.isoformat(),
        "source_provider":"Yahoo Finance index level distributor (SECONDARY)",
        "index_calculator":"S&P Dow Jones Indices",
        "series_names":{"price":"S&P 500 Price Return (^GSPC)",
                        "total_return":"S&P 500 Gross Total Return (^SP500TR)"},
        "source_files":sources,
        "math_reference":SP_MATH_URL,"dividend_points_reference":SP_DIVIDEND_POINTS_URL,
        "formula":"PR[t-1] * (TR[t] / TR[t-1]) - PR[t]",
        "first_completed_quarter":quarters.index.min().date().isoformat(),
        "latest_completed_quarter":quarters.index.max().date().isoformat(),
        "last_dividends_per_index_share":float(quarters.dividends_per_share.iloc[-1]),
        "completed_quarters":len(quarters),
        "precision_warning":"Derived from rounded daily index levels; approximate to index points, NOT exact licensed S&P workbook dividends.",
        "data_time_warning":"Retrospective daily index levels may be restated; first live availability established only from this snapshot time.",
        "readiness":"SHADOW_RESEARCH_ONLY__NO_BROKER_ORDERS",
    }
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    return manifest

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-dir",type=Path,required=True)
    args=p.parse_args()
    result=acquire(args.output_dir,now=datetime.now(timezone.utc))
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
