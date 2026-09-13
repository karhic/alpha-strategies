from __future__ import annotations
from dataclasses import dataclass
from causaltrader import DataEvent, Strategy, StrategyContext, TargetWeight

@dataclass(frozen=True, slots=True)
class Triple40Config:
    lookback: int = 40
    spx_dataset: str = "index.sp500.level.1w"
    baa_dataset: str = "rates.moody_baa.1w"
    cp_dataset: str = "rates.commercial_paper.3m.1w"
    decision_dataset: str = "clock.weekly.freeburg"
    risk_asset: str = "SPY"

class Triple40Strategy(Strategy):
    name = "freeburg_triple40"; version = "1"
    def __init__(self, config: Triple40Config|None=None): self.config=config or Triple40Config()
    def on_event(self, ctx: StrategyContext, event: DataEvent):
        c=self.config
        if event.dataset != c.decision_dataset: return ()
        spx=ctx.data.payload_history(c.spx_dataset,"SPX",count=c.lookback)
        baa=ctx.data.payload_history(c.baa_dataset,"US",count=c.lookback)
        cp=ctx.data.payload_history(c.cp_dataset,"US",count=c.lookback)
        if min(map(len,(spx,baa,cp))) < c.lookback: return ()
        sm=sum(map(float,spx))/c.lookback; bm=sum(map(float,baa))/c.lookback; cm=sum(map(float,cp))/c.lookback
        s,b,p=map(float,(spx[-1],baa[-1],cp[-1]))
        on=s>sm and (b<bm or p<cm)
        reason=f"SPX={s:.6g} MA40={sm:.6g}; BAA={b:.6g} MA40={bm:.6g}; CP={p:.6g} MA40={cm:.6g}; risk_on={on}"
        return (TargetWeight(c.risk_asset,1.0 if on else 0.0,tag="triple40",reason=reason),)
