"""Compare strategy action weights emitted by the *same* causal runtime."""
from __future__ import annotations
import argparse,json
from pathlib import Path

def compare(baseline:Path,rebuild:Path):
    def actions(path):
        out={}
        with path.open() as fh:
            for line in fh:
                r=json.loads(line)
                if r["kind"]!="strategy_action":continue
                ts=r["timestamp"];v=float(r["payload"]["weight"])
                if ts in out:raise ValueError(f"Duplicate strategy action at {ts}")
                out[ts]=v
        return out
    base=actions(baseline);other=actions(rebuild)
    common=sorted(set(base)&set(other))
    if not common:raise ValueError("No shared strategy decision timestamps")
    changes=[d for d in common if abs(base[d]-other[d])>1e-9]
    return {
        "reference_actions":len(base),"rebuilt_actions":len(other),
        "common_dates":len(common),"different_decisions":len(changes),
        "difference_percent":round(len(changes)*100/len(common),4),
        "missing_in_rebuild":len(set(base)-set(other)),
        "new_in_rebuild":len(set(other)-set(base)),
        "first_differences":changes[:15],
        "status":"EXACT_ACTION_LEDGER_COMPARISON__NOT_A_RETURN_OR_PIT_CERTIFICATION"}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--baseline",type=Path,required=True)
    p.add_argument("--rebuilt",type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(compare(a.baseline,a.rebuilt),indent=2))
if __name__=="__main__":main()
