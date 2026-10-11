"""Fresh user-side acquisition of explicitly permitted/public Freeburg inputs.

This *acquires* data but does not assert source licensing, point-in-time
availability, signal equivalence, or completion of all six sleeves.
No scraped S&P vendor data, no automatic publication of downloaded bytes.
"""
from __future__ import annotations
import argparse
from datetime import date
import hashlib
import json
import os
from pathlib import Path
import tempfile
from urllib.request import Request, urlopen
from .free_data import govinfo_urls

SOURCES = {
    "fed_h15": ("https://www.federalreserve.gov/datadownload/Output.aspx?filetype=zip&rel=H15", "h15.zip", "zip"),
    "nber_cp": ("https://data.nber.org/databases/macrohistory/rectdata/13/m13002.dat", "nber_m13002.dat", "text"),
}
MAX_BYTES = 80_000_000


def acquire(url: str, out: Path, kind: str, *, timeout=90, opener=None) -> dict:
    """Never substitute HTML for a market-data file; never overwrite existing."""
    if out.exists():
        raise FileExistsError(f"Refusing overwrite: {out}")
    op=opener or urlopen
    req=Request(url,headers={"User-Agent":"Freeburg-open-research/0.2"})
    with op(req,timeout=timeout) as res:
        body=res.read(MAX_BYTES+1)
        status=getattr(res,"status",200)
        if status != 200: raise ValueError(f"Unexpected HTTP status: {status}")
    if len(body)>MAX_BYTES:raise ValueError("Download exceeds 80 MB")
    if kind=="zip":
        if not body.startswith(b"PK\\x03\\x04".decode("unicode_escape").encode("latin1")):
            raise ValueError("Expected ZIP, got an unrelated payload")
    elif kind=="xls":
        if not (body.startswith(bytes.fromhex("d0cf11e0")) or body.startswith(b"PK\x03\x04")):
            raise ValueError("Expected XLS file, not HTML/error page")
    elif kind=="text":
        head=body[:300].lower().lstrip()
        if not body or head.startswith(b"<!doctype html") or head.startswith(b"<html"):
            raise ValueError("Expected raw NBER text, not HTML")
    else:raise ValueError(kind)
    out.parent.mkdir(parents=True,exist_ok=True)
    # Refuse clobbers after the network round trip, too.
    with out.open("xb") as fh:fh.write(body)
    return {"url":url,"path":str(out),"bytes":len(body),
            "sha256":hashlib.sha256(body).hexdigest(),"kind":kind}


def run(dest: Path, *, govinfo_issue: list[str], include_base=True) -> dict:
    """Stable manifest. Re-run in a NEW destination for a new fresh snapshot."""
    if dest.exists() and any(dest.iterdir()):
        raise FileExistsError("Choose an empty destination; snapshots are immutable")
    dest.mkdir(parents=True,exist_ok=True)
    downloads=[]
    issues=[*govinfo_issue]
    seen=set()
    try:
        if include_base:
            for source,(url,name,kind) in SOURCES.items():
                record=acquire(url,dest/name,kind)
                record["source_id"]=source
                downloads.append(record)
        for issue in issues:
            if issue in seen:continue
            seen.add(issue)
            links=govinfo_urls(issue,"31")
            name=f"ECONI-{issue}-Pg31.xls"
            try:
                record=acquire(links["xls"],dest/"govinfo"/name,"xls",timeout=45)
                record["source_id"]="govinfo_econi_page31"
                record["issue"]=issue
                record["status"]="SOURCE_XLS_VALID_UNVERIFIED_PIT"
            except (ValueError,OSError,TimeoutError) as exc:
                record={"source_id":"govinfo_econi_page31","issue":issue,"url":links["xls"],
                        "status":"UNAVAILABLE_OR_INVALID","error":str(exc)}
            downloads.append(record)
    finally:
        summary={"snapshot_date_utc":date.today().isoformat(),
                 "result":"ACQUISITION_ONLY_NO_SIX_SLEEVE_CERTIFICATION",
                 "files":downloads,
                 "limitations":["Stock prices require lawful user-provided input.",
                                "Moody's Baa/IMF rates may have provider terms.",
                                "Heine DJ20 and CRB series not downloaded.",
                                "GovInfo publication timing not established.",
                                "GovInfo tables are third-party S&P derived.",
                                "Source file presence is not signal parity."]}
        (dest/"manifest.json").write_text(json.dumps(summary,indent=2)+"\n")
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-dir",type=Path,required=True)
    p.add_argument("--govinfo-issue",action="append",default=[],
                   help="Specific YYYY-MM issue(s) for Common Stock Prices and Yields XLS")
    p.add_argument("--no-base",action="store_true",help="Only acquire GovInfo issue(s)")
    a=p.parse_args()
    summary=run(a.output_dir,govinfo_issue=a.govinfo_issue,include_base=not a.no_base)
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    main()
