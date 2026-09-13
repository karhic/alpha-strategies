# Heine Bond Model

The actual Freeburg slide rule is a 3-of-5 bond-timing model. A condition is `Good` when:

1. Dow Jones 20 Bond Average (DJCB) > 24-week moving average
2. long Treasury yield < 6-week moving average
3. 90-day T-bill yield < 6-week moving average
4. Dow Jones Utility Average > 10-week moving average
5. CRB index < 20-week moving average

Own bonds when at least **3 of 5** are Good; otherwise cash/T-bills.

## Published result

Freeburg reports **11.5% CAGR / -4.8% max drawdown** since 1970.

## Reconstruction status

The rule itself is reconstructed exactly. The principal unresolved input is the historical **Dow Jones 20 Bond Average / DJ20BNX** price/return path.

A public-source proxy reconstruction using a digitized Dow Jones bond chart through 2001 and a Treasury-derived splice afterward produced materially inconsistent drawdown behavior and is **not accepted as an exact replication**. The old repository's five-macro `Heine3Of5` proxy is also explicitly rejected because it was not the slide model.

No post-2013 headline is reported until the DJ20 continuity problem is resolved honestly.

## Data provenance / open items

- DJ20/DJCB: historical Dow Jones 20 Bond Average, known to be an average price (% par) of 10 industrial + 10 utility bonds; exact machine-readable history remains unresolved.
- long Treasury yield: public Federal Reserve historical Treasury yield proxy.
- 90-day T-bill: Federal Reserve H.15.
- DJ Utility Average: historical Dow Jones Utility Average.
- CRB: historical CRB commodity index; exact series/version continuity must remain frozen with source notes.

`strategy.py` implements the actual 3-of-5 rule and deliberately does not encode any proxy substitution.
