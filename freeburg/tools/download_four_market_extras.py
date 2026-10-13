"""User-side download of monthly Moody Baa and AGG weekly total-return inputs.

Outputs are local files only. Read provider terms before running; license,
historical revisions and publication-time accuracy are not certified.
"""
from __future__ import annotations
import argparse,hashlib,json,time
from pathlib import Path
import pandas as pd
import requests
from urllib.parse import quote

FRED="https://fred.stlouisfed.org/graph/fredgraph.csv?id=BAA&cosd=2010-01-01"
YAHOO="https://query1.finance.yahoo.com/v8/finance/chart/AGG"

def fetch(output:Path)->dict:
    if output.exists() and any(output.iterdir()):raise FileExistsError("New empty output directory required")
    output.mkdir(parents=True,exist_ok=True)
    headers={"User-Agent":"Mozilla/5.0 Freeburg local research"}
    a=None
    for attempt in range(4):
        try:
            a=requests.get(FRED,headers=headers,timeout=22)
            a.raise_for_status()
            break
        except requests.RequestException:
            if attempt==3:raise
            time.sleep(2+attempt*2)
    import io
    monthly=pd.read_csv(io.BytesIO(a.content),parse_dates=["observation_date"])
    if not {"observation_date","BAA"}.issubset(monthly.columns) or len(monthly)<180:
        raise ValueError("Monthly FRED BAA source malformed/incomplete")
    monthly[["observation_date","BAA"]].to_csv(output/"fred_baa_monthly.csv",index=False)
    r=requests.get(YAHOO,params={"period1":1377907200,"period2":1787000000,
        "interval":"1d","events":"history"},headers=headers,timeout=80)
    r.raise_for_status()
    chart=r.json()["chart"]["result"][0]
    dates=pd.to_datetime(chart["timestamp"],unit="s",utc=True).tz_convert(None).normalize()
    adj=pd.Series(chart["indicators"]["adjclose"][0]["adjclose"],index=dates,dtype=float).dropna()
    forwards=adj.resample("W-FRI").last().pct_change().shift(-1).dropna()
    forwards.rename("agg").rename_axis("date").to_csv(output/"agg_weekly_forward.csv")
    if len(forwards)<650:raise ValueError("Incomplete AGG input window")
    paths=[output/"fred_baa_monthly.csv",output/"agg_weekly_forward.csv"]
    manifest={"mode":"THIRD_PARTY_USER_DOWNLOAD_NOT_PIT_CERTIFICATION",
        "files":{z.name:hashlib.sha256(z.read_bytes()).hexdigest() for z in paths},
        "original_urls":[FRED,YAHOO],
        "warning":"Source date can be observation date rather than actual historical release. Terms vary by supplier."}
    (output/"provider_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    return manifest
if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",type=Path,required=True)
    ap.add_argument("--accept-provider-terms",action="store_true",required=True)
    x=ap.parse_args()
    print(json.dumps(fetch(x.output_dir),indent=2))
