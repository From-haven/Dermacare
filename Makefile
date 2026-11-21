.PHONY: bootstrap infra-up infra-down migrate seed dev api worker web test test-api test-contracts test-web lint deploy-fuji openapi reset

PYTHON ?= python3

bootstrap:
	@echo "=== DermaCare Agent Bootstrap ==="
	@which $(PYTHON) >/dev/null || (echo "ERROR: python3 not found. Please install Python 3.11+" && exit 1)
	@which node >/dev/null 2>&1 || echo "NOTE: Node.js not detected in host PATH. Using built-in Web server fallback."
	@which pnpm >/dev/null 2>&1 || echo "NOTE: pnpm not detected in host PATH."
	@which docker >/dev/null 2>&1 || echo "NOTE: docker not detected in host PATH. Local standalone mode active."
	@which forge >/dev/null 2>&1 || echo "NOTE: foundry/forge not detected in host PATH. Using Python chain mock & EVM test runner."
	@test -f .env || $(PYTHON) apps/api/scripts/gen_keys.py --env
	@$(PYTHON) -c "import sqlite3; print('SQLite/DB engine: OK')"
	@echo "Bootstrap completed successfully."

infra-up:
	@which docker compose >/dev/null 2>&1 && docker compose -f infra/docker-compose.yml up -d || echo "Docker compose not available; continuing in standalone local mode."

infra-down:
	@which docker compose >/dev/null 2>&1 && docker compose -f infra/docker-compose.yml down || true

migrate:
	@$(PYTHON) -c "import sys; sys.path.insert(0, 'apps/api'); from app.core.db import init_db; init_db(); print('Database initialized.')"

seed:
	@$(PYTHON) apps/api/scripts/seed.py

dev:
	@$(PYTHON) apps/api/app/main.py

api:
	@$(PYTHON) apps/api/app/main.py --api-only

worker:
	@$(PYTHON) apps/api/app/worker/jobs.py

web:
	@$(PYTHON) apps/api/app/main.py --web-only

test:
	@$(PYTHON) -m unittest discover -s tests -p "test_*.py" -v

test-api:
	@$(PYTHON) -m unittest discover -s tests -p "test_auth.py" -v
	@$(PYTHON) -m unittest discover -s tests -p "test_rbac.py" -v

test-contracts:
	@$(PYTHON) -m unittest discover -s tests -p "test_chain*.py" -v

test-web:
	@$(PYTHON) -m unittest discover -s tests -p "test_web*.py" -v

lint:
	@$(PYTHON) -c "import py_compile, glob; [py_compile.compile(f, doraise=True) for f in glob.glob('apps/api/**/*.py', recursive=True) + glob.glob('ml/**/*.py', recursive=True)]; print('Lint: OK')"

deploy-fuji:
	@$(PYTHON) apps/api/scripts/deploy_fuji.py

openapi:
	@$(PYTHON) apps/api/scripts/export_openapi.py

reset:
	@rm -rf data/derma.db data/storage/
	@echo "Data reset complete."
