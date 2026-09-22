from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from datetime import UTC, datetime
from itertools import pairwise
from pathlib import Path

from .indicators import classify_regimes
from .models import Candle, GridOrder, Position, Side, StrategyConfig, Trade
from .strategy import build_grid


@dataclass(frozen=True)
class EquityPoint:
    timestamp: datetime
    equity: float


@dataclass(frozen=True)
class BacktestResult:
    config: StrategyConfig
    candles: tuple[Candle, ...]
    trades: tuple[Trade, ...]
    equity_curve: tuple[EquityPoint, ...]
    ending_equity: float
    total_return_pct: float
    buy_hold_return_pct: float
    max_drawdown_pct: float
    win_rate_pct: float
    profit_factor: float | None
    total_fees: float

    def metrics(self) -> dict[str, float | int | None]:
        return {
            "starting_equity": round(self.config.initial_equity, 8),
            "ending_equity": round(self.ending_equity, 8),
            "total_return_pct": round(self.total_return_pct, 6),
            "buy_hold_return_pct": round(self.buy_hold_return_pct, 6),
            "max_drawdown_pct": round(self.max_drawdown_pct, 6),
            "closed_trades": len(self.trades),
            "win_rate_pct": round(self.win_rate_pct, 6),
            "profit_factor": None if self.profit_factor is None else round(self.profit_factor, 6),
            "total_fees": round(self.total_fees, 8),
        }


def load_candles(path: str | Path) -> list[Candle]:
    candles: list[Candle] = []
    with Path(path).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            timestamp = datetime.fromisoformat(row["timestamp"])
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=UTC)
            candles.append(
                Candle(
                    timestamp=timestamp,
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row.get("volume", 0.0)),
                )
            )
    if len(candles) < 100:
        raise ValueError("at least 100 candles are required")
    if any(left.timestamp >= right.timestamp for left, right in pairwise(candles)):
        raise ValueError("candles must be strictly chronological")
    return candles


def _exit_price(position: Position, candle: Candle, config: StrategyConfig) -> tuple[float, str] | None:
    tp_distance = position.entry_atr * config.take_profit_atr
    stop_distance = position.entry_atr * config.stop_loss_atr
    if position.side is Side.LONG:
        take_profit = position.entry_price + tp_distance
        stop = position.entry_price - stop_distance
        hit_stop = candle.low <= stop
        hit_take_profit = candle.high >= take_profit
    else:
        take_profit = position.entry_price - tp_distance
        stop = position.entry_price + stop_distance
        hit_stop = candle.high >= stop
        hit_take_profit = candle.low <= take_profit

    # OHLC bars do not reveal intrabar path. If both boundaries are touched,
    # choose the stop first so the demo cannot benefit from optimistic ordering.
    if hit_stop:
        return stop, "stop"
    if hit_take_profit:
        return take_profit, "take_profit"
    return None


def _mark_to_market(position: Position, price: float) -> float:
    direction = 1.0 if position.side is Side.LONG else -1.0
    return direction * (price - position.entry_price) * position.quantity


def _close_position(
    position: Position,
    timestamp: datetime,
    raw_exit_price: float,
    reason: str,
    config: StrategyConfig,
) -> Trade:
    direction = 1.0 if position.side is Side.LONG else -1.0
    execution_price = raw_exit_price * (1.0 - direction * config.slippage_rate)
    gross_pnl = direction * (execution_price - position.entry_price) * position.quantity
    exit_fee = abs(execution_price * position.quantity) * config.fee_rate
    fees = position.entry_fee + exit_fee
    return Trade(
        side=position.side,
        level=position.level,
        regime=position.regime,
        opened_at=position.opened_at,
        closed_at=timestamp,
        entry_price=position.entry_price,
        exit_price=execution_price,
        quantity=position.quantity,
        gross_pnl=gross_pnl,
        fees=fees,
        net_pnl=gross_pnl - fees,
        exit_reason=reason,
    )


