from __future__ import annotations
from dataclasses import dataclass
from causaltrader import DataEvent, Strategy, StrategyContext, TargetWeight

@dataclass(frozen=True, slots=True)
class HeineConfig:
    decision_dataset:str="clock.weekly.freeburg"
    risk_asset:str="TLT"
    threshold:int=3

class HeineStrategy(Strategy):
    """Freeburg slide's actual 3-of-5 Heine rule; data identity caveats live in README."""
    name="freeburg_heine"; version="1"
    def __init__(self,config:HeineConfig|None=None):self.config=config or HeineConfig()
    def _ma_check(self,ctx,ds,inst,n,above):
        h=ctx.data.payload_history(ds,inst,count=n)
        if len(h)<n:return None
        now=float(h[-1]); ma=sum(map(float,h))/n
        return (now>ma if above else now<ma,now,ma)
    def on_event(self,ctx:StrategyContext,event:DataEvent):
        c=self.config
        if event.dataset!=c.decision_dataset:return ()
        specs=(("index.dj20_bond.price.1w","DJCB",24,True,"djcb"),("rates.treasury.long.1w","US",6,False,"tbond"),("rates.tbill.3m.1w","US",6,False,"tbill"),("index.dj_utility.level.1w","DJUA",10,True,"djua"),("index.crb.level.1w","CRB",20,False,"crb"))
        out={}
        for ds,inst,n,above,k in specs:
            x=self._ma_check(ctx,ds,inst,n,above)
            if x is None:return ()
            out[k]=x
        score=sum(int(v[0]) for v in out.values()); on=score>=c.threshold
        reason="; ".join(f"{k}={v[1]:.6g} MA={v[2]:.6g} good={v[0]}" for k,v in out.items())+f"; score={score}; risk_on={on}"
        return (TargetWeight(c.risk_asset,1.0 if on else 0.0,tag="heine",reason=reason),)
