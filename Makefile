PYTHON ?= python3
BACKEND_HOST ?= 127.0.0.1
BACKEND_PORT ?= 8000
FRONTEND_PORT ?= 8080
BACKEND_ORIGIN ?= http://$(BACKEND_HOST):$(BACKEND_PORT)

.PHONY: help run backend frontend test test-backend test-frontend smoke

help:
	@echo "Targets:"
	@echo "  make run            Start backend + python frontend dev server"
	@echo "  make backend        Start backend API only"
	@echo "  make frontend       Start python frontend dev server only"
	@echo "  make test-backend   Run backend pytest suite"
	@echo "  make test-frontend  Run frontend unit/regression suites"
	@echo "  make smoke          Run backend integration + browser smoke tests"
	@echo "  make test           Run backend + frontend + smoke tests"

backend:
	$(PYTHON) -m uvicorn backend.app.main:app --host $(BACKEND_HOST) --port $(BACKEND_PORT)

frontend:
	PORT=$(FRONTEND_PORT) BACKEND_ORIGIN=$(BACKEND_ORIGIN) $(PYTHON) scripts/dev_server.py

run:
	@set -e; \
	echo "Starting backend on http://$(BACKEND_HOST):$(BACKEND_PORT)"; \
	$(PYTHON) -m uvicorn backend.app.main:app --host $(BACKEND_HOST) --port $(BACKEND_PORT) & \
	BACK_PID=$$!; \
	echo "Starting frontend on http://127.0.0.1:$(FRONTEND_PORT)/public/index.html"; \
	PORT=$(FRONTEND_PORT) BACKEND_ORIGIN=$(BACKEND_ORIGIN) $(PYTHON) scripts/dev_server.py & \
	FRONT_PID=$$!; \
	trap 'kill $$FRONT_PID $$BACK_PID >/dev/null 2>&1' INT TERM EXIT; \
	wait $$BACK_PID $$FRONT_PID

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
