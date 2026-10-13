"""Freeburg autonomous PAPER-only SPY rebalance with external SPY price.

Runs at most once per completed Friday decision, during NY stock hours.
Only accepts *matching* actual-causaltrader and independent live-source
shadow decisions. Never routes to a real-money account.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timedelta, time, timezone
import hashlib
import json
import math
import os
from pathlib import Path
from zoneinfo import ZoneInfo
import requests
import pandas as pd

from freeburg.deploy.ibkr_paper import plan

NY=ZoneInfo("America/New_York")
SPY_URL="https://query1.finance.yahoo.com/v8/finance/chart/SPY"
NAMES={"primas","triple40","pushen","competitive"}
def validate_capture(state:dict, now:datetime)->tuple[str,float]:
    if not state.get("all_data_stages_ok"):raise ValueError("Data capture incomplete")
    if not state.get("canonical_shadow_agrees"):raise ValueError("Causal engine signal parity failed")
    c=state.get("canonical",{})
    s=state.get("shadow",{})
    if c.get("schema")!="freeburg.four.canonical-shadow.v1" or s.get("schema")!="freeburg.four.weekly-shadow.v1":
        raise ValueError("Signals absent/unknown")
    if set(c.get("states",{}))!=NAMES or c["states"]!=s.get("states"):
        raise ValueError("Unmatched sleeve outputs")
    if c.get("actual_causaltrader_strategy_classes") is not True:
        raise ValueError("Unverified original strategy execution")
    if c.get("paper_orders_authorized") is not False or c.get("spy_target_weight")!=s.get("spy_target_weight"):
        raise ValueError("Signal schema inconsistent")
    friday=c.get("decision_friday")
    if friday!=s.get("decision_friday") or c.get("spy_target_weight") not in (0,.25,.5,.75,1):
        raise ValueError("Invalid decision date/exposure")
    d=pd.Timestamp(friday)
    if d.weekday()!=4 or d.date()>now.date() or (now.date()-d.date()).days>4:
        raise ValueError("No sufficiently recent completed Friday decision")
    t=datetime.fromisoformat(c["captured_utc"])
    if t.tzinfo is None or now<t or now-t>timedelta(days=5):
        raise ValueError("Source capture stale, naive, or future")
    if sum(c["states"].values())/4!=c["spy_target_weight"]:
        raise ValueError("Inconsistent sleeve allocation")
    return friday,float(c["spy_target_weight"])

def spy_price(now:datetime,*,session=None)->tuple[float,str]:
    req=session or requests
    r=req.get(SPY_URL,params={"range":"1d","interval":"1m"},
              headers={"User-Agent":"Mozilla/5.0 Freeburg paper-price/0.1"},timeout=20)
    r.raise_for_status()
    data=r.json()["chart"]["result"][0]
    times=data["timestamp"]
    values=data["indicators"]["quote"][0]["close"]
    rows=[(datetime.fromtimestamp(x,timezone.utc),float(v)) for x,v in zip(times,values)
          if v is not None and math.isfinite(float(v)) and float(v)>0 and
          datetime.fromtimestamp(x,timezone.utc)<=now]
    if not rows:raise ValueError("No SPY intraday market price")
    at,price=rows[-1]
    if now-at>timedelta(minutes=25):
        raise ValueError(f"SPY external intraday quote too old: {at.isoformat()}")
    if at.astimezone(NY).date()!=now.astimezone(NY).date():
        raise ValueError("External SPY quote from previous trading session")
    return price,at.isoformat()

def in_trade_window(now:datetime)->bool:
    t=now.astimezone(NY)
    return t.weekday()<5 and time(9,45)<=t.time()<time(15,45)

def execute(latest:Path,record_dir:Path, *,send=False,now:datetime|None=None)->dict:
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:raise ValueError("UTC-aware timestamp required")
    if not in_trade_window(now):
        raise ValueError("Paper rebalancer must run between 09:45–15:45 New York time")
    state=json.loads(latest.read_text())
    decision,weight=validate_capture(state,now)
    # All account reconciliation happens on an authenticated API connection.
    # Price is the external Yahoo SPY quote, NOT an IBKR subscription.
    price,price_at=spy_price(now)
    from ib_async import IB,Stock,MarketOrder
    ib=IB()
    try:
        ib.connect("127.0.0.1",4002,clientId=93,readonly=not send,timeout=12)
        accounts=ib.managedAccounts()
        if len(accounts)!=1 or not accounts[0].startswith("DU"):
            raise ValueError("Exactly one IBKR paper DU account required")
        account=accounts[0]
        contracts=ib.qualifyContracts(Stock("SPY","SMART","USD"))
        if len(contracts)!=1 or contracts[0].symbol!="SPY":
            raise ValueError("SPY stock contract ambiguous")
        contract=contracts[0]
        positions=ib.positions(account)
        if any(p.contract.symbol=="SPY" and p.contract.conId!=contract.conId for p in positions):
            raise ValueError("Other SPY contract detected")
        shares=sum(p.position for p in positions if p.contract.conId==contract.conId)
        summary=ib.accountSummary(account)
        def metric(tag):
            vals=[float(v.value) for v in summary if v.tag==tag and v.currency in ("USD","BASE")]
            if not vals or not math.isfinite(vals[0]):raise ValueError(f"Missing {tag} account metric")
            return vals[0]
        equity=metric("NetLiquidation")
        # Request open orders from all API client IDs, not only this process.
        all_orders=ib.reqAllOpenOrders()
        if any(t.contract.conId==contract.conId and not t.isDone() for t in all_orders):
            raise ValueError("Open SPY order: refuse to duplicate")
        trade=plan(target_weight=weight,net_liquidation=equity,spy_price=price,
                   spy_position=shares,max_trade_fraction=.30)
        if trade["action"]=="BUY":
            if trade["estimated_notional"]>metric("AvailableFunds"):
                raise ValueError("Not enough free paper buying power")
        status={"mode":"IBKR_PAPER_ONLY","source_decision_friday":decision,
            "observed_at_utc":now.isoformat(),"source_snapshot":state.get("snapshot"),
            "original_and_shadow_agree":True,"target_weight":weight,
            "external_spy_price":price,"quote_at":price_at,
            "account_masked":"D***"+account[-2:],
            "trade_plan":trade,"order_submitted":False}
        if not send:return status
        if os.getenv("FREEBURG_PAPER_SEND")!="YES":
            raise ValueError("FREEBURG_PAPER_SEND=YES required")
        record_dir.mkdir(parents=True,exist_ok=True)
        path=record_dir/(decision+".json")
        # Claim before sending. On a crash/timeout, manual reconciliation is
        # required, rather than risking a duplicate full rebalance.
        claim={**status,"state":"CLAIMED_BEFORE_SEND"}
        with path.open("x") as f:
            f.write(json.dumps(claim,indent=2)+"\n")
            f.flush();os.fsync(f.fileno())
        if trade["quantity"]:
            ref="FreeburgPaper-"+decision.replace("-","")
            trade_obj=ib.placeOrder(contract,MarketOrder(
                trade["action"],int(trade["quantity"]),account=account,
                orderRef=ref,tif="DAY",outsideRth=False))
            status["order_submitted"]=True
            status["ib_order_id"]=trade_obj.order.orderId
            status["order_reference"]=ref
            ib.sleep(3)
            status["ib_status"]=trade_obj.orderStatus.status
            status["filled"]=trade_obj.orderStatus.filled
        else:
            status["ib_status"]="NO_ORDER_NEEDED"
        status["state"]="SENT_OR_NOOP"
        # A write can fail after an order; the preclaim still prevents retry.
        tmp=path.with_suffix(".tmp")
        tmp.write_text(json.dumps(status,indent=2)+"\n")
        tmp.replace(path)
        return status
    finally:
        ib.disconnect()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--latest",type=Path,default=Path("/var/lib/freeburg/captures/latest.json"))
    p.add_argument("--records",type=Path,default=Path("/var/lib/freeburg/paper_runs"))
    p.add_argument("--send-paper",action="store_true")
    a=p.parse_args()
    result=execute(a.latest,a.records,send=a.send_paper)
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
