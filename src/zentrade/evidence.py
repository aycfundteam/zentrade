from __future__ import annotations

import csv
import html
import json
from decimal import Decimal
from pathlib import Path


def load_daily_pnl(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def summarize(rows: list[dict[str, str]]) -> dict[str, str | int]:
    if not rows:
        raise ValueError("daily evidence is empty")
    decimal_columns = [
        "gross_cashflow_usdt",
        "trading_fee_usdt",
        "net_funding_usdt",
        "net_pnl_usdt",
        "closed_pnl_usdt",
    ]
    totals = {
        column: sum((Decimal(row[column]) for row in rows), Decimal(0))
        for column in decimal_columns
    }
    return {
        "days": len(rows),
        "first_day_utc_plus_8": rows[0]["date_utc_plus_8"],
        "last_day_utc_plus_8": rows[-1]["date_utc_plus_8"],
        **{key: format(value, "f") for key, value in totals.items()},
    }


def _write_svg(rows: list[dict[str, str]], path: Path) -> None:
    width, height = 1000, 420
    left, right, top, bottom = 82, 30, 52, 58
    cumulative: list[Decimal] = []
    total = Decimal(0)
    for row in rows:
        total += Decimal(row["net_pnl_usdt"])
        cumulative.append(total)
    values = [float(value) for value in cumulative]
    low, high = min(0.0, min(values)), max(0.0, max(values))
    span = max(high - low, 1.0)
    plot_w, plot_h = width - left - right, height - top - bottom
    points = []
    for index, value in enumerate(values):
        x = left + plot_w * index / max(len(values) - 1, 1)
        y = top + plot_h * (high - value) / span
        points.append(f"{x:.2f},{y:.2f}")
    zero_y = top + plot_h * high / span
    title = html.escape(f"Connected Bybit account · net realized PnL {total:+.2f} USDT")
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Cumulative net realized PnL">
<rect width="100%" height="100%" rx="18" fill="#0b0f14"/>
<text x="{left}" y="30" fill="#f4f5f7" font-family="ui-monospace,monospace" font-size="18">{title}</text>
<text x="{left}" y="48" fill="#9ba7b4" font-family="ui-monospace,monospace" font-size="12">2026-03-06 11:00 → 2026-03-27 11:00 UTC+8 · transfers excluded</text>
<line x1="{left}" y1="{zero_y:.2f}" x2="{width-right}" y2="{zero_y:.2f}" stroke="#34404d"/>
<line x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}" stroke="#34404d"/>
<polyline points="{' '.join(points)}" fill="none" stroke="#43d17a" stroke-width="4" stroke-linejoin="round"/>
<text x="12" y="{top+6}" fill="#9ba7b4" font-family="ui-monospace,monospace" font-size="13">{high:+.0f}</text>
<text x="12" y="{height-bottom+5}" fill="#9ba7b4" font-family="ui-monospace,monospace" font-size="13">{low:+.0f}</text>
<text x="{left}" y="{height-20}" fill="#9ba7b4" font-family="ui-monospace,monospace" font-size="13">{rows[0]['date_utc_plus_8']}</text>
<text x="{width-right-84}" y="{height-20}" fill="#9ba7b4" font-family="ui-monospace,monospace" font-size="13">{rows[-1]['date_utc_plus_8']}</text>
</svg>\n"""
    path.write_text(svg, encoding="utf-8")


def write_evidence_bundle(
    rows: list[dict[str, str]],
    manifest: dict[str, object],
    output_dir: str | Path,
) -> Path:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    totals = summarize(rows)
    payload = {
        "schema_version": "zentrade-competition-evidence/v1",
        "daily_aggregate": totals,
        "read_only_api_summary": manifest,
        "interpretation": {
            "competition_metric_reproduced": False,
            "rank_independently_reverified": False,
            "account_identifier_included": False,
        },
    }
    (output / "evidence.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    report = f"""# Competition-window account evidence

| Metric | Value |
|---|---:|
| Daily rows | {totals['days']} |
| Net realized PnL, transfers excluded | {totals['net_pnl_usdt']} USDT |
| Closed PnL | {totals['closed_pnl_usdt']} USDT |
| Trading fees | -{totals['trading_fee_usdt']} USDT |
| Net funding | {totals['net_funding_usdt']} USDT |
| Simple realized return | {manifest['simple_realized_return_pct']}% |

This is a sanitized daily aggregation of a read-only Bybit V5 account reconstruction for the supplied event window. The account identifier and authenticated raw payloads are excluded. The simple return is not Bybit's leaderboard formula and does not independently verify the reported rank or +14.82% competition result.
"""
    (output / "report.md").write_text(report, encoding="utf-8")
    _write_svg(rows, output / "daily-pnl.svg")
    return output
