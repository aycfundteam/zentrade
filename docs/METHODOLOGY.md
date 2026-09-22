# Methodology

zenTrade Grid Lab is a deterministic bar-based simulator for studying adaptive grid behavior. It is intentionally small enough to audit without a framework.

## Signal timing

At rebalance time the strategy uses the prior candle's close, EMA, ATR, and regime. It then places limit levels around that anchor. The current candle may fill those orders, but the same candle cannot also close a newly filled position. This removes one common look-ahead shortcut.

## Grid construction

The base distance is:

```text
ATR × spacing_atr × regime_multiplier
```

The EMA determines which side sits slightly closer to the anchor. Both long and short orders remain available, so the demo preserves the two-sided character of the competition-era design without copying the production engine.

## Regime model

The four regimes combine two observable features:

- trend: normalized EMA slope over a short lookback;
- volatility: current ATR relative to a rolling ATR baseline.

The resulting states are `stable_trend`, `volatile_trend`, `sideways_quiet`, and `sideways_chop`. Regimes change grid spacing; they do not make performance claims.

## Execution assumptions

- Entry price includes adverse slippage.
- Exit price includes adverse slippage.
- Entry and exit notional each pay a fee.
- If stop and take-profit are both inside one OHLC bar, stop wins.
- Open positions close at the last available close.
- Margin is computed as notional divided by leverage and capped at a share of cash.

The model does not include funding, liquidation, order-book queue position, partial fills, latency, minimum quantity, tick size, outages, or tax.

## Why the bundled result is not the competition result

The sample uses BTCUSDT hourly candles and public parameters selected for clarity. The competition system traded a live account under an operational stack with different execution data, controls, and strategy revisions. Treat the sample as a reproducible experiment, not a replay.

## Reproduction contract

A result is comparable when all of these stay fixed:

1. dataset checksum;
2. strategy configuration;
3. simulator version;
4. fee and slippage assumptions;
5. intrabar conflict rule.

`result.json` records those inputs. Include it when opening a result issue or pull request.
