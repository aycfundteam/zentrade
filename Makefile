.PHONY: demo test check

demo:
	python -m zentrade demo

test:
	python -m pytest

check: test
	python -m ruff check .
	python -m zentrade verify-data
	python -m zentrade demo --output artifacts/demo
	python -m zentrade evidence --output artifacts/evidence
