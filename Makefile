.PHONY: install format lint typecheck test report

install:
	uv sync

format:
	uv run ruff format .

lint:
	uv run ruff format --check .
	uv run ruff check .

typecheck:
	uv run mypy

test:
	uv run pytest

report:
	uv run python -m quran_analysis.claims.report
