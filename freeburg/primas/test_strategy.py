from datetime import datetime, timedelta, timezone

from causaltrader import CausalDataStore, DataEvent, SimBroker
from causaltrader.account import AccountView
from causaltrader.clock import ReplayClock
from causaltrader.state import MemoryState
from causaltrader.strategy import StrategyContext

from freeburg.primas.strategy import PrimasStrategy

UTC = timezone.utc


def make_ctx(events, now):
    clock = ReplayClock(now)
    data = CausalDataStore(clock, events)
    return StrategyContext(data, AccountView(SimBroker()), MemoryState(), now)


def weekly_events(start, values, dataset, instrument, available_shift_days=0):
    out = []
    for i, value in enumerate(values):
        t = start + timedelta(days=7 * i)
        out.append(
            DataEvent(
                source="test",
                dataset=dataset,
                instrument=instrument,
                event_time=t,
                available_at=t + timedelta(days=available_shift_days),
                payload=float(value),
            )
        )
    return out


def decision_event(t):
    return DataEvent("test", "clock.weekly.freeburg", None, t, t, None)


def risk_weight(actions):
    return actions[0].weight


def test_primas_requires_both_conditions():
    start = datetime(2025, 1, 3, tzinfo=UTC)
    spx = weekly_events(start, [100.0] * 51 + [110.0], "index.sp500.level.1w", "SPX")
    cp_good = weekly_events(start, [5.0] * 51 + [4.0], "rates.commercial_paper.3m.1w", "US")
    cp_bad = weekly_events(start, [5.0] * 51 + [6.0], "rates.commercial_paper.3m.1w", "US")
    now = spx[-1].available_at
    strat = PrimasStrategy()

    assert risk_weight(strat.on_event(make_ctx(spx + cp_good, now), decision_event(now))) == 1.0
    assert risk_weight(strat.on_event(make_ctx(spx + cp_bad, now), decision_event(now))) == 0.0


def test_future_cp_is_invisible():
    start = datetime(2025, 1, 3, tzinfo=UTC)
    spx = weekly_events(start, [100.0] * 51 + [110.0], "index.sp500.level.1w", "SPX")
    cp = weekly_events(start, [5.0] * 51 + [4.0], "rates.commercial_paper.3m.1w", "US")
    now = cp[-1].available_at
    future_t = now + timedelta(days=7)
    future = DataEvent(
        "test",
        "rates.commercial_paper.3m.1w",
        "US",
        future_t,
        future_t,
        1_000_000.0,
    )
    actions = PrimasStrategy().on_event(make_ctx(spx + cp + [future], now), decision_event(now))
    assert risk_weight(actions) == 1.0


def test_non_decision_events_do_nothing():
    now = datetime(2026, 1, 2, tzinfo=UTC)
    ctx = make_ctx([], now)
    event = DataEvent("test", "index.sp500.level.1w", "SPX", now, now, 100.0)
    assert PrimasStrategy().on_event(ctx, event) == ()
