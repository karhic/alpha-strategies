"""
Freeburg-style timing models.

These modules are deliberately small and causal: they consume a Snapshot-like
object containing current and trailing historical observations and return target
weights only.  The verifier/replay layer is responsible for chronology,
financing, fills, dividends, and accounting.

The six reconstructed sleeves are:

1. PrimasV1
2. Triple40
3. Heine3Of5
4. PuShenEarningsYield
5. CompetitiveReturns
6. PrimeDiscountSpread
7. FreeburgSixEqualWeight composite wrapper

Input convention
----------------
The helpers support a forgiving Snapshot interface during early development:
- snapshot.get_series(name) -> sequence/Series-like values ending at now, or
- snapshot.series[name], snapshot.data[name], snapshot[name]

Values should be ordered oldest -> newest.  Current value is the final element.
Moving-average windows are counted in observations supplied by the verifier,
usually weekly bars for the original Freeburg models.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence


Weights = Dict[str, float]


def _series(snapshot: Any, key: str) -> Sequence[float]:
    """Return a trailing series ending at the current observation."""
    if hasattr(snapshot, "get_series"):
        values = snapshot.get_series(key)
        if values is not None:
            return values

    for attr in ("series", "data", "features"):
        obj = getattr(snapshot, attr, None)
        if isinstance(obj, Mapping) and key in obj:
            return obj[key]

    if isinstance(snapshot, Mapping) and key in snapshot:
        return snapshot[key]

    raise KeyError(f"Missing required series: {key}")


def _last(values: Sequence[float]) -> float:
    if len(values) == 0:
        raise ValueError("Empty series")
    return float(values[-1])


def _lag(values: Sequence[float], periods: int) -> float:
    if len(values) <= periods:
        raise ValueError(f"Need at least {periods + 1} observations")
    return float(values[-periods - 1])


def _sma(values: Sequence[float], window: int) -> float:
    if len(values) < window:
        raise ValueError(f"Need at least {window} observations for SMA")
    tail = [float(x) for x in values[-window:]]
    return sum(tail) / window


def _clean(weights: Mapping[str, float]) -> Weights:
    return {k: float(v) for k, v in weights.items() if abs(float(v)) > 1e-12}


@dataclass(frozen=True)
class StrategyResult:
    target_weights: Weights
    diagnostics: Dict[str, Any]


@dataclass(frozen=True)
class PrimasV1:
    """SPX above 52-week MA and commercial paper below 52-week MA."""

    spx_key: str = "SPX"
    commercial_paper_key: str = "COMMERCIAL_PAPER"
    risk_asset: str = "SPX"
    risk_off_asset: str = "COMMERCIAL_PAPER"
    window: int = 52

    def evaluate(self, snapshot: Any) -> StrategyResult:
        spx = _series(snapshot, self.spx_key)
        cp = _series(snapshot, self.commercial_paper_key)
        risk_on = _last(spx) > _sma(spx, self.window) and _last(cp) < _sma(cp, self.window)
        weights = {self.risk_asset: 1.0} if risk_on else {self.risk_off_asset: 1.0}
        return StrategyResult(_clean(weights), {"risk_on": risk_on})


@dataclass(frozen=True)
class Triple40:
    """SPX above 40-week MA and either BAA yield or CP yield below 40-week MA."""

    spx_key: str = "SPX"
    baa_yield_key: str = "BAA_YIELD"
    commercial_paper_key: str = "COMMERCIAL_PAPER"
    risk_asset: str = "SPX"
    risk_off_asset: str = "COMMERCIAL_PAPER"
    window: int = 40

    def evaluate(self, snapshot: Any) -> StrategyResult:
        spx = _series(snapshot, self.spx_key)
        baa = _series(snapshot, self.baa_yield_key)
        cp = _series(snapshot, self.commercial_paper_key)
        risk_on = (
            _last(spx) > _sma(spx, self.window)
            and (_last(baa) < _sma(baa, self.window) or _last(cp) < _sma(cp, self.window))
        )
        weights = {self.risk_asset: 1.0} if risk_on else {self.risk_off_asset: 1.0}
        return StrategyResult(_clean(weights), {"risk_on": risk_on})


@dataclass(frozen=True)
class Heine3Of5:
    """Heine-style 3-of-5 bond-timing proxy.

    A condition is "good" when the current value is below its moving average,
    matching the falling-yield / easing-pressure interpretation used in the
    Freeburg notes.  The strategy owns BAA bonds when at least 3 of 5 conditions
    are good; otherwise it owns T-bills/cash.

    This is still a proxy until exact original Heine inputs are verified.
    """

    baa_yield_key: str = "BAA_YIELD"
    treasury_10y_key: str = "TREASURY_10Y"
    tbill_3m_key: str = "TBILL_3M"
    commercial_paper_key: str = "COMMERCIAL_PAPER"
    cpi_key: str = "CPI"
    risk_asset: str = "BAA_BOND"
    risk_off_asset: str = "TBILL_3M"
    baa_window: int = 24
    treasury_window: int = 6
    tbill_window: int = 6
    cp_window: int = 24
    cpi_window: int = 24
    threshold: int = 3

    def evaluate(self, snapshot: Any) -> StrategyResult:
        checks = {
            "baa_below_ma": _last(_series(snapshot, self.baa_yield_key)) < _sma(_series(snapshot, self.baa_yield_key), self.baa_window),
            "treasury_10y_below_ma": _last(_series(snapshot, self.treasury_10y_key)) < _sma(_series(snapshot, self.treasury_10y_key), self.treasury_window),
            "tbill_3m_below_ma": _last(_series(snapshot, self.tbill_3m_key)) < _sma(_series(snapshot, self.tbill_3m_key), self.tbill_window),
            "commercial_paper_below_ma": _last(_series(snapshot, self.commercial_paper_key)) < _sma(_series(snapshot, self.commercial_paper_key), self.cp_window),
            "cpi_below_ma": _last(_series(snapshot, self.cpi_key)) < _sma(_series(snapshot, self.cpi_key), self.cpi_window),
        }
        score = sum(1 for v in checks.values() if v)
        risk_on = score >= self.threshold
        weights = {self.risk_asset: 1.0} if risk_on else {self.risk_off_asset: 1.0}
        return StrategyResult(_clean(weights), {"risk_on": risk_on, "score": score, "checks": checks})


@dataclass(frozen=True)
class PuShenEarningsYield:
    """Pu Shen earnings-yield spread model.

    Original rule approximation:
    spread = S&P earnings yield - 90-day commercial-paper yield.
    Buy when spread > spread 50 weeks ago and S&P > S&P 50 weeks ago.
    Otherwise hold commercial paper/cash.
    """

    spx_key: str = "SPX"
    earnings_yield_key: str = "EARNINGS_YIELD"
    commercial_paper_key: str = "COMMERCIAL_PAPER"
    risk_asset: str = "SPX"
    risk_off_asset: str = "COMMERCIAL_PAPER"
    lookback: int = 50
    earnings_yield_is_percent: bool = False
    commercial_paper_is_percent: bool = True

    def evaluate(self, snapshot: Any) -> StrategyResult:
        spx = _series(snapshot, self.spx_key)
        ey = [float(x) for x in _series(snapshot, self.earnings_yield_key)]
        cp = [float(x) for x in _series(snapshot, self.commercial_paper_key)]
        ey_scale = 100.0 if self.earnings_yield_is_percent else 1.0
        cp_scale = 100.0 if self.commercial_paper_is_percent else 1.0
        spread_now = ey[-1] / ey_scale - cp[-1] / cp_scale
        spread_then = ey[-self.lookback - 1] / ey_scale - cp[-self.lookback - 1] / cp_scale
        risk_on = spread_now > spread_then and _last(spx) > _lag(spx, self.lookback)
        weights = {self.risk_asset: 1.0} if risk_on else {self.risk_off_asset: 1.0}
        return StrategyResult(_clean(weights), {"risk_on": risk_on, "spread": spread_now, "spread_lag": spread_then})


@dataclass(frozen=True)
class CompetitiveReturns:
    """Competitive returns model.

    Four "good" conditions:
    - T-bond yield below 24 weeks ago
    - T-bill yield below 24 weeks ago
    - S&P dividend yield below 24 weeks ago
    - CPI below 24 weeks ago

    Risk-on when at least two are good, otherwise cash.
    """

    tbond_key: str = "TREASURY_10Y"
    tbill_key: str = "TBILL_3M"
    dividend_yield_key: str = "DIVIDEND_YIELD"
    cpi_key: str = "CPI"
    risk_asset: str = "SPX"
    risk_off_asset: str = "TBILL_3M"
    lookback: int = 24
    threshold: int = 2

    def evaluate(self, snapshot: Any) -> StrategyResult:
        tbond = _series(snapshot, self.tbond_key)
        tbill = _series(snapshot, self.tbill_key)
        divy = _series(snapshot, self.dividend_yield_key)
        cpi = _series(snapshot, self.cpi_key)
        checks = {
            "tbond_lower": _last(tbond) < _lag(tbond, self.lookback),
            "tbill_lower": _last(tbill) < _lag(tbill, self.lookback),
            "dividend_yield_lower": _last(divy) < _lag(divy, self.lookback),
            "cpi_lower": _last(cpi) < _lag(cpi, self.lookback),
        }
        score = sum(1 for v in checks.values() if v)
        risk_on = score >= self.threshold
        weights = {self.risk_asset: 1.0} if risk_on else {self.risk_off_asset: 1.0}
        return StrategyResult(_clean(weights), {"risk_on": risk_on, "score": score, "checks": checks})


@dataclass(frozen=True)
class PrimeDiscountSpread:
    """Prime-rate minus discount-rate spread model.

    Buy when spread < 50-week spread MA and S&P > 50-week S&P MA.
    Otherwise hold T-bills/cash.
    """

    spx_key: str = "SPX"
    prime_rate_key: str = "PRIME_RATE"
    discount_rate_key: str = "DISCOUNT_RATE"
    risk_asset: str = "SPX"
    risk_off_asset: str = "TBILL_3M"
    window: int = 50

    def evaluate(self, snapshot: Any) -> StrategyResult:
        spx = _series(snapshot, self.spx_key)
        prime = [float(x) for x in _series(snapshot, self.prime_rate_key)]
        discount = [float(x) for x in _series(snapshot, self.discount_rate_key)]
        if len(prime) < self.window or len(discount) < self.window:
            raise ValueError(f"Need at least {self.window} observations for prime/discount spread")
        spread = [p - d for p, d in zip(prime[-self.window:], discount[-self.window:])]
        spread_now = spread[-1]
        spread_ma = sum(spread) / self.window
        risk_on = spread_now < spread_ma and _last(spx) > _sma(spx, self.window)
        weights = {self.risk_asset: 1.0} if risk_on else {self.risk_off_asset: 1.0}
        return StrategyResult(_clean(weights), {"risk_on": risk_on, "spread": spread_now, "spread_ma": spread_ma})


@dataclass(frozen=True)
class FreeburgSixEqualWeight:
    """Equal-weight composite of the six reconstructed Freeburg sleeves."""

    sleeves: Optional[Sequence[Any]] = None

    def _sleeves(self) -> Sequence[Any]:
        return self.sleeves or (
            PrimasV1(),
            Triple40(),
            Heine3Of5(),
            PuShenEarningsYield(),
            CompetitiveReturns(),
            PrimeDiscountSpread(),
        )

    def evaluate(self, snapshot: Any) -> StrategyResult:
        sleeves = self._sleeves()
        n = len(sleeves)
        combined: Dict[str, float] = {}
        diagnostics: Dict[str, Any] = {}
        for sleeve in sleeves:
            result = sleeve.evaluate(snapshot)
            name = sleeve.__class__.__name__
            diagnostics[name] = result.diagnostics
            for asset, weight in result.target_weights.items():
                combined[asset] = combined.get(asset, 0.0) + weight / n
        return StrategyResult(_clean(combined), diagnostics)
