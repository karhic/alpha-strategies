from __future__ import annotations
from dataclasses import dataclass
from causaltrader import DataEvent, Strategy, StrategyContext, TargetWeight

@dataclass(frozen=True, slots=True)
class PuShenConfig:
    lookback: int = 50
    spx_dataset: str = "index.sp500.level.1w"
    earnings_yield_dataset: str = "fundamentals.sp500.earnings_yield.1w"
    cp_dataset: str = "rates.commercial_paper.3m.1w"
    decision_dataset: str = "clock.weekly.freeburg"
    risk_asset: str = "SPY"

class PuShenStrategy(Strategy):
    name="freeburg_pushen"; version="1"
    def __init__(self,config:PuShenConfig|None=None): self.config=config or PuShenConfig()
    def on_event(self,ctx:StrategyContext,event:DataEvent):
        c=self.config
        if event.dataset!=c.decision_dataset:return ()
        n=c.lookback+1
        spx=ctx.data.payload_history(c.spx_dataset,"SPX",count=n)
        ey=ctx.data.payload_history(c.earnings_yield_dataset,"SPX",count=n)
        cp=ctx.data.payload_history(c.cp_dataset,"US",count=n)
        if min(map(len,(spx,ey,cp)))<n:return ()
        sn,so=float(spx[-1]),float(spx[0]); spread=float(ey[-1])-float(cp[-1]); old=float(ey[0])-float(cp[0])
        on=spread>old and sn>so
        reason=f"spread={spread:.6g} lag50={old:.6g}; SPX={sn:.6g} lag50={so:.6g}; risk_on={on}"
        return (TargetWeight(c.risk_asset,1.0 if on else 0.0,tag="pushen",reason=reason),)
