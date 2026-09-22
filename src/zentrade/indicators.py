from __future__ import annotations

from .models import Candle, Regime


def ema(values: list[float], period: int) -> list[float]:
    if not values:
        return []
    alpha = 2.0 / (period + 1.0)
    output = [values[0]]
    for value in values[1:]:
        output.append(alpha * value + (1.0 - alpha) * output[-1])
    return output


def atr(candles: list[Candle], period: int) -> list[float]:
    if not candles:
        return []
    true_ranges: list[float] = []
    previous_close = candles[0].close
    for candle in candles:
        true_ranges.append(
            max(
                candle.high - candle.low,
                abs(candle.high - previous_close),
                abs(candle.low - previous_close),
            )
        )
        previous_close = candle.close
    return ema(true_ranges, period)


def rolling_mean(values: list[float], period: int) -> list[float]:
    output: list[float] = []
    total = 0.0
    for index, value in enumerate(values):
        total += value
        if index >= period:
            total -= values[index - period]
        count = min(index + 1, period)
        output.append(total / count)
    return output


def classify_regimes(
    candles: list[Candle],
    ema_period: int,
    atr_period: int,
    atr_baseline_period: int,
) -> tuple[list[float], list[float], list[Regime]]:
    closes = [candle.close for candle in candles]
    ema_values = ema(closes, ema_period)
    atr_values = atr(candles, atr_period)
    atr_baseline = rolling_mean(atr_values, atr_baseline_period)
    regimes: list[Regime] = []

    slope_window = max(4, ema_period // 6)
    for index, candle in enumerate(candles):
        previous = ema_values[max(0, index - slope_window)]
        slope = abs(ema_values[index] - previous)
        normalized_slope = slope / max(atr_values[index], 1e-12)
        atr_ratio = atr_values[index] / max(atr_baseline[index], 1e-12)
        trending = normalized_slope >= 0.80
        volatile = atr_ratio >= 1.15

        if trending and volatile:
            regime = Regime.VOLATILE_TREND
        elif trending:
            regime = Regime.STABLE_TREND
        elif volatile:
            regime = Regime.SIDEWAYS_CHOP
        else:
            regime = Regime.SIDEWAYS_QUIET
        regimes.append(regime)

    return ema_values, atr_values, regimes
