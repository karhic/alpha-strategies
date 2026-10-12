"""IBKR SPY paper-trading order planner and *explicitly gated* executor.

No automatic live account access. Paper-only ports, account starts DU, dry run
is default. Generates one rebalancing order for a previously audited signal.
"""
from __future__ import annotations
import argparse,json,math,os
from datetime import datetime,timezone,timedelta
from pathlib import Path

def plan(*,target_weight:float,net_liquidation:float,spy_price:float,spy_position:int,
         open_spy_orders:int=0,max_trade_fraction:float=1.0)->dict:
    if target_weight not in (0,.25,.5,.75,1):raise ValueError("Unexpected target fraction")
    if not all(math.isfinite(z) and z>0 for z in (net_liquidation,spy_price)):raise ValueError("Invalid equity or price")
    if int(spy_position)!=spy_position or spy_position<0:raise ValueError("Long-only whole-share SPY account")
    if open_spy_orders:raise ValueError("Open SPY orders exist: refuse duplicate rebalance")
    if not 0<max_trade_fraction<=1:raise ValueError("Invalid trade ceiling")
    target_shares=int(net_liquidation*target_weight/spy_price)
    delta=target_shares-int(spy_position)
    if abs(delta)*spy_price > max_trade_fraction*net_liquidation+1e-6:
        raise ValueError("Order exceeds configured account trade limit")
    return {"target_weight":target_weight,"target_shares":target_shares,
            "current_shares":int(spy_position),"delta":delta,
            "action":"BUY" if delta>0 else "SELL" if delta<0 else "HOLD",
            "quantity":abs(delta),"estimated_notional":abs(delta)*spy_price}

def read_signal(path:Path)->dict:
    x=json.loads(path.read_text())
    # Only accept one of the signal system's committed ledger-derived schemas.
    if x.get("schema")!="freeburg.four.weekly-signal.v1":raise ValueError("Unrecognized signal schema")
    w=x.get("spy_target_weight")
    if w not in (0,.25,.5,.75,1) or sum(x.get("risk_on",{}).values())/4!=w:
        raise ValueError("Invalid or inconsistent signal allocation")
    if x.get("execution_enabled") is not False:raise ValueError("Signal must retain execution-disabled label")
    return x

def broker_preflight(host:str,port:int,client_id:int,*,send:bool,account_confirm:str):
    if port not in (4002,7497):raise ValueError("Paper-only API ports 4002/7497")
    from ib_async import IB,Stock,MarketOrder
    ib=IB()
    try:
        ib.connect(host,port,clientId=client_id,readonly=not send,timeout=12)
        accounts=ib.managedAccounts()
        if len(accounts)!=1 or not accounts[0].startswith("DU"):
            raise ValueError("Single IBKR paper account starting DU required")
        account=accounts[0]
        if send and account_confirm!=account:raise ValueError("Explicit account confirmation mismatch")
        contracts=ib.qualifyContracts(Stock("SPY","SMART","USD"))
        if len(contracts)!=1 or contracts[0].symbol!="SPY":raise RuntimeError("SPY contract qualification failed")
        contract=contracts[0]
        summary=ib.accountSummary(account)
        def metric(key):
            vals=[v for v in summary if v.tag==key and v.currency in ("USD","BASE")]
            if not vals:raise ValueError("Missing IBKR account metric "+key)
            return float(vals[0].value)
        equity=metric("NetLiquidation")
        positions=ib.positions(account)
        if any(p.contract.symbol=="SPY" and p.contract.conId!=contract.conId for p in positions):
            raise ValueError("Ambiguous nonmatching SPY positions")
        position=sum(p.position for p in positions if p.contract.conId==contract.conId)
        if position!=int(position) or position<0:raise ValueError("Fractional/short SPY position unsupported")
        open_orders=sum(1 for trade in ib.openTrades() if trade.contract.conId==contract.conId
                        and not trade.isDone())
        ticker=ib.reqTickers(contract)[0]
        # Market snapshots may be absent without subscription. Do not assume stale last.
        midpoint=((ticker.bid+ticker.ask)/2 if (ticker.bid and ticker.ask and
                 math.isfinite(ticker.bid) and math.isfinite(ticker.ask) and
                 ticker.bid>0 and ticker.ask>=ticker.bid) else None)
        price=midpoint if midpoint is not None else ticker.marketPrice()
        if price is None or not math.isfinite(price) or price<=0:
            raise ValueError("No valid market snapshot; cannot size SPY order")
        return ib,contract,account,equity,int(position),open_orders,float(price),MarketOrder
    except BaseException:
        ib.disconnect()
        raise

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--signal",required=True,type=Path)
    p.add_argument("--host",default=os.getenv("IBKR_HOST","127.0.0.1"))
    p.add_argument("--port",type=int,default=int(os.getenv("IBKR_PORT","4002")))
    p.add_argument("--client-id",type=int,default=79)
    p.add_argument("--send-paper-order",action="store_true",help="Opt-in actual IBKR paper order")
    p.add_argument("--confirm-account",default="",help="Full DU paper account ID when sending")
    p.add_argument("--confirm-trading",default="",help="Must equal PAPER_ONLY")
    p.add_argument("--max-trade-fraction",type=float,default=1.0)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    if a.output.exists():raise FileExistsError(a.output)
    signal=read_signal(a.signal)
    decision_at=datetime.fromisoformat(signal["decision_at"])
    if decision_at.tzinfo is None or decision_at>datetime.now(timezone.utc):
        raise ValueError("Signal decision timestamp invalid")
    if a.send_paper_order and datetime.now(timezone.utc)-decision_at>timedelta(days=8):
        raise ValueError("Cannot send stale weekly paper signal")
    if a.send_paper_order and (a.confirm_trading!="PAPER_ONLY" or os.getenv("IBKR_PAPER_ORDERS")!="YES"):
        raise ValueError("Set IBKR_PAPER_ORDERS=YES and --confirm-trading PAPER_ONLY")
    ib,contract,account,equity,held,opened,price,MarketOrder=broker_preflight(
        a.host,a.port,a.client_id,send=a.send_paper_order,account_confirm=a.confirm_account)
    try:
        result=plan(target_weight=signal["spy_target_weight"],net_liquidation=equity,
                    spy_price=price,spy_position=held,open_spy_orders=opened,
                    max_trade_fraction=a.max_trade_fraction)
        result.update({"mode":"IBKR_PAPER","account_masked":account[:1]+"***"+account[-2:],
                       "signal_decision_at":signal["decision_at"],"market_price_snapshot":price,
                       "order_submitted":False})
        if a.send_paper_order and result["quantity"]:
            trade=ib.placeOrder(contract,MarketOrder(result["action"],result["quantity"],
                                                   account=account))
            result["order_submitted"]=True
            result["ib_order_id"]=trade.order.orderId
            ib.sleep(2)
            result["order_status"]=trade.orderStatus.status
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(json.dumps(result,indent=2)+"\n")
        print(json.dumps(result,indent=2))
    finally:ib.disconnect()
if __name__=="__main__":main()
