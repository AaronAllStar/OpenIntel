.PHONY: dev test test-unit test-adapters test-api lint clean-exports migrate

dev:
	uv run --no-sync uvicorn src.app.api.main:app --reload --host 127.0.0.1 --port 8000

worker:
	uv run --no-sync celery -A src.app.infrastructure.celery_app worker --loglevel=info

dev-ui:
	cd src/ui && npm run dev

test:
	uv run --no-sync pytest tests/ -v

test-unit:
	uv run --no-sync pytest tests/unit/ -v

test-adapters:
	uv run --no-sync pytest tests/adapters/ -v

test-api:
	uv run --no-sync pytest tests/integration/ -v

lint:
	uv run --no-sync ruff check src tests
	uv run --no-sync mypy src

migrate:
	uv run alembic upgrade head

clean-exports:
	rm -rf data/exports/*
