from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol


@dataclass(frozen=True)
class Target:
    asset: str
    weight: float


@dataclass(frozen=True)
class StrategyResponse:
    timestamp: datetime
    targets: tuple[Target, ...]
    module_id: str = "primas_v1"
    module_hash: str | None = None


class SnapshotLike(Protocol):
    timestamp: datetime

    def get(self, key: str) -> Any: ...


@dataclass(frozen=True)
class PrimasV1:
    """Primas-style equity/commercial-paper timing module.

    Rule:
        risk_on = SPX > 52-week MA AND commercial paper < 52-week MA

    Target:
        risk_on  -> 100% SPX
        risk_off -> 100% commercial paper / cash-equivalent

    The module expects the snapshot to provide historical series under:
        - "SPX"
        - "COMMERCIAL_PAPER"

    Each series should be ordered oldest -> newest and contain only information
    available at the snapshot timestamp.
    """

    lookback: int = 52
    spx_key: str = "SPX"
    cp_key: str = "COMMERCIAL_PAPER"
    risk_asset: str = "SPX"
    defensive_asset: str = "COMMERCIAL_PAPER"

    def evaluate(self, snapshot: SnapshotLike) -> StrategyResponse:
        spx = list(snapshot.get(self.spx_key))
        cp = list(snapshot.get(self.cp_key))

        if len(spx) < self.lookback or len(cp) < self.lookback:
            return StrategyResponse(
                timestamp=snapshot.timestamp,
                targets=(Target(self.defensive_asset, 1.0),),
            )

        spx_now = float(spx[-1])
        cp_now = float(cp[-1])
        spx_ma = sum(float(x) for x in spx[-self.lookback :]) / self.lookback
        cp_ma = sum(float(x) for x in cp[-self.lookback :]) / self.lookback

        risk_on = (spx_now > spx_ma) and (cp_now < cp_ma)
        target_asset = self.risk_asset if risk_on else self.defensive_asset
        return StrategyResponse(timestamp=snapshot.timestamp, targets=(Target(target_asset, 1.0),))
