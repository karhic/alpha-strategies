from __future__ import annotations
from dataclasses import dataclass
from causaltrader import DataEvent, Strategy, StrategyContext, TargetWeight

@dataclass(frozen=True, slots=True)
class CompetitiveConfig:
    lookback:int=24
    threshold:int=2
    tbond_dataset:str="rates.treasury.10y.1w"
    tbill_dataset:str="rates.tbill.3m.1w"
    dividend_yield_dataset:str="fundamentals.sp500.dividend_yield.1w"
    cpi_dataset:str="macro.cpi.1w"
    decision_dataset:str="clock.weekly.freeburg"
    risk_asset:str="SPY"

class CompetitiveStrategy(Strategy):
    name="freeburg_competitive"; version="1"
    def __init__(self,config:CompetitiveConfig|None=None):self.config=config or CompetitiveConfig()
    def on_event(self,ctx:StrategyContext,event:DataEvent):
        c=self.config
        if event.dataset!=c.decision_dataset:return ()
        n=c.lookback+1
        specs=((c.tbond_dataset,"US","tbond"),(c.tbill_dataset,"US","tbill"),(c.dividend_yield_dataset,"SPX","div"),(c.cpi_dataset,"US","cpi"))
        vals={}
        for ds,inst,k in specs:
            h=ctx.data.payload_history(ds,inst,count=n)
            if len(h)<n:return ()
            vals[k]=(float(h[-1]),float(h[0]))
        checks={k:a<b for k,(a,b) in vals.items()}; score=sum(checks.values()); on=score>=c.threshold
        reason="; ".join(f"{k}={a:.6g} lag24={b:.6g} good={checks[k]}" for k,(a,b) in vals.items())+f"; score={score}; risk_on={on}"
        return (TargetWeight(c.risk_asset,1.0 if on else 0.0,tag="competitive",reason=reason),)
