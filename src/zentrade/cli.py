from __future__ import annotations

import argparse
import hashlib
import json
from importlib import resources
from pathlib import Path

from . import __version__
from .backtest import load_candles, run_backtest
from .evidence import load_daily_pnl, write_evidence_bundle
from .models import StrategyConfig
from .reporting import write_report_bundle


def sample_data_path() -> Path:
    return Path(str(resources.files("zentrade.data").joinpath("btcusdt_1h_2026-03-06_2026-03-27.csv")))


def competition_data_path() -> Path:
    return Path(str(resources.files("zentrade.data").joinpath("competition_daily_pnl.csv")))


def _config_from_args(args: argparse.Namespace) -> StrategyConfig:
    return StrategyConfig(
        initial_equity=args.initial_equity,
        leverage=args.leverage,
        fee_rate=args.fee_rate,
        slippage_rate=args.slippage_rate,
    )


def _run(args: argparse.Namespace) -> int:
    path = sample_data_path() if args.command == "demo" else Path(args.csv)
    result = run_backtest(load_candles(path), _config_from_args(args))
    output = write_report_bundle(result, args.output, path.name)
    metrics = result.metrics()
    print("zenTrade Grid Lab")
    print(f"dataset        {path}")
    print(f"return         {metrics['total_return_pct']:+.2f}%")
    print(f"buy & hold     {metrics['buy_hold_return_pct']:+.2f}%")
    print(f"max drawdown   {metrics['max_drawdown_pct']:.2f}%")
    print(f"closed trades  {metrics['closed_trades']}")
    print(f"report         {output / 'report.md'}")
    return 0


def _verify(_: argparse.Namespace) -> int:
    checks = [
        (sample_data_path(), "manifest.json"),
        (competition_data_path(), "competition_manifest.json"),
    ]
    for data_path, manifest_name in checks:
        manifest_path = Path(str(resources.files("zentrade.data").joinpath(manifest_name)))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        digest = hashlib.sha256(data_path.read_bytes()).hexdigest()
        if digest != manifest["sha256"]:
            print(f"FAILED: expected {manifest['sha256']}, got {digest}")
            return 1
        print(f"OK {digest}  {data_path.name}")
    return 0


def _evidence(args: argparse.Namespace) -> int:
    data_path = competition_data_path()
    manifest_path = Path(
        str(resources.files("zentrade.data").joinpath("competition_manifest.json"))
    )
    rows = load_daily_pnl(data_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    output = write_evidence_bundle(rows, manifest, args.output)
    print("zenTrade competition-window evidence")
    print(f"daily data  {data_path}")
    print(f"report      {output / 'report.md'}")
    return 0


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--output", default="artifacts/demo", help="report output directory")
    parser.add_argument("--initial-equity", type=float, default=1_000.0)
    parser.add_argument("--leverage", type=float, default=3.0)
    parser.add_argument("--fee-rate", type=float, default=0.00055)
    parser.add_argument("--slippage-rate", type=float, default=0.00020)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="zentrade",
        description="Reproducible adaptive-grid research, with no exchange keys.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo = subparsers.add_parser("demo", help="run the bundled competition-window sample")
    _add_common(demo)
    demo.set_defaults(handler=_run)

    backtest = subparsers.add_parser("backtest", help="run a chronological OHLCV CSV")
    backtest.add_argument("--csv", required=True)
    _add_common(backtest)
    backtest.set_defaults(handler=_run)

    verify = subparsers.add_parser("verify-data", help="verify the bundled sample checksum")
    verify.set_defaults(handler=_verify)

    evidence = subparsers.add_parser(
        "evidence", help="rebuild the sanitized competition-window evidence bundle"
    )
    evidence.add_argument("--output", default="artifacts/evidence")
    evidence.set_defaults(handler=_evidence)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.handler(args)
