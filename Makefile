.PHONY: install test lint check build up down logs health

install:
	python -m pip install -e ".[dev]"

test:
	python -m pytest -q

lint:
	python -m ruff check .

check: lint test

build:
	docker compose build app

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

health:
	curl -fsS http://localhost:8000/health
