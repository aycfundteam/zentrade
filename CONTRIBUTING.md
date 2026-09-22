# Contributing

Thank you for improving zenTrade Grid Lab.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
pytest
zentrade demo
```

## Pull requests

- Keep live exchange connectivity out of this repository.
- Add a focused test for changed accounting or execution behavior.
- Preserve chronological signal timing.
- State the data checksum, configuration, and simulator version for performance comparisons.
- Commit generated benchmark assets only when the inputs and command are documented.
- Never include API keys, account identifiers, authenticated exchange payloads, or customer data.

Performance improvements need an explanation of the changed assumption. Parameter tuning on the bundled sample alone is not evidence of generalization.
