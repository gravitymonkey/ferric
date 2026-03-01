PYTHON ?= python3
BACKEND_HOST ?= 127.0.0.1
BACKEND_PORT ?= 8000
FRONTEND_PORT ?= 8080
BACKEND_ORIGIN ?= http://$(BACKEND_HOST):$(BACKEND_PORT)
DATABASE_URL ?= sqlite:///./backend/ferric.db
FERRIC_LOG_DIR ?= ./backend/logs
FERRIC_BACKEND_LOG_PATH ?= $(FERRIC_LOG_DIR)/backend.log
FERRIC_FRONTEND_LOG_PATH ?= $(FERRIC_LOG_DIR)/frontend.log

ifneq (,$(wildcard .env))
include .env
export BACKEND_HOST BACKEND_PORT FRONTEND_PORT BACKEND_ORIGIN DATABASE_URL FERRIC_ADMIN_USER FERRIC_ADMIN_PASSWORD FERRIC_LOG_DIR FERRIC_BACKEND_LOG_PATH FERRIC_FRONTEND_LOG_PATH
endif

.PHONY: help deps run run-hot backend backend-hot frontend db-upgrade db-downgrade db-seed logs-tail test test-backend test-frontend smoke

help:
	@echo "Targets:"
	@echo "  make deps           Install backend Python dependencies"
	@echo "  make run            Start backend + python frontend dev server"
	@echo "  make run-hot        Start backend + frontend with backend auto-reload"
	@echo "  make backend        Start backend API only"
	@echo "  make backend-hot    Start backend API only (auto-reload)"
	@echo "  make frontend       Start python frontend dev server only"
	@echo "  make db-upgrade     Apply Alembic migrations to DATABASE_URL"
	@echo "  make db-downgrade   Downgrade Alembic migration by one step"
	@echo "  make db-seed        Seed catalog data from public/catalog.json into DB"
	@echo "  make logs-tail      Tail backend/frontend log files"
	@echo "  make test-backend   Run backend pytest suite"
	@echo "  make test-frontend  Run frontend unit/regression suites"
	@echo "  make smoke          Run backend integration + browser smoke tests"
	@echo "  make test           Run backend + frontend + smoke tests"

deps:
	$(PYTHON) -m pip install -r backend/requirements.txt

db-upgrade:
	DATABASE_URL=$(DATABASE_URL) $(PYTHON) -m alembic -c backend/alembic.ini upgrade head

db-downgrade:
	DATABASE_URL=$(DATABASE_URL) $(PYTHON) -m alembic -c backend/alembic.ini downgrade -1

db-seed: db-upgrade
	DATABASE_URL=$(DATABASE_URL) $(PYTHON) -m backend.app.seed_catalog

backend: deps db-upgrade db-seed
	@mkdir -p $(FERRIC_LOG_DIR)
	DATABASE_URL=$(DATABASE_URL) FERRIC_LOG_DIR=$(FERRIC_LOG_DIR) FERRIC_BACKEND_LOG_PATH=$(FERRIC_BACKEND_LOG_PATH) $(PYTHON) -m uvicorn backend.app.main:app --host $(BACKEND_HOST) --port $(BACKEND_PORT)

backend-hot: deps db-upgrade db-seed
	@mkdir -p $(FERRIC_LOG_DIR)
	DATABASE_URL=$(DATABASE_URL) FERRIC_LOG_DIR=$(FERRIC_LOG_DIR) FERRIC_BACKEND_LOG_PATH=$(FERRIC_BACKEND_LOG_PATH) $(PYTHON) -m uvicorn backend.app.main:app --host $(BACKEND_HOST) --port $(BACKEND_PORT) --reload --reload-dir backend/app --reload-dir public --reload-dir src

frontend:
	@mkdir -p $(FERRIC_LOG_DIR)
	PORT=$(FRONTEND_PORT) BACKEND_ORIGIN=$(BACKEND_ORIGIN) FERRIC_FRONTEND_LOG_PATH=$(FERRIC_FRONTEND_LOG_PATH) $(PYTHON) scripts/dev_server.py

