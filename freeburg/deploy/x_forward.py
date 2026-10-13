"""Publish weekly Freeburg four-sleeve forward signals to X, safely.

Source of truth: same current captured market/fundamental snapshot + canonical
causaltrader classes + independent matching implementation used by paper
trading. Fail closed on discrepancies or stale data. Default preview only.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
from pathlib import Path
from typing import Callable

NAMES = ("primas", "triple40", "pushen", "competitive")
DISPLAY = {"primas": "Primas", "triple40": "Triple-40",
           "pushen": "Pu Shen", "competitive": "Competitive"}

def validate(state:dict, at:datetime) -> tuple[str,dict[str,int],float]:
    if at.tzinfo is None:
        raise ValueError("aware now required")
    if not state.get("all_data_stages_ok") or state.get("canonical_shadow_agrees") is not True:
        raise ValueError("Missing or divergent live source/strategy stages")
    x, y = state.get("canonical", {}),state.get("shadow", {})
    if x.get("schema") != "freeburg.four.canonical-shadow.v1":
        raise ValueError("No original causaltrader decision")
    if y.get("schema") != "freeburg.four.weekly-shadow.v1":
        raise ValueError("No independent strategy check")
    if x.get("actual_causaltrader_strategy_classes") is not True:
        raise ValueError("Not original strategies")
    if x.get("paper_orders_authorized") is not False:
        raise ValueError("Unexpected decision permissions")
    s=x.get("states", {})
    if set(s)!=set(NAMES) or any(type(s[name]) is not int or s[name] not in (0, 1) for name in NAMES):
        raise ValueError("Missing or nonbinary sleeve states")
    if s != y.get("states") or x.get("decision_friday") != y.get("decision_friday"):
        raise ValueError("Strategy outputs differ")
    weight=sum(s.values())/4
    if x.get("spy_target_weight") != weight or y.get("spy_target_weight") != weight:
        raise ValueError("Portfolio allocation differs")
    day=x["decision_friday"]
    date=datetime.fromisoformat(day).date()
    days=(at.date()-date).days
    if date.weekday()!=4 or days<0 or days>4:
        raise ValueError("Decision not the latest Friday (max 4 days)")
    stamp=datetime.fromisoformat(x["captured_utc"])
    if stamp.tzinfo is None or stamp>at or at-stamp>timedelta(days=4):
        raise ValueError("Current source capture missing/stale")
    if state.get("snapshot") is None or state.get("time") is None:
        raise ValueError("Cannot audit source snapshot")
    return day,s,weight

def format_post(decision_day:str,states:dict[str,int],weight:float,asof:datetime)->str:
    lines=[
       f"Freeburg 4 | week ending {decision_day}",
       " / ".join(f"{DISPLAY[key]} {'ON' if states[key] else 'OFF'}" for key in NAMES[:2]),
       " / ".join(f"{DISPLAY[key]} {'ON' if states[key] else 'OFF'}" for key in NAMES[2:]),
       f"Model allocation: {round(100*weight):d}% SPY / {round(100*(1-weight)):d}% cash",
       f"Observed: {asof.strftime('%d %b %Y')} UTC. Research/paper signals; not investment advice.",
    ]
    message="\n".join(lines)
    if len(message)>280:
        raise ValueError(f"X post exceeds character limit: {len(message)}")
    return message

def send_to_x(content:str)->dict:
    import tweepy
    # Tokens are ONLY fetched in memory. No provider credentials are logged.
    names=("X_API_KEY","X_API_SECRET","X_ACCESS_TOKEN","X_ACCESS_TOKEN_SECRET")
    if any(not os.getenv(name) for name in names):
        raise ValueError("X API user-auth credentials have not been configured")
    client=tweepy.Client(
       consumer_key=os.environ["X_API_KEY"],
       consumer_secret=os.environ["X_API_SECRET"],
       access_token=os.environ["X_ACCESS_TOKEN"],
       access_token_secret=os.environ["X_ACCESS_TOKEN_SECRET"])
    resp=client.create_tweet(text=content,user_auth=True)
    if not resp.data or not resp.data.get("id"):
        raise RuntimeError("X responded without a post ID")
    return {"id":str(resp.data["id"])}

def run(latest:Path,records:Path,*,now:datetime|None=None,
        post:bool=False,api_send:Callable[[str],dict]|None=None)->dict:
    now=now or datetime.now(timezone.utc)
    state=json.loads(latest.read_text())
    day,states,weight=validate(state,now)
    stamp=datetime.fromisoformat(state["canonical"]["captured_utc"])
    msg=format_post(day,states,weight,stamp)
    raw=latest.read_bytes()
    source_dir=Path(state["snapshot"])
    # Strong source binding: record SHA of exact state and both strategies.
    for file in (source_dir/"market/manifest.json",source_dir/"canonical/signal.json",
                 source_dir/"eps/manifest.json",source_dir/"dividends/manifest.json"):
        if not file.is_file():
            raise ValueError(f"Missing auditable original source: {file}")
    provenance={
       "snapshot_manifest_sha256":hashlib.sha256(raw).hexdigest(),
       "original_strategy_signal_sha256":
         hashlib.sha256((source_dir/"canonical/signal.json").read_bytes()).hexdigest(),
       "fundamental_sources":{
         n:hashlib.sha256((source_dir/n/"manifest.json").read_bytes()).hexdigest()
         for n in ("market","eps","dividends")},
    }
    result={
       "schema":"freeburg.x.weekly-post.v1","decision_friday":day,
       "created_utc":now.isoformat(),"model_weight":weight,
       "states":states,"text":msg,"provenance":provenance,
       "posted":False,"status":"DRAFT",
    }
    records.mkdir(parents=True,exist_ok=True)
    drafts=records/"drafts";posts=records/"posts"
    drafts.mkdir(exist_ok=True);posts.mkdir(exist_ok=True)
    target=posts/(day+".json")
    if target.exists():
        prior=json.loads(target.read_text())
        return {**prior,"duplicate_prevented":True}
    # Previews are repeatable; replacing a draft is acceptable, unlike posts.
    tmp=drafts/(day+".tmp")
    tmp.write_text(json.dumps(result,indent=2)+"\n")
    tmp.replace(drafts/(day+".json"))
    if not post:
        return result
    if os.environ.get("X_ENABLE_POSTING")!="YES":
        result["status"]="DRAFT_X_POSTING_NOT_AUTHORIZED"
        return result
    for name in ("X_API_KEY","X_API_SECRET","X_ACCESS_TOKEN","X_ACCESS_TOKEN_SECRET"):
        if not os.getenv(name):
            result["status"]="DRAFT_X_CREDENTIALS_INCOMPLETE"
            return result
    # Claim *before* contacting X. A timeout after publish must not produce
    # duplicate tweets through retries or Monday's recovery timer.
    claimed={**result,"status":"CLAIMED_BEFORE_X_REQUEST"}
    with target.open("x") as f:
        f.write(json.dumps(claimed,indent=2)+"\n")
        f.flush();os.fsync(f.fileno())
    try:
        reply=(api_send or send_to_x)(msg)
        result.update({"status":"POSTED","posted":True,"post_id":str(reply["id"])})
    except Exception as exc:
        result["status"]="POSTING_UNCERTAIN_MANUAL_RECONCILIATION_REQUIRED"
        result["error_type"]=type(exc).__name__
        # Intentional: don't output detailed provider errors that might echo secrets.
    replacement=target.with_suffix(".tmp")
    replacement.write_text(json.dumps(result,indent=2)+"\n")
    replacement.replace(target)
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--latest",type=Path,default=Path("/var/lib/freeburg/captures/latest.json"))
    p.add_argument("--records",type=Path,default=Path("/var/lib/freeburg/x"))
    p.add_argument("--post-if-enabled",action="store_true")
    a=p.parse_args()
    report=run(a.latest,a.records,post=a.post_if_enabled)
    print(json.dumps(report,indent=2))
    if report.get("status")=="POSTING_UNCERTAIN_MANUAL_RECONCILIATION_REQUIRED":
        raise SystemExit(1)

if __name__=="__main__":main()
