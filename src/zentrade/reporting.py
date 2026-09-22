from __future__ import annotations

import csv
import html
import json
from pathlib import Path

from .backtest import BacktestResult


def _fmt(value: float | None, suffix: str = "") -> str:
    if value is None:
        return "n/a"
    if value == float("inf"):
        return "∞"
    return f"{value:,.2f}{suffix}"


def write_json(result: BacktestResult, path: Path, dataset: str) -> None:
    payload = {
        "schema_version": "zentrade-backtest/v1",
        "dataset": dataset,
        "metrics": result.metrics(),
        "config": result.config.to_dict(),
        "window": {
            "first_candle": result.candles[0].timestamp.isoformat().replace("+00:00", "Z"),
            "last_candle": result.candles[-1].timestamp.isoformat().replace("+00:00", "Z"),
            "candles": len(result.candles),
        },
        "assumptions": {
            "intrabar_conflict": "stop_first",
            "orders_fill_at": "grid_price_plus_slippage",
            "live_execution": False,
        },
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_trades(result: BacktestResult, path: Path) -> None:
    fields = list(result.trades[0].to_dict()) if result.trades else [
        "side", "level", "regime", "opened_at", "closed_at", "entry_price",
        "exit_price", "quantity", "gross_pnl", "fees", "net_pnl", "exit_reason",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for trade in result.trades:
            writer.writerow(trade.to_dict())


def write_markdown(result: BacktestResult, path: Path, dataset: str) -> None:
    metrics = result.metrics()
    text = f"""# zenTrade Grid Lab report

Dataset: `{dataset}`  
Window: {result.candles[0].timestamp.isoformat()} to {result.candles[-1].timestamp.isoformat()}  
Candles: {len(result.candles)}

| Metric | Result |
|---|---:|
| Strategy return | {_fmt(result.total_return_pct, '%')} |
| Buy and hold return | {_fmt(result.buy_hold_return_pct, '%')} |
| Ending equity | {_fmt(result.ending_equity, ' USDT')} |
| Maximum drawdown | {_fmt(result.max_drawdown_pct, '%')} |
| Closed trades | {metrics['closed_trades']} |
| Win rate | {_fmt(result.win_rate_pct, '%')} |
| Profit factor | {_fmt(result.profit_factor)} |
| Modeled fees | {_fmt(result.total_fees, ' USDT')} |

## Interpretation

This is a deterministic research simulation, not the live Bybit competition account and not a prediction. It uses hourly OHLCV bars, explicit fees and slippage, and stop-first ordering whenever one candle touches both stop and take-profit. It does not model funding, queue position, liquidation, latency, partial fills, or exchange outages.

See `result.json` for the machine-readable configuration and `trades.csv` for every modeled close.
"""
    path.write_text(text, encoding="utf-8")


def write_svg(result: BacktestResult, path: Path) -> None:
    width, height = 1000, 420
    pad_left, pad_right, pad_top, pad_bottom = 76, 30, 44, 54
    values = [point.equity for point in result.equity_curve]
    if not values:
        path.write_text("<svg xmlns='http://www.w3.org/2000/svg'/>", encoding="utf-8")
        return
    low, high = min(values), max(values)
    span = max(high - low, 1.0)
    plot_w = width - pad_left - pad_right
    plot_h = height - pad_top - pad_bottom
    points = []
    for index, value in enumerate(values):
        x = pad_left + plot_w * index / max(len(values) - 1, 1)
        y = pad_top + plot_h * (high - value) / span
        points.append(f"{x:.2f},{y:.2f}")
    color = "#43d17a" if result.total_return_pct >= 0 else "#ff6b6b"
    title = html.escape(f"zenTrade Grid Lab · {result.total_return_pct:+.2f}%")
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Equity curve">
<rect width="100%" height="100%" rx="18" fill="#0b0f14"/>
<text x="{pad_left}" y="28" fill="#f4f5f7" font-family="ui-monospace,monospace" font-size="18">{title}</text>
<line x1="{pad_left}" y1="{pad_top}" x2="{pad_left}" y2="{height-pad_bottom}" stroke="#34404d"/>
<line x1="{pad_left}" y1="{height-pad_bottom}" x2="{width-pad_right}" y2="{height-pad_bottom}" stroke="#34404d"/>
<polyline points="{' '.join(points)}" fill="none" stroke="{color}" stroke-width="3" stroke-linejoin="round"/>
<text x="12" y="{pad_top+6}" fill="#9ba7b4" font-family="ui-monospace,monospace" font-size="13">{high:,.0f}</text>
<text x="12" y="{height-pad_bottom+5}" fill="#9ba7b4" font-family="ui-monospace,monospace" font-size="13">{low:,.0f}</text>
<text x="{pad_left}" y="{height-18}" fill="#9ba7b4" font-family="ui-monospace,monospace" font-size="13">{result.candles[0].timestamp.date()}</text>
<text x="{width-pad_right-82}" y="{height-18}" fill="#9ba7b4" font-family="ui-monospace,monospace" font-size="13">{result.candles[-1].timestamp.date()}</text>
</svg>\n"""
    path.write_text(svg, encoding="utf-8")


def write_report_bundle(result: BacktestResult, output_dir: str | Path, dataset: str) -> Path:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    write_json(result, output / "result.json", dataset)
    write_trades(result, output / "trades.csv")
    write_markdown(result, output / "report.md", dataset)
    write_svg(result, output / "equity.svg")
    return output
