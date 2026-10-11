"""One entrypoint to rebuild and replay the already validated Freeburg sleeves.

Profiles:
- baseline: five original documented sleeves (Heine excluded)
- sources: independently rebuilt Pu Shen/Competitive fundamentals, with
           explicit frozen macro fallback and no certified PIT claim.

This tool NEVER redoes archival OCR or rewrites the original benchmark inputs.
"""
from __future__ import annotations
import argparse,json,os,subprocess,sys
from pathlib import Path
from datetime import datetime

ROOT=Path(__file__).resolve().parent
SLEEVES=("primas","triple40","pushen","competitive","prime_discount")

def launch(module, *args, cwd=None):
    cmd=[sys.executable,"-m",module,*map(str,args)]
    subprocess.run(cmd,cwd=cwd,check=True)

def replay_script(sleeve, events, ledger):
    script=ROOT/sleeve/"run_replay.py"
    subprocess.run([sys.executable,str(script),"--events",str(events),
                    "--ledger",str(ledger)],check=True)

def summarize(path):
    from collections import Counter
    counts=Counter()
    actions=[]
    with path.open() as fh:
        for line in fh:
            row=json.loads(line)
            counts[row["kind"]]+=1
            if row["kind"]=="strategy_action":
                actions.append((row["timestamp"],row["payload"].get("weight")))
    return {"ledger":str(path),"data_events":counts["data_event"],
            "strategy_decisions":len(actions),
            "first_decision":actions[0][0] if actions else None,
            "last_decision":actions[-1][0] if actions else None}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mode",choices=("baseline","sources"),default="baseline")
    p.add_argument("--output-dir",type=Path,required=True)
    p.add_argument("--fresh-snapshot",type=Path)
    p.add_argument("--fraser-dir",type=Path)
    p.add_argument("--govinfo-vintages",type=Path)
    p.add_argument("--govinfo-xls-dir",type=Path)
    a=p.parse_args()
    out=a.output_dir.resolve()
    if out.exists() and any(out.iterdir()):p.error("Use a new empty output directory")
    if a.mode=="sources" and not all([a.fresh_snapshot,a.fraser_dir,a.govinfo_vintages,a.govinfo_xls_dir]):
        p.error("sources mode requires fresh snapshot, FRASER, GovInfo vintages and XLS paths")
    out.mkdir(parents=True,exist_ok=True)
    report={"mode":a.mode,"status":"ACTUAL_CAUSAL_REPLAY_NOT_A_PIT_OR_RIGHTS_CERTIFICATION",
            "sleeves":{}, "limitations":[]}
    if a.mode=="sources":
        rebuilt=out/"rebuilt_fundamentals.csv"
        prices=a.fresh_snapshot/"spx"/"spx_weekly.csv"
        if not prices.exists():raise FileNotFoundError(prices)
        launch("freeburg.tools.rebuild_fundamentals",
            "--prices",prices,"--fraser-dir",a.fraser_dir,
            "--govinfo-vintages",a.govinfo_vintages,
            "--govinfo-xls-dir",a.govinfo_xls_dir,
            "--output",rebuilt,"--report",out/"fundamental_report.json")
        for s in ("pushen","competitive"):
            path=out/(s+"_events.jsonl")
            launch("freeburg.tools.replay_rebuilt_fundamentals",
                "--sleeve",s,"--fundamentals",rebuilt,
                "--frozen",ROOT/s/"data"/"pit_weekly_inputs.csv",
                "--output",path)
            ledger=out/(s+"_ledger.jsonl")
            replay_script(s,path,ledger)
            report["sleeves"][s]=summarize(ledger)
        report["limitations"].append("Rebuilt fundamentals rely on already extracted FRASER; other macro columns are frozen.")
        report["limitations"].append("No independent original-publication-time verification.")
    else:
        for s in SLEEVES:
            events=ROOT/s/"data"/f"{s}_benchmark_events.jsonl"
            if not events.exists():
                launch(f"freeburg.{s}.build_historical_events")
            ledger=out/(s+"_ledger.jsonl")
            replay_script(s,events,ledger)
            report["sleeves"][s]=summarize(ledger)
        report["limitations"].append("Baseline includes legacy/frozen or separately fetched sources.")
    report["limitations"].append("Heine 3-of-5 remains without exact DJ20 bond/CRB reconstruction.")
    (out/"run_manifest.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
if __name__=="__main__":main()