run:
	@set -e; \
	$(PYTHON) -m pip install -r backend/requirements.txt; \
	mkdir -p $(FERRIC_LOG_DIR); \
	DATABASE_URL=$(DATABASE_URL) $(PYTHON) -m alembic -c backend/alembic.ini upgrade head; \
	DATABASE_URL=$(DATABASE_URL) $(PYTHON) -m backend.app.seed_catalog; \
	echo "Starting backend on http://$(BACKEND_HOST):$(BACKEND_PORT)"; \
	DATABASE_URL=$(DATABASE_URL) FERRIC_LOG_DIR=$(FERRIC_LOG_DIR) FERRIC_BACKEND_LOG_PATH=$(FERRIC_BACKEND_LOG_PATH) $(PYTHON) -m uvicorn backend.app.main:app --host $(BACKEND_HOST) --port $(BACKEND_PORT) & \
	BACK_PID=$$!; \
	echo "Starting frontend on http://127.0.0.1:$(FRONTEND_PORT)/public/index.html"; \
	PORT=$(FRONTEND_PORT) BACKEND_ORIGIN=$(BACKEND_ORIGIN) FERRIC_FRONTEND_LOG_PATH=$(FERRIC_FRONTEND_LOG_PATH) $(PYTHON) scripts/dev_server.py & \
	FRONT_PID=$$!; \
	trap 'kill $$FRONT_PID $$BACK_PID >/dev/null 2>&1' INT TERM EXIT; \
	wait $$BACK_PID $$FRONT_PID

run-hot:
	@set -e; \
	$(PYTHON) -m pip install -r backend/requirements.txt; \
	mkdir -p $(FERRIC_LOG_DIR); \
	DATABASE_URL=$(DATABASE_URL) $(PYTHON) -m alembic -c backend/alembic.ini upgrade head; \
	DATABASE_URL=$(DATABASE_URL) $(PYTHON) -m backend.app.seed_catalog; \
	echo "Starting backend (reload) on http://$(BACKEND_HOST):$(BACKEND_PORT)"; \
	DATABASE_URL=$(DATABASE_URL) FERRIC_LOG_DIR=$(FERRIC_LOG_DIR) FERRIC_BACKEND_LOG_PATH=$(FERRIC_BACKEND_LOG_PATH) $(PYTHON) -m uvicorn backend.app.main:app --host $(BACKEND_HOST) --port $(BACKEND_PORT) --reload --reload-dir backend/app --reload-dir public --reload-dir src & \
	BACK_PID=$$!; \
	echo "Starting frontend on http://127.0.0.1:$(FRONTEND_PORT)/public/index.html"; \
	PORT=$(FRONTEND_PORT) BACKEND_ORIGIN=$(BACKEND_ORIGIN) FERRIC_FRONTEND_LOG_PATH=$(FERRIC_FRONTEND_LOG_PATH) $(PYTHON) scripts/dev_server.py & \
	FRONT_PID=$$!; \
	trap 'kill $$FRONT_PID $$BACK_PID >/dev/null 2>&1' INT TERM EXIT; \
	wait $$BACK_PID $$FRONT_PID

logs-tail:
	@mkdir -p $(FERRIC_LOG_DIR)
	@echo "Tailing $(FERRIC_BACKEND_LOG_PATH) and $(FERRIC_FRONTEND_LOG_PATH)"
	@tail -n 100 -f $(FERRIC_BACKEND_LOG_PATH) $(FERRIC_FRONTEND_LOG_PATH)

test-backend:
	$(PYTHON) -m pytest backend/tests -q

test-frontend:
	npm run test:catalog
	npm run test:api-seams
	npm run test:queue
	npm run test:media-engine
	npm run test:playback-play-pause
	npm run test:view-continuity
	npm run test:golden-flow
	npm run test:hls-assets
	npm run test:catalog-media

smoke:
	npm run test:phase2-integration
	npm run test:browsers

test: test-backend test-frontend smoke
