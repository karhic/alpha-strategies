# Freeburg

Clean, auditable reconstruction of the six Freeburg timing sleeves.

This directory consolidates the validated work from `karhic/edge-research-scratchpad` into a readable strategy project. The scratchpad remains the research archive; this directory is the clean implementation and documentation layer.

## Design goals

A reader should be able to:

1. read each sleeve rule in a small amount of code;
2. trace every input to a documented source;
3. rebuild/download the data using provided scripts;
4. verify that only information available at the decision time is visible to the strategy;
5. reproduce the historical analytics and published Freeburg fingerprints;
6. inspect the resulting signals/trades; and
7. run the same strategy logic through a replay, paper, or live adapter without rewriting the rule itself.

## The six sleeves

1. Primas
2. Triple-40
3. Heine
4. Pu Shen
5. Competitive Returns
6. Prime / Discount Spread

The equal-weight six-sleeve portfolio is a portfolio layer, not a seventh sleeve.

## What is already established

The accounting and most of the historical reconstruction work already exists in `edge-research-scratchpad`; it is not being rediscovered here.

The corrected scratchpad reconstruction reached approximately:

- five-sleeve common-sample portfolio: 11.52% CAGR / -9.16% max drawdown;
- six sleeves with the current Heine return proxy: 11.34% CAGR / -7.33% max drawdown;
- Freeburg published six-sleeve target: 11.3% CAR / -11.7% max drawdown.

The mean-return fingerprint is therefore essentially replicated. The main unresolved historical discrepancy is the exact weekly Dow Jones 20/Composite Bond return path used by Heine, whose current proxy is too smooth and therefore understates portfolio drawdown.

## Project policy

This clean project ports canonical results, source logic, timing conventions, and accounting from the scratchpad. It does not silently replace them with new approximations.

Where a result is unresolved, the unresolved state is documented explicitly rather than tuned away.

The standalone replay/live infrastructure remains outside this repository. Freeburg should be able to plug into an engine such as `causal-trading-engine` or `open-alpha-verifier`, but those repositories remain generic and contain no Freeburg-specific implementation.
