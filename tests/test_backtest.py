from importlib import resources
from pathlib import Path

import pytest

from zentrade.backtest import load_candles, run_backtest
from zentrade.models import StrategyConfig


def sample_path() -> Path:
    return Path(str(resources.files("zentrade.data").joinpath("btcusdt_1h_2026-03-06_2026-03-27.csv")))


def test_bundled_backtest_is_deterministic_and_accounted() -> None:
    candles = load_candles(sample_path())
    first = run_backtest(candles)
    second = run_backtest(candles)

    assert first.metrics() == second.metrics()
    assert len(first.trades) > 10
    assert first.ending_equity == pytest.approx(
        first.config.initial_equity + sum(trade.net_pnl for trade in first.trades)
    )
    assert first.total_fees == pytest.approx(sum(trade.fees for trade in first.trades))
    assert 0 <= first.win_rate_pct <= 100
    assert first.max_drawdown_pct >= 0


def test_lower_leverage_reduces_absolute_pnl_and_fees() -> None:
    candles = load_candles(sample_path())
    low = run_backtest(candles, StrategyConfig(leverage=1))
    high = run_backtest(candles, StrategyConfig(leverage=3))

    assert abs(low.ending_equity - low.config.initial_equity) < abs(
        high.ending_equity - high.config.initial_equity
    )
    assert low.total_fees < high.total_fees


def test_configuration_rejects_excessive_leverage() -> None:
    with pytest.raises(ValueError, match="leverage"):
        StrategyConfig(leverage=25).validate()