def run_backtest(candles: list[Candle], config: StrategyConfig | None = None) -> BacktestResult:
    config = config or StrategyConfig()
    config.validate()
    if len(candles) < max(config.ema_period, config.atr_baseline_period) + 2:
        raise ValueError("not enough candles for the configured warm-up")

    ema_values, atr_values, regimes = classify_regimes(
        candles, config.ema_period, config.atr_period, config.atr_baseline_period
    )
    warmup = max(config.ema_period, config.atr_baseline_period)
    cash = config.initial_equity
    peak_equity = cash
    max_drawdown = 0.0
    positions: list[Position] = []
    orders: list[GridOrder] = []
    trades: list[Trade] = []
    curve: list[EquityPoint] = []

    for index in range(warmup, len(candles)):
        candle = candles[index]

        survivors: list[Position] = []
        for position in positions:
            exit_signal = _exit_price(position, candle, config)
            if exit_signal is None:
                survivors.append(position)
                continue
            trade = _close_position(position, candle.timestamp, *exit_signal, config)
            cash += trade.net_pnl
            trades.append(trade)
        positions = survivors

        if (index - warmup) % config.rebalance_bars == 0:
            previous = candles[index - 1]
            orders = build_grid(
                anchor=previous.close,
                current_ema=ema_values[index - 1],
                current_atr=atr_values[index - 1],
                regime=regimes[index - 1],
                config=config,
            )

        remaining_orders: list[GridOrder] = []
        for order in orders:
            if len(positions) >= config.max_open_positions:
                remaining_orders.append(order)
                continue
            touched = candle.low <= order.price if order.side is Side.LONG else candle.high >= order.price
            if not touched:
                remaining_orders.append(order)
                continue

            used_margin = sum(abs(p.entry_price * p.quantity) / config.leverage for p in positions)
            allowed_margin = max(0.0, cash * config.max_margin_ratio - used_margin)
            desired_margin = cash * config.risk_per_level
            margin = min(desired_margin, allowed_margin)
            if margin <= 0:
                remaining_orders.append(order)
                continue

            direction = 1.0 if order.side is Side.LONG else -1.0
            execution_price = order.price * (1.0 + direction * config.slippage_rate)
            notional = margin * config.leverage
            quantity = notional / execution_price
            entry_fee = notional * config.fee_rate
            positions.append(
                Position(
                    side=order.side,
                    level=order.level,
                    entry_price=execution_price,
                    quantity=quantity,
                    entry_atr=order.atr,
                    opened_at=candle.timestamp,
                    entry_fee=entry_fee,
                    regime=order.regime,
                )
            )
        orders = remaining_orders

        marked_equity = (
            cash
            + sum(_mark_to_market(position, candle.close) for position in positions)
            - sum(position.entry_fee for position in positions)
        )
        peak_equity = max(peak_equity, marked_equity)
        if peak_equity > 0:
            max_drawdown = max(max_drawdown, (peak_equity - marked_equity) / peak_equity)
        curve.append(EquityPoint(candle.timestamp, marked_equity))

    final_candle = candles[-1]
    for position in positions:
        trade = _close_position(position, final_candle.timestamp, final_candle.close, "end_of_data", config)
        cash += trade.net_pnl
        trades.append(trade)
    if curve:
        curve[-1] = EquityPoint(final_candle.timestamp, cash)

    wins = [trade.net_pnl for trade in trades if trade.net_pnl > 0]
    losses = [trade.net_pnl for trade in trades if trade.net_pnl < 0]
    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))
    profit_factor = gross_profit / gross_loss if gross_loss else (math.inf if gross_profit else None)
    win_rate = len(wins) / len(trades) * 100 if trades else 0.0
    start_price = candles[warmup - 1].close
    buy_hold_return = (candles[-1].close / start_price - 1.0) * 100

    return BacktestResult(
        config=config,
        candles=tuple(candles),
        trades=tuple(trades),
        equity_curve=tuple(curve),
        ending_equity=cash,
        total_return_pct=(cash / config.initial_equity - 1.0) * 100,
        buy_hold_return_pct=buy_hold_return,
        max_drawdown_pct=max_drawdown * 100,
        win_rate_pct=win_rate,
        profit_factor=profit_factor,
        total_fees=sum(trade.fees for trade in trades),
    )
