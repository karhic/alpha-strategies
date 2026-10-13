"""Re-acquire the exact *source snapshot URLs* behind the S&P quarterly archive.

21 capture times/URLs, no proprietary numeric values bundled. For each
quarter, retain earliest historical-actual capture separately for reported EPS
and quarterly dividends. Binary workbooks stay local, never in git.
Not certified as true initial release availability/PIT.
"""
from __future__ import annotations
import argparse,hashlib,io,json,time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import pandas as pd,requests

def parse_workbook(body,source):
    if not body.startswith(b'PK\x03\x04'):raise ValueError("Expected XLSX archive bytes")
    cap=pd.to_datetime(source["timestamp"],format="%Y%m%d%H%M%S")
    metadata=pd.read_excel(io.BytesIO(body),sheet_name="SECTOR EPS",header=None,nrows=20,engine="openpyxl")
    cutoff=None
    for _,r in metadata.iterrows():
        cells=r.tolist()
        for i,v in enumerate(cells):
            if isinstance(v,str) and "historical actual" in v.lower():
                for z in cells[i+1:i+7]:
                    dt=pd.to_datetime(z,errors="coerce")
                    if pd.notna(dt):
                        cutoff=pd.Timestamp(dt).normalize()
                        break
    if cutoff is None:raise ValueError("Cannot establish historical-actual cutoff")
    sheet=pd.read_excel(io.BytesIO(body),sheet_name="QUARTERLY DATA",header=None,engine="openpyxl")
    found=[]
    for _,r in sheet.iterrows():
        dt=pd.to_datetime(r.iloc[0],errors="coerce")
        if pd.isna(dt):continue
        dt=pd.Timestamp(dt).normalize()
        if not 1950<=dt.year<=2030 or dt.month not in (3,6,9,12) or dt>cutoff:continue
        vals=[pd.to_numeric(r.iloc[i],errors="coerce") for i in (1,2,3)]
        if pd.isna(vals[1]) and pd.isna(vals[2]):continue
        # Normalize end-of-quarter trading day to quarter ending date.
        dt=dt.to_period("Q").end_time.normalize()
        found.append({
            "quarter_date":dt,"capture_timestamp":cap,
            "as_reported_eps":vals[1],"dividends_per_share":vals[2],
            "source_url":source["original"],
            "snapshot_sha256":hashlib.sha256(body).hexdigest()})
    if not found:raise ValueError("No historical-actual quarterly observations")
    return found

def download_one(src,timeout=65,cache=None):
    if cache is not None:
        local=Path(cache)/(src["timestamp"]+".xlsx")
        if local.exists():
            blob=local.read_bytes()
            rows=parse_workbook(blob,src)
            return rows,{"timestamp":src["timestamp"],"original":src["original"],
                "status":"OK","bytes":len(blob),"sha256":hashlib.sha256(blob).hexdigest(),
                "retrieval":"USER_SUPPLIED_LOCAL_SNAPSHOT"},blob
    url=f'https://web.archive.org/web/{src["timestamp"]}id_/{src["original"]}'
    err=None
    for attempt in range(3):
        try:
            res=requests.get(url,timeout=timeout,headers={"User-Agent":"Mozilla/5.0 Freeburg reproducibility researcher"})
            res.raise_for_status()
            rows=parse_workbook(res.content,src)
            return rows,{"timestamp":src["timestamp"],"original":src["original"],
                "status":"OK","bytes":len(res.content),"sha256":hashlib.sha256(res.content).hexdigest()},res.content
        except Exception as e:
            err=str(e)
            if attempt<2:time.sleep(2*(attempt+1))
    return [],{"timestamp":src["timestamp"],"original":src["original"],"status":"FAILED","error":err},None

def harvest(manifest,output,*,workers=3,cache=None):
    if output.exists() and any(output.iterdir()):raise FileExistsError("Use an empty output directory")
    sources=json.loads(manifest.read_text())
    if not sources:raise ValueError("No archive source manifest")
    if workers>4 or workers<1:raise ValueError("Choose 1–4 workers")
    output.mkdir(parents=True,exist_ok=True)
    (output/"snapshots").mkdir(exist_ok=True)
    observations=[];records=[]
    with ThreadPoolExecutor(max_workers=workers) as ex:
        tasks={ex.submit(download_one,src,65,cache):src for src in sources}
        for f in as_completed(tasks):
            rows,rec,blob=f.result()
            observations+=rows;records.append(rec)
            if blob:
                (output/"snapshots"/(rec["timestamp"]+".xlsx")).write_bytes(blob)
            print("WAYBACK",rec["timestamp"],rec["status"],len(rows),flush=True)
    if not observations:
        (output/"acquisition_manifest.json").write_text(json.dumps(records,indent=2))
        raise RuntimeError("No archive snapshots downloaded")
    allrows=pd.DataFrame(observations).sort_values(["quarter_date","capture_timestamp"])
    allrows.to_csv(output/"observed_quarterly_values.csv",index=False)
    expected_cols={}
    for kind in ("as_reported_eps","dividends_per_share"):
        good=allrows.dropna(subset=[kind])
        selected=good.sort_values(["quarter_date","capture_timestamp"]).drop_duplicates("quarter_date",keep="first")
        expected_cols[kind]=selected.set_index("quarter_date")
    keys=expected_cols["as_reported_eps"].index.union(expected_cols["dividends_per_share"].index).sort_values()
    out=pd.DataFrame(index=keys)
    for kind,short in (("as_reported_eps","eps"),("dividends_per_share","div")):
        frame=expected_cols[kind]
        out[kind]=frame[kind].reindex(keys)
        out[short+"_capture_timestamp"]=frame.capture_timestamp.reindex(keys)
        out[short+"_source_url"]=frame.source_url.reindex(keys)
        out[short+"_snapshot_sha256"]=frame.snapshot_sha256.reindex(keys)
    out.index.name="quarter_date"
    out.to_csv(output/"quarterly_first_observed_actual.csv")
    check=out.loc["1988-03-31":"2025-09-30"]
    missing=check[["as_reported_eps","dividends_per_share"]].isna().sum().to_dict()
    report={"source_count":len(sources),"successes":sum(r["status"]=="OK" for r in records),
         "failed":[r for r in records if r["status"]!="OK"],
         "quarters":len(out),"quarter_min":str(out.index.min().date()),
         "quarter_max":str(out.index.max().date()),
         "missing_selected_field_counts":missing,
         "status":"USER_DOWNLOADED_HISTORICAL_ARCHIVE__NOT_PIT_CERTIFIED",
         "warning":"Archive first capture is not necessarily source first-publication date, and reported values could have been revised.",
         "snapshots":records}
    (output/"acquisition_manifest.json").write_text(json.dumps(report,indent=2)+"\n")
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest",type=Path,default=Path("freeburg/sources/sp500_wayback_captures.json"))
    p.add_argument("--output-dir",required=True,type=Path)
    p.add_argument("--workers",type=int,default=3)
    p.add_argument("--snapshot-cache",type=Path,help="Optional folder with timestamp.xlsx copies for inaccessible Wayback captures")
    p.add_argument("--accept-source-terms",required=True,action="store_true")
    a=p.parse_args()
    result=harvest(a.manifest,a.output_dir,workers=a.workers,cache=a.snapshot_cache)
    print(json.dumps({k:v for k,v in result.items() if k!="snapshots"},indent=2))
if __name__=="__main__":main()
