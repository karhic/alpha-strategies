"""Optional fresh S&P 500 close download, initiated by the end user.

Yahoo's public chart endpoint is an *optional*, third-party source. Users must
review the provider's conditions before invoking. Do not redistribute downloaded
data or claim vendor rights; never store it inside tracked research fixtures.
"""
from __future__ import annotations
import argparse,csv,hashlib,json
from datetime import datetime,timezone,timedelta
from pathlib import Path
from urllib.request import Request,urlopen
from freeburg.tools.free_data import load_prices,_write_csv,price_comparison

ENDPOINT="https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC?period1=0&period2=1800000000&interval=1d&events=history"
def parse(raw:bytes)->list[dict]:
    payload=json.loads(raw)
    result=payload["chart"]["result"][0]
    stamps=result["timestamp"]
    closes=result["indicators"]["quote"][0]["close"]
    if len(stamps)!=len(closes):raise ValueError("Timestamp/close length mismatch")
    seen={}
    for stamp,close in zip(stamps,closes):
        if close is None:continue
        day=datetime.fromtimestamp(int(stamp),timezone.utc).date()
        try:v=float(close)
        except (TypeError,ValueError):continue
        if v<=0 or v>=1e7:continue
        ds=day.isoformat()
        if ds in seen and abs(seen[ds]-v)>1e-7:raise ValueError("Conflicting dates")
        seen[ds]=v
    if not seen:raise ValueError("No valid closes")
    return [{"date":d,"close":f"{v:.12g}"} for d,v in sorted(seen.items())]

def download(destination:Path, *, expected_min=10000, transport=None)->dict:
    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError("Refusing populated directory (immutable snapshot)")
    transport=transport or urlopen
    req=Request(ENDPOINT,headers={"User-Agent":"Mozilla/5.0 (research locally)"})
    with transport(req,timeout=75) as res:
        raw=res.read(20_000_001)
        status=getattr(res,"status",200)
    if status!=200:raise ValueError(f"HTTP {status}")
    if len(raw)>20_000_000:raise ValueError("Oversized price response")
    prices=parse(raw)
    if len(prices)<expected_min:
        raise ValueError(f"Short history: {len(prices)} rows, expected >= {expected_min}")
    destination.mkdir(parents=True,exist_ok=True)
    (destination/"raw_spx_chart.json").write_bytes(raw)
    _write_csv(destination/"spx_daily.csv",["date","close"],prices)
    weekly=load_prices(destination/"spx_daily.csv")
    _write_csv(destination/"spx_weekly.csv",["date","spx"],[
        {"date":d.isoformat(),"spx":f"{v:.12g}"} for d,v in weekly.items()])
    manifest={"provider":"Yahoo chart (third party, user-authorized)",
              "source_url":ENDPOINT,"rows_daily":len(prices),"rows_weekly":len(weekly),
              "first":prices[0]["date"],"last":prices[-1]["date"],
              "raw_sha256":hashlib.sha256(raw).hexdigest(),
              "license":"NOT_ESTABLISHED__LOCAL_USER_DOWNLOAD_ONLY",
              "status":"FRESH_USER_SOURCE_NOT_PIT_OR_RIGHTS_CERTIFIED"}
    (destination/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    return manifest

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-dir",type=Path,required=True)
    p.add_argument("--accept-provider-terms",action="store_true",
                   help="Confirm you have checked provider terms for your use.")
    p.add_argument("--compare-to",type=Path)
    a=p.parse_args()
    if not a.accept_provider_terms:p.error("Review source terms and explicitly pass --accept-provider-terms")
    result=download(a.output_dir)
    if a.compare_to:
        result["benchmark_comparison"]=price_comparison(a.output_dir/"spx_weekly.csv",a.compare_to)
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
