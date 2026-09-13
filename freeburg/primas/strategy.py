from __future__ import annotations

from dataclasses import dataclass

from causaltrader import DataEvent, Strategy, StrategyContext, TargetWeight


@dataclass(frozen=True, slots=True)
class PrimasConfig:
    lookback: int = 52
    spx_dataset: str = "index.sp500.level.1w"
    spx_instrument: str = "SPX"
    cp_dataset: str = "rates.commercial_paper.3m.1w"
    cp_instrument: str = "US"
    decision_dataset: str = "clock.weekly.freeburg"
    risk_asset: str = "SPY"
    defensive_asset: str | None = None


class PrimasStrategy(Strategy):
    name = "freeburg_primas"
    version = "1"

    def __init__(self, config: PrimasConfig | None = None) -> None:
        self.config = config or PrimasConfig()

    def on_event(self, ctx: StrategyContext, event: DataEvent):
        cfg = self.config
        if event.dataset != cfg.decision_dataset:
            return ()

        spx = ctx.data.payload_history(
            cfg.spx_dataset,
            cfg.spx_instrument,
            count=cfg.lookback,
        )
        cp = ctx.data.payload_history(
            cfg.cp_dataset,
            cfg.cp_instrument,
            count=cfg.lookback,
        )
        if len(spx) < cfg.lookback or len(cp) < cfg.lookback:
            return ()

        spx_now = float(spx[-1])
        cp_now = float(cp[-1])
        spx_ma = sum(float(x) for x in spx) / cfg.lookback
        cp_ma = sum(float(x) for x in cp) / cfg.lookback
        risk_on = spx_now > spx_ma and cp_now < cp_ma

        reason = (
            f"SPX={spx_now:.6g} MA52={spx_ma:.6g}; "
            f"CP={cp_now:.6g} MA52={cp_ma:.6g}; "
            f"risk_on={risk_on}"
        )
        risk_weight = 1.0 if risk_on else 0.0
        actions = [
            TargetWeight(cfg.risk_asset, risk_weight, tag="primas", reason=reason)
        ]
        if cfg.defensive_asset is not None:
            actions.append(
                TargetWeight(
                    cfg.defensive_asset,
                    1.0 - risk_weight,
                    tag="primas",
                    reason=reason,
                )
            )
        return tuple(actions)
