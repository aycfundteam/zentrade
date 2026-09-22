"""zenTrade Grid Lab: a small, reproducible adaptive-grid research kit."""

from .backtest import BacktestResult, run_backtest
from .models import StrategyConfig

__all__ = ["BacktestResult", "StrategyConfig", "run_backtest"]
__version__ = "0.1.0"
