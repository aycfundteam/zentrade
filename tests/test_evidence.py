from decimal import Decimal
from importlib import resources
from pathlib import Path

from zentrade.evidence import load_daily_pnl, summarize


def data_path() -> Path:
    return Path(str(resources.files("zentrade.data").joinpath("competition_daily_pnl.csv")))


def test_sanitized_daily_evidence_reconciles() -> None:
    totals = summarize(load_daily_pnl(data_path()))
    assert totals["days"] == 22
    assert Decimal(str(totals["net_pnl_usdt"])) == Decimal("316.83743975")
    components = (
        Decimal(str(totals["gross_cashflow_usdt"]))
        - Decimal(str(totals["trading_fee_usdt"]))
        + Decimal(str(totals["net_funding_usdt"]))
    )
    assert abs(components - Decimal(str(totals["net_pnl_usdt"]))) == Decimal("0.00000003")
