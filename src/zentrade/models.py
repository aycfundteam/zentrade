from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum


class Side(str, Enum):
    LONG = "long"
    SHORT = "short"


class Regime(str, Enum):
    STABLE_TREND = "stable_trend"
    VOLATILE_TREND = "volatile_trend"
    SIDEWAYS_QUIET = "sideways_quiet"
    SIDEWAYS_CHOP = "sideways_chop"


@dataclass(frozen=True)
class Candle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class StrategyConfig:
    initial_equity: float = 1_000.0
    leverage: float = 3.0
    levels_per_side: int = 3
    risk_per_level: float = 0.035
    max_margin_ratio: float = 0.50
    ema_period: int = 48
    atr_period: int = 14
    atr_baseline_period: int = 72
    rebalance_bars: int = 6
    spacing_atr: float = 0.85
    take_profit_atr: float = 0.70
    stop_loss_atr: float = 3.25
    fee_rate: float = 0.00055
    slippage_rate: float = 0.00020
    max_open_positions: int = 6

    def validate(self) -> None:
        if self.initial_equity <= 0:
            raise ValueError("initial_equity must be positive")
        if not 1 <= self.leverage <= 10:
            raise ValueError("leverage must be between 1 and 10")
        if not 1 <= self.levels_per_side <= 10:
            raise ValueError("levels_per_side must be between 1 and 10")
        if not 0 < self.risk_per_level <= 0.25:
            raise ValueError("risk_per_level must be in (0, 0.25]")
        if not 0 < self.max_margin_ratio <= 1:
            raise ValueError("max_margin_ratio must be in (0, 1]")
        if min(self.ema_period, self.atr_period, self.atr_baseline_period) < 2:
            raise ValueError("indicator periods must be at least 2")
        if self.rebalance_bars < 1:
            raise ValueError("rebalance_bars must be positive")
        if min(self.spacing_atr, self.take_profit_atr, self.stop_loss_atr) <= 0:
            raise ValueError("ATR multipliers must be positive")
        if min(self.fee_rate, self.slippage_rate) < 0:
            raise ValueError("cost rates cannot be negative")
        if self.max_open_positions < 1:
            raise ValueError("max_open_positions must be positive")

    def to_dict(self) -> dict[str, float | int]:
        return asdict(self)


@dataclass(frozen=True)
class GridOrder:
    side: Side
    level: int
    price: float
    atr: float
    regime: Regime


@dataclass
class Position:
    side: Side
    level: int
    entry_price: float
    quantity: float
    entry_atr: float
    opened_at: datetime
    entry_fee: float
    regime: Regime


@dataclass(frozen=True)
class Trade:
    side: Side
    level: int
    regime: Regime
    opened_at: datetime
    closed_at: datetime
    entry_price: float
    exit_price: float
    quantity: float
    gross_pnl: float
    fees: float
    net_pnl: float
    exit_reason: str

    def to_dict(self) -> dict[str, str | float | int]:
        return {
            "side": self.side.value,
            "level": self.level,
            "regime": self.regime.value,
            "opened_at": self.opened_at.isoformat().replace("+00:00", "Z"),
            "closed_at": self.closed_at.isoformat().replace("+00:00", "Z"),
            "entry_price": round(self.entry_price, 8),
            "exit_price": round(self.exit_price, 8),
            "quantity": round(self.quantity, 12),
            "gross_pnl": round(self.gross_pnl, 8),
            "fees": round(self.fees, 8),
            "net_pnl": round(self.net_pnl, 8),
            "exit_reason": self.exit_reason,
        }
