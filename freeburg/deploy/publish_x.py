"""Render Freeburg weekly signals for X; opt-in posting only."""
from __future__ import annotations
import argparse,hashlib,json,os
from pathlib import Path
from datetime import datetime,timezone
from freeburg.deploy.signals import build,SLEEVES

def render(snapshot:dict)->str:
    on=sum(snapshot["risk_on"].values())
    labels=", ".join(f"{s} {'ON' if snapshot['risk_on'][s] else 'OFF'}" for s in SLEEVES)
    return (f"Freeburg 4 | {snapshot['decision_at'][:10]} UTC\n"
            f"Risk-on sleeves: {on}/4 | Model SPY exposure: {on*25}%\n"
            f"{labels}\n"
            "Research signals only. Not investment advice. Source release timing not fully audited.")
def main():
    a=argparse.ArgumentParser()
    a.add_argument("--ledger-dir",type=Path,required=True)
    a.add_argument("--output-dir",type=Path,required=True)
    a.add_argument("--post",action="store_true",help="Explicitly authorize a real X post; never default")
    a.add_argument("--asof",help="ISO UTC timestamp for testing; leave unset for now")
    opt=a.parse_args()
    now=datetime.fromisoformat(opt.asof.replace("Z","+00:00")) if opt.asof else datetime.now(timezone.utc)
    snap=build(opt.ledger_dir,now)
    content=render(snap)
    if len(content)>280:raise ValueError("Exceeds X character limit")
    opt.output_dir.mkdir(parents=True,exist_ok=True)
    marker=hashlib.sha256(snap["decision_at"].encode()).hexdigest()[:20]
    path=opt.output_dir/(marker+".json")
    if path.exists():raise FileExistsError("This decision was previously prepared: "+str(path))
    # Never allow offline test clock to send a real tweet.
    if opt.post and opt.asof:raise ValueError("Historical or synthetic asof cannot post")
    if opt.post:
        if os.getenv("X_ENABLE_POSTING")!="YES":
            raise RuntimeError("X_ENABLE_POSTING=YES required for posting")
        import tweepy
        client=tweepy.Client(consumer_key=os.environ["X_API_KEY"],
            consumer_secret=os.environ["X_API_SECRET"],
            access_token=os.environ["X_ACCESS_TOKEN"],
            access_token_secret=os.environ["X_ACCESS_TOKEN_SECRET"])
        resp=client.create_tweet(text=content,user_auth=True)
        status="POSTED";post_id=str(resp.data["id"])
    else:status="DRAFT_ONLY";post_id=None
    obj={"status":status,"id":post_id,"text":content,"source":snap}
    path.write_text(json.dumps(obj,indent=2)+"\n")
    print(json.dumps({"status":status,"text":content,"out":str(path)},indent=2))
if __name__=="__main__":main()
