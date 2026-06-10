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
    module_id: str = "heine_3of3"
    module_hash: str | None = None


class SnapshotLike(Protocol):
    timestamp: datetime

    def get(self, key: str) -> Any: ...


@dataclass(frozen=True)
class Heine3Of3:
    """Simplified Heine-style bond timing module.

    Risk-on when all three conditions are true:
        1. BAA yield < 24-week moving average
        2. 10Y Treasury yield < 6-week moving average
        3. 3M T-bill yield < 6-week moving average

    Target:
        risk_on  -> bond_asset at `risk_weight`
        risk_off -> cash_asset at 1.0

    Expected snapshot series, ordered oldest -> newest and containing only
    information available at the snapshot timestamp:
        - "BAA_YIELD"
        - "TREASURY_10Y"
        - "TBILL_3M"

    This module emits target weights only. Financing, synthetic bond return
    construction, duration assumptions, and collateral treatment belong in the
    verifier/accounting layer, not inside the private strategy module.
    """

    baa_key: str = "BAA_YIELD"
    treasury_10y_key: str = "TREASURY_10Y"
    tbill_3m_key: str = "TBILL_3M"
    bond_asset: str = "BAA_BOND"
    cash_asset: str = "TBILL_3M"
    risk_weight: float = 1.0
    baa_lookback: int = 24
    rate_lookback: int = 6

    def evaluate(self, snapshot: SnapshotLike) -> StrategyResponse:
        baa = list(snapshot.get(self.baa_key))
        treasury_10y = list(snapshot.get(self.treasury_10y_key))
        tbill_3m = list(snapshot.get(self.tbill_3m_key))

        if (
            len(baa) < self.baa_lookback
            or len(treasury_10y) < self.rate_lookback
            or len(tbill_3m) < self.rate_lookback
        ):
            return StrategyResponse(
                timestamp=snapshot.timestamp,
                targets=(Target(self.cash_asset, 1.0),),
            )

        baa_now = float(baa[-1])
        treasury_now = float(treasury_10y[-1])
        tbill_now = float(tbill_3m[-1])

        baa_ma = sum(float(x) for x in baa[-self.baa_lookback :]) / self.baa_lookback
        treasury_ma = sum(float(x) for x in treasury_10y[-self.rate_lookback :]) / self.rate_lookback
        tbill_ma = sum(float(x) for x in tbill_3m[-self.rate_lookback :]) / self.rate_lookback

        risk_on = (
            baa_now < baa_ma
            and treasury_now < treasury_ma
            and tbill_now < tbill_ma
        )

        if risk_on:
            return StrategyResponse(
                timestamp=snapshot.timestamp,
                targets=(Target(self.bond_asset, self.risk_weight),),
            )

        return StrategyResponse(
            timestamp=snapshot.timestamp,
            targets=(Target(self.cash_asset, 1.0),),
        )
