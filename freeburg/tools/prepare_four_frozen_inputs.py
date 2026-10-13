"""Prepare Freeburg-4 offline input tables from repository's frozen research snapshots.

Run explicitly as *frozen-input* mode: these historical rate/price columns were
previously assembled and are not themselves a fresh-download PIT certification.
The remaining quarterly S&P, FRED BAA and AGG inputs must be provided by user.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
import pandas as pd

def prepare(root:Path,output:Path)->dict:
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("Refuse overwrite existing prepared inputs")
    p=pd.read_csv(root/"pushen/data/pit_weekly_inputs.csv",parse_dates=["date"]).set_index("date")
    c=pd.read_csv(root/"competitive/data/pit_weekly_inputs.csv",parse_dates=["date"]).set_index("date")
    if not p.index.equals(c.index):raise ValueError("Frozen price and macro dates diverge")
    output.mkdir(parents=True,exist_ok=True)
    files={"weekly_prices":p[["spx","cp"]],"macro":c[["tbond_10y","tbill_3m","cpi"]]}
    hashes={}
    for name,data in files.items():
        if data.isna().any().any():raise ValueError("Missing frozen input values")
        path=output/(name+".csv")
        data.rename_axis("date").to_csv(path,float_format="%.16g")
        hashes[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    summary={"mode":"FROZEN_RESEARCH_SNAPSHOT_NOT_INDEPENDENT_SOURCE_REBUILD",
        "dates":len(p),"start":p.index.min().date().isoformat(),
        "end":p.index.max().date().isoformat(),
        "files_sha256":hashes,
        "critical_missing_sources":["archived S&P quarterly EPS and dividends; see docs",
                                    "monthly FRED BAA","AGG adjusted-close forward weekly returns"],
        "source_warning":"Frozen CSVs contain later-processed historical values and do not independently prove PIT"}
    (output/"source_manifest.json").write_text(json.dumps(summary,indent=2)+"\n")
    return summary
if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--freeburg-root",type=Path,default=Path("freeburg"))
    ap.add_argument("--output-dir",type=Path,required=True)
    a=ap.parse_args()
    print(json.dumps(prepare(a.freeburg_root,a.output_dir),indent=2))
