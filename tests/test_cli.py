import json
from pathlib import Path

from zentrade.cli import main


def test_demo_writes_reviewable_bundle(tmp_path: Path) -> None:
    output = tmp_path / "demo"
    assert main(["demo", "--output", str(output)]) == 0

    assert {path.name for path in output.iterdir()} == {
        "equity.svg",
        "report.md",
        "result.json",
        "trades.csv",
    }
    result = json.loads((output / "result.json").read_text())
    assert result["schema_version"] == "zentrade-backtest/v1"
    assert result["assumptions"]["live_execution"] is False
    assert result["window"]["candles"] == 504


def test_verify_data_checksum() -> None:
    assert main(["verify-data"]) == 0


def test_evidence_writes_sanitized_bundle(tmp_path: Path) -> None:
    output = tmp_path / "evidence"
    assert main(["evidence", "--output", str(output)]) == 0
    assert {path.name for path in output.iterdir()} == {
        "daily-pnl.svg",
        "evidence.json",
        "report.md",
    }
    payload = json.loads((output / "evidence.json").read_text())
    assert payload["interpretation"]["account_identifier_included"] is False
