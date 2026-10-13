"""Inspect the current portable Freeburg research run."""
import json
from pathlib import Path

def main():
    root=Path("/data/captures")
    p=root/"latest.json"
    if not p.is_file():
        print("No captured run yet. Start the container or execute portable_once.")
        raise SystemExit(1)
    x=json.loads(p.read_text())
    c=x.get("canonical",{})
    print("Last capture:",x.get("time"))
    print("All data acquired:",bool(x.get("all_data_stages_ok")))
    print("Original and reference strategy parity:",bool(x.get("canonical_shadow_agrees")))
    if c:
        print("Decision Friday:",c.get("decision_friday"))
        for name,state in c.get("states",{}).items():
            print(f"  {name}: {'ON' if state else 'OFF'}")
        print(f"Model SPY weight: {100*c['spy_target_weight']:.0f}%")
    else:
        for name,z in x.get("stages",{}).items():
            print(name,z)
        print("Canonical error:",x.get("canonical_error","none recorded"))
    print("IBKR orders disabled. X posting disabled.")

if __name__=="__main__":main()
