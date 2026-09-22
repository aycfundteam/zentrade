from datetime import UTC, datetime, timedelta

import pytest

from zentrade.indicators import atr, classify_regimes, ema
from zentrade.models import Candle, Regime


def candles(count: int = 120) -> list[Candle]:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    output = []
    for index in range(count):
        close = 100 + index * 0.4
        output.append(
            Candle(
                timestamp=start + timedelta(hours=index),
                open=close - 0.2,
                high=close + 1.0,
                low=close - 1.0,
                close=close,
                volume=10,
            )
        )
    return output


def test_ema_preserves_length_and_moves_toward_prices() -> None:
    values = [1.0, 2.0, 3.0, 4.0]
    result = ema(values, 3)
    assert result == pytest.approx([1.0, 1.5, 2.25, 3.125])


def test_atr_uses_previous_close_gap() -> None:
    sample = [
        Candle(datetime(2026, 1, 1, tzinfo=UTC), 100, 101, 99, 100, 1),
        Candle(datetime(2026, 1, 1, 1, tzinfo=UTC), 110, 111, 109, 110, 1),
    ]
    values = atr(sample, 2)
    assert values[0] == pytest.approx(2)
    assert values[1] > 2


def test_regime_classifier_returns_one_state_per_candle() -> None:
    sample = candles()
    ema_values, atr_values, regimes = classify_regimes(sample, 48, 14, 72)
    assert len(ema_values) == len(atr_values) == len(regimes) == len(sample)
    assert set(regimes).issubset(set(Regime))
