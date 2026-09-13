from datetime import datetime,timedelta,timezone
from causaltrader import CausalDataStore,DataEvent,SimBroker
from causaltrader.account import AccountView
from causaltrader.clock import ReplayClock
from causaltrader.state import MemoryState
from causaltrader.strategy import StrategyContext
from freeburg.triple40.strategy import Triple40Strategy
from freeburg.pushen.strategy import PuShenStrategy
from freeburg.competitive.strategy import CompetitiveStrategy
from freeburg.prime_discount.strategy import PrimeDiscountStrategy
from freeburg.heine.strategy import HeineStrategy
UTC=timezone.utc

def events(ds,inst,vals,start=datetime(2025,1,3,tzinfo=UTC)):
 return [DataEvent('test',ds,inst,start+timedelta(days=7*i),start+timedelta(days=7*i),float(v)) for i,v in enumerate(vals)]
def ctx(ev,now):
 c=ReplayClock(now); return StrategyContext(CausalDataStore(c,ev),AccountView(SimBroker()),MemoryState(),now)
def dec(now): return DataEvent('test','clock.weekly.freeburg',None,now,now,None)
def w(strat,ev):
 now=max(x.available_at for x in ev); return strat.on_event(ctx(ev,now),dec(now))[0].weight

def test_triple40_or_branch():
 ev=events('index.sp500.level.1w','SPX',[100]*39+[110])+events('rates.moody_baa.1w','US',[6]*40)+events('rates.commercial_paper.3m.1w','US',[5]*39+[4])
 assert w(Triple40Strategy(),ev)==1

def test_pushen_lag_rule():
 ev=events('index.sp500.level.1w','SPX',[100]+[105]*49+[110])+events('fundamentals.sp500.earnings_yield.1w','SPX',[5]+[5]*49+[8])+events('rates.commercial_paper.3m.1w','US',[4]*51)
 assert w(PuShenStrategy(),ev)==1

def test_competitive_two_of_four():
 ev=[]
 ev+=events('rates.treasury.10y.1w','US',[5]+[5]*23+[4])
 ev+=events('rates.tbill.3m.1w','US',[4]+[4]*23+[3])
 ev+=events('fundamentals.sp500.dividend_yield.1w','SPX',[2]*25)
 ev+=events('macro.cpi.1w','US',[100]*25)
 assert w(CompetitiveStrategy(),ev)==1

def test_prime_discount_rule():
 ev=events('index.sp500.level.1w','SPX',[100]*49+[110])+events('rates.bank_prime.1w','US',[8]*50)+events('rates.discount_rate.1w','US',[5]*49+[6])
 assert w(PrimeDiscountStrategy(),ev)==1

def test_heine_actual_three_of_five():
 ev=[]
 ev+=events('index.dj20_bond.price.1w','DJCB',[100]*23+[110])
 ev+=events('rates.treasury.long.1w','US',[5]*5+[4])
 ev+=events('rates.tbill.3m.1w','US',[5]*5+[4])
 ev+=events('index.dj_utility.level.1w','DJUA',[100]*10)
 ev+=events('index.crb.level.1w','CRB',[100]*20)
 assert w(HeineStrategy(),ev)==1

def test_future_event_invisible_for_triple40():
 base=events('index.sp500.level.1w','SPX',[100]*39+[110])+events('rates.moody_baa.1w','US',[6]*40)+events('rates.commercial_paper.3m.1w','US',[5]*39+[4])
 now=max(x.available_at for x in base)
 fut=DataEvent('test','rates.commercial_paper.3m.1w','US',now+timedelta(days=7),now+timedelta(days=7),999.)
 assert Triple40Strategy().on_event(ctx(base+[fut],now),dec(now))[0].weight==1
