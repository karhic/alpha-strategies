"""Heine-inspired modern 3-of-5: LQD, long yield, 3m bill, DJU, DBC.

LQD/DJU/DBC Friday close signals, Fed yields at or before decision Friday.
Next-week LQD adjusted-close return if risk-on, else contemporaneous bill carry.
This is a proxy experiment, NOT exact Heine, and no calibration to outcomes.
"""
from __future__ import annotations
import json,requests, pandas as pd, numpy as np
from pathlib import Path
from datetime import datetime,timezone
from freeburg.primas.build_historical_events import _fed_series
OUT=Path('/tmp/freeburg-heine-v1');OUT.mkdir(exist_ok=True)
def yahoo(ticker):
    import urllib.parse
    u='https://query1.finance.yahoo.com/v8/finance/chart/'+urllib.parse.quote(ticker,safe='')
    r=requests.get(u,params={'period1':1356998400,'period2':1791000000,'interval':'1d','events':'history'},headers={'User-Agent':'Mozilla/5.0'},timeout=55)
    r.raise_for_status();a=r.json()['chart']['result'][0];dates=pd.to_datetime(a['timestamp'],unit='s',utc=True).tz_convert(None).normalize()
    close=pd.Series(a['indicators']['quote'][0]['close'],index=dates,dtype=float).dropna().resample('W-FRI').last().dropna()
    adjusted=pd.Series(a['indicators']['adjclose'][0]['adjclose'],index=dates,dtype=float).dropna().resample('W-FRI').last().dropna()
    return close,adjusted
lqd,lqd_adj=yahoo('LQD');dju,_=yahoo('^DJU');dbc,_=yahoo('DBC')
idx=lqd.index.intersection(dju.index).intersection(dbc.index)
long=_fed_series('RIFLGFCY20_N.WF').reindex(idx).ffill()
bill=_fed_series('RIFSGFSM03_N.WF').reindex(idx).ffill()
x=pd.DataFrame({'lqd':lqd.reindex(idx),'dju':dju.reindex(idx),'dbc':dbc.reindex(idx),'long':long,'bill':bill},index=idx)
f=pd.DataFrame(index=idx)
f['bond']=x.lqd>x.lqd.rolling(24).mean()
f['long_yield']=x.long<x.long.rolling(6).mean()
f['bill_yield']=x.bill<x.bill.rolling(6).mean()
f['utilities']=x.dju>x.dju.rolling(10).mean()
f['commodities']=x.dbc<x.dbc.rolling(20).mean()
x['score']=f.sum(axis=1);x['on']=x.score>=3
x['lqd_return']=lqd_adj.pct_change().shift(-1).reindex(idx)
x['cash_return']=x.bill.clip(lower=0)/5200
x['ret']=np.where(x.on,x.lqd_return,x.cash_return)
x=x.loc['2013-10-04':'2026-08-07'].dropna()
x.to_csv(OUT/'weekly.csv',index_label='date')
r=x.ret; wealth=np.r_[1.,(1+r).cumprod().values]; years=len(r)/52
dd=(wealth/np.maximum.accumulate(wealth)-1).min()
print(json.dumps({'rows':len(x),'first':str(x.index.min().date()),'last':str(x.index.max().date()),'cagr':float(wealth[-1]**(1/years)-1),'max_dd':float(dd),'sharpe_raw':float(r.mean()/r.std()*np.sqrt(52)),'exposure':float(x.on.mean()),'entries':int((x.on&~x.on.shift(1,fill_value=False)).sum()),'annual_returns':{str(k):float((1+g).prod()-1) for k,g in r.groupby(r.index.year)}},indent=2))
