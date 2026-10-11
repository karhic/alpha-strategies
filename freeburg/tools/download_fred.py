"""Download fresh FRED observations for Prime/Discount using a user's own API key.

User-local artifacts only. FRED may host third-party IMF/Moody's content;
permissions do not automatically transfer to open-source redistribution.
"""
from __future__ import annotations
import argparse,hashlib,json,os
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen
from freeburg.prime_discount.build_fed_public_events import fred_json_series

SERIES=("DPRIME","INTDSRUSM193N")
API="https://api.stlouisfed.org/fred/series/observations"
def download(dest:Path, *, api_key:str, opener=None, series=SERIES)->dict:
    if not (len(api_key)==32 and api_key.isalnum() and api_key==api_key.lower()):
        raise ValueError("Pass a 32-character lowercase FRED API key")
    if dest.exists() and any(dest.iterdir()):
        raise FileExistsError("Use an empty output directory for this snapshot")
    op=opener or urlopen
    downloaded=[]
    dest.mkdir(parents=True,exist_ok=True)
    for name in series:
        if name not in SERIES:raise ValueError("Series not in source whitelist")
        # Never print or persist the key as part of any URL/manifest.
        params=urlencode({"series_id":name,"api_key":api_key,"file_type":"json",
                          "observation_start":"1900-01-01",
                          "observation_end":"9999-12-31"})
        request=Request(API+"?"+params,headers={"User-Agent":"Freeburg-user-research/0.3"})
        with op(request,timeout=80) as res:
            data=res.read(10_000_001)
            if getattr(res,"status",200)!=200:raise ValueError("FRED HTTP failure")
        if len(data)>10_000_000:raise ValueError("Oversized FRED response")
        payload=json.loads(data)
        if not isinstance(payload.get("observations"),list):
            raise ValueError("FRED observations missing")
        file=dest/(name+".json")
        file.write_bytes(data)
        numeric=fred_json_series(file)
        downloaded.append({"series":name,"observations_numeric":len(numeric),
                           "first":str(numeric.index.min().date()),
                           "last":str(numeric.index.max().date()),
                           "bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()})
    report={"provider":"FRED API v1 (user-owned key; IMF source rights may apply)",
            "api_endpoint":API,"results":downloaded,
            "historical_timing":"RETROSPECTIVE_AS_OF_DOWNLOAD__NOT_PIT_CERTIFIED",
            "redistribution_rights":"UNVERIFIED"}
    (dest/"manifest.json").write_text(json.dumps(report,indent=2)+"\n")
    return report
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-dir",required=True,type=Path)
    a=p.parse_args()
    key=os.getenv("FRED_API_KEY")
    if not key:p.error("Set FRED_API_KEY in your environment; no key is stored in the manifest")
    print(json.dumps(download(a.output_dir,api_key=key),indent=2))
if __name__=="__main__":main()
