# Coding-agent experiment

Use this workflow to make one controlled change:

1. Run `zentrade verify-data`.
2. Run `zentrade demo --output artifacts/baseline`.
3. Read `artifacts/baseline/result.json` and keep the bundled data unchanged.
4. Change exactly one `StrategyConfig` value or pass one supported CLI option.
5. Run the new configuration to `artifacts/experiment`.
6. Compare return, maximum drawdown, trade count, fees, and buy-and-hold.
7. Explain why the result does or does not support a general claim. Do not use one data window as evidence of future returns.

Suggested first experiment:

```bash
zentrade demo --output artifacts/1x --leverage 1
zentrade demo --output artifacts/3x --leverage 3
```

Compare risk and costs as well as return.
