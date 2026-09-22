from __future__ import annotations

from .models import GridOrder, Regime, Side, StrategyConfig

_REGIME_SPACING = {
    Regime.STABLE_TREND: 0.90,
    Regime.VOLATILE_TREND: 1.35,
    Regime.SIDEWAYS_QUIET: 0.80,
    Regime.SIDEWAYS_CHOP: 1.55,
}


def build_grid(
    anchor: float,
    current_ema: float,
    current_atr: float,
    regime: Regime,
    config: StrategyConfig,
) -> list[GridOrder]:
    """Build a two-sided grid, with the trend side slightly closer to price."""
    base_spacing = current_atr * config.spacing_atr * _REGIME_SPACING[regime]
    bullish = anchor >= current_ema
    orders: list[GridOrder] = []

    for level in range(1, config.levels_per_side + 1):
        long_bias = 0.85 if bullish else 1.15
        short_bias = 1.15 if bullish else 0.85
        orders.append(
            GridOrder(
                side=Side.LONG,
                level=level,
                price=anchor - base_spacing * level * long_bias,
                atr=current_atr,
                regime=regime,
            )
        )
        orders.append(
            GridOrder(
                side=Side.SHORT,
                level=level,
                price=anchor + base_spacing * level * short_bias,
                atr=current_atr,
                regime=regime,
            )
        )
    return orders
