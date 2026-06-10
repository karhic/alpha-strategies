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
    module_id: str = "pu_shen_earnings_yield"
    module_hash: str | None = None


class SnapshotLike(Protocol):
    timestamp: datetime

    def get(self, key: str) -> Any: ...


@dataclass(frozen=True)
class PuShenEarningsYield:
    """Pu Shen / Freeburg-style earnings-yield timing module.

    Monthly Shiller approximation of the slide rule:

        spread = S&P earnings yield - 90-day commercial-paper yield

        risk_on = spread_now > spread_12_months_ago
                  AND
                  SPX_now > SPX_12_months_ago

    The original slide uses weekly S&P earnings yield and 50-week comparisons.
    This module is the monthly approximation, with 12 months used as the
    50-week proxy.

    Expected snapshot series, ordered oldest -> newest and containing only
    information available at the snapshot timestamp:
        - "SPX"
        - "EARNINGS_YIELD"
        - "COMMERCIAL_PAPER"

    Units:
        - EARNINGS_YIELD may be decimal (0.045) or percent (4.5). Set
          `earnings_yield_is_percent` accordingly.
        - COMMERCIAL_PAPER may be percent by default (4.5). Set
          `commercial_paper_is_percent` accordingly.

    Target:
        risk_on  -> equity_asset at risk_weight
        risk_off -> defensive_asset at 1.0

    Return construction, dividends, cash carry, financing, and exact data
    release lags belong in the verifier/accounting layer.
    """

    spx_key: str = "SPX"
    earnings_yield_key: str = "EARNINGS_YIELD"
    cp_key: str = "COMMERCIAL_PAPER"
    equity_asset: str = "SPX"
    defensive_asset: str = "COMMERCIAL_PAPER"
    lookback: int = 12
    risk_weight: float = 1.0
    earnings_yield_is_percent: bool = False
    commercial_paper_is_percent: bool = True

    def evaluate(self, snapshot: SnapshotLike) -> StrategyResponse:
        spx = list(snapshot.get(self.spx_key))
        earnings_yield = list(snapshot.get(self.earnings_yield_key))
        cp = list(snapshot.get(self.cp_key))

        required = self.lookback + 1
        if len(spx) < required or len(earnings_yield) < required or len(cp) < required:
            return StrategyResponse(
                timestamp=snapshot.timestamp,
                targets=(Target(self.defensive_asset, 1.0),),
            )

        spx_now = float(spx[-1])
        spx_then = float(spx[-1 - self.lookback])

        ey_now = float(earnings_yield[-1])
        ey_then = float(earnings_yield[-1 - self.lookback])
        cp_now = float(cp[-1])
        cp_then = float(cp[-1 - self.lookback])

        if self.earnings_yield_is_percent:
            ey_now /= 100.0
            ey_then /= 100.0
        if self.commercial_paper_is_percent:
            cp_now /= 100.0
            cp_then /= 100.0

        spread_now = ey_now - cp_now
        spread_then = ey_then - cp_then

        risk_on = (spread_now > spread_then) and (spx_now > spx_then)

        if risk_on:
            return StrategyResponse(
                timestamp=snapshot.timestamp,
                targets=(Target(self.equity_asset, self.risk_weight),),
            )

        return StrategyResponse(
            timestamp=snapshot.timestamp,
            targets=(Target(self.defensive_asset, 1.0),),
        )
