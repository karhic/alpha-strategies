from __future__ import annotations
from dataclasses import dataclass
from causaltrader import DataEvent, Strategy, StrategyContext, TargetWeight

@dataclass(frozen=True, slots=True)
class PrimeDiscountConfig:
    lookback:int=50
    spx_dataset:str="index.sp500.level.1w"
    prime_dataset:str="rates.bank_prime.1w"
    discount_dataset:str="rates.discount_rate.1w"
    decision_dataset:str="clock.weekly.freeburg"
    risk_asset:str="SPY"

class PrimeDiscountStrategy(Strategy):
    name="freeburg_prime_discount"; version="1"
    def __init__(self,config:PrimeDiscountConfig|None=None):self.config=config or PrimeDiscountConfig()
    def on_event(self,ctx:StrategyContext,event:DataEvent):
        c=self.config
        if event.dataset!=c.decision_dataset:return ()
        spx=ctx.data.payload_history(c.spx_dataset,"SPX",count=c.lookback)
        prime=ctx.data.payload_history(c.prime_dataset,"US",count=c.lookback)
        disc=ctx.data.payload_history(c.discount_dataset,"US",count=c.lookback)
        if min(map(len,(spx,prime,disc)))<c.lookback:return ()
        spread=[float(p)-float(d) for p,d in zip(prime,disc)]; sm=sum(spread)/c.lookback; s=spread[-1]
        px=float(spx[-1]); pm=sum(map(float,spx))/c.lookback; on=s<sm and px>pm
        reason=f"spread={s:.6g} MA50={sm:.6g}; SPX={px:.6g} MA50={pm:.6g}; risk_on={on}"
        return (TargetWeight(c.risk_asset,1.0 if on else 0.0,tag="prime_discount",reason=reason),)
