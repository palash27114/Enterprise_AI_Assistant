.PHONY: help install dev run frontend-install frontend-dev docker-build docker-up docker-down docker-dev docker-logs docker-ps health

help:
	@echo "Enterprise AI Assistant — available commands:"
	@echo "  make install          Install Python dependencies locally"
	@echo "  make dev              Run API locally with hot reload"
	@echo "  make run              Run API locally (production mode, multi-worker)"
	@echo "  make frontend-install Install frontend dependencies"
	@echo "  make frontend-dev     Run frontend locally (Vite dev server)"
	@echo "  make docker-build     Build production Docker images"
	@echo "  make docker-up        Start production stack (frontend + api + nginx + postgres)"
	@echo "  make docker-dev       Start development stack with hot reload"
	@echo "  make docker-down      Stop all Docker containers"
	@echo "  make docker-logs      Tail container logs"
	@echo "  make docker-ps        Show running containers"
	@echo "  make health           Hit the health endpoint"

install:
	pip install -r requirements.txt

dev:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2

frontend-install:
	cd frontend && npm install

frontend-dev:
	cd frontend && npm run dev

docker-build:
	docker compose build

docker-up:
	docker compose up -d --build

docker-dev:
	docker compose -f docker-compose.dev.yml up --build

docker-reset-db:
	docker compose -f docker-compose.dev.yml down -v
	docker compose down -v 2>/dev/null || true
	@echo "Database volumes removed. Run 'make docker-dev' to start fresh."

docker-down:
	docker compose down
	docker compose -f docker-compose.dev.yml down 2>/dev/null || true

docker-logs:
	docker compose logs -f

docker-ps:
	docker compose ps

health:
	curl -s http://localhost:$${NGINX_PORT:-80}/health || curl -s http://localhost:8000/health
