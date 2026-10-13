"""IBKR paper-account preflight, always read-only (no orders)."""
from __future__ import annotations
import argparse,json,os
def preflight(host:str,port:int,client_id:int):
    if port not in (7497,4002):
        raise ValueError("Only standard IBKR paper TWS/Gateway ports allowed")
    try:
        from ib_async import IB
    except ImportError as e:
        raise RuntimeError("Install ib_async in the container for IBKR connectivity") from e
    ib=IB()
    try:
        ib.connect(host,port,clientId=client_id,readonly=True,timeout=12)
        accounts=ib.managedAccounts()
        account_types=[a[:1]+"***"+a[-2:] if len(a)>3 else "***" for a in accounts]
        summary={"connected":ib.isConnected(),"accounts_masked":account_types,
                 "server_version":ib.client.serverVersion(),"read_only":True,
                 "trades_submitted":0,"paper_port":port}
        if not accounts:raise RuntimeError("No accessible account returned by paper API")
        return summary
    finally:
        ib.disconnect()
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--host",default=os.getenv("IBKR_HOST","127.0.0.1"))
    p.add_argument("--port",type=int,default=int(os.getenv("IBKR_PORT","4002")))
    p.add_argument("--client-id",type=int,default=int(os.getenv("IBKR_CLIENT_ID","71")))
    a=p.parse_args()
    print(json.dumps(preflight(a.host,a.port,a.client_id),indent=2))
if __name__=="__main__":main()
