include .env

$(eval export $(shell sed -ne 's/ *#.*$$//; /./ s/=.*$$// p' .env 2>/dev/null))

PYTHONPATH := $(shell pwd)/src

# ======================================
# ------------- Colors -----------------
# ======================================

GREEN  := $(shell tput -Txterm setaf 2)
YELLOW := $(shell tput -Txterm setaf 3)
WHITE  := $(shell tput -Txterm setaf 7)
RESET  := $(shell tput -Txterm sgr0)

# ======================================
# ------------- Setup ------------------
# ======================================

install: # Install dependencies using pip in your moxi virtual environment
	pip install -e .

install-dev: # Install dev dependencies
	pip install -e ".[dev]"

local-start: # Build and start local Docker infrastructure
	docker compose -f docker-compose.yml up --build -d

help: # Show this help message
	@echo ''
	@echo 'Usage:'
	@echo '  ${YELLOW}make${RESET} ${GREEN}<target>${RESET}'
	@echo ''
	@echo 'Targets:'
	@grep -E '^[a-zA-Z0-9 -]+:.*#'  Makefile | sort | while read -r l; do printf "  ${YELLOW}$$(echo $$l | cut -f 1 -d':')${RESET}:$$(echo $$l | cut -f 2- -d'#')\n"; done
	@echo ''

# ======================================
# ---------- Core Module ---------------
# ======================================

test-config: # Test that configuration loads correctly
	cd src && python -c "from core.config import settings; print(f'Project: {settings.PROJECT_NAME}'); print(f'Environment: {settings.ENVIRONMENT}')"

test-logger: # Test the logging system
	cd src && python -c "from core.logger_utils import get_logger; logger = get_logger('test'); logger.info('Logger is working!', extra='data')"

# ======================================
# ------- Pipeline 1: Repo Analyzer ----
# ======================================

local-analyze-repo: # Analyze a repository (usage: make local-analyze-repo REPO=https://github.com/user/repo)
	@if [ -z "$(REPO)" ]; then \
		echo "${YELLOW}Usage: make local-analyze-repo REPO=https://github.com/user/repo${RESET}"; \
		exit 1; \
	fi
	cd src && PYTHONPATH=$(PYTHONPATH) python -m moxi_analyzer.main --repo $(REPO)

# ======================================
# --- Moxi pipelines (collect → chunk → train). One data/ folder only. ---
# ======================================
# See data/README.md. No "training_data" folder: use data/ only.

moxi-collect: # Step 1: collect READMEs from awesome-readme lists → data/collection/ + MongoDB
	cd src && PYTHONPATH=$(PYTHONPATH) python -m moxi_collect

run-collection: # Alias for moxi-collect
	$(MAKE) moxi-collect

crawl-github-repos: # Crawl GitHub for repo URLs (for README collection or review)
	cd src && PYTHONPATH=$(PYTHONPATH) python -m moxi_data.crawlers.github_repo_crawler

find-well-structured-repos: # Find well-structured repos (candidates for README collection)
	cd src && PYTHONPATH=$(PYTHONPATH) python -m moxi_data.find_structured_repos \
		--min-stars 20 \
		--limit 200 \
		--output ../data/collection/well_structured_repos.txt

review-repos: # Launch repo review UI (approve/discard repos for README collection)
	cd src && PYTHONPATH=$(PYTHONPATH) python -m moxi_data.review_ui

pipeline-dashboard: # Dev-only: open workflow dashboard (phases, collection count e.g. 121)
	cd src && PYTHONPATH=$(PYTHONPATH) python -m web_ui.pipeline_dashboard

moxi-chunk: # Step 2: chunk READMEs from collection → data/chunks/readme_chunks.json
	cd src && PYTHONPATH=$(PYTHONPATH) python -m moxi_chunk.run_feature --output ../data/chunks/readme_chunks.json

moxi-analyze-repo: # Analyze one repo (file tree + key files). Usage: make moxi-analyze-repo REPO=https://github.com/user/repo
	@if [ -z "$(REPO)" ]; then \
		echo "${YELLOW}Usage: make moxi-analyze-repo REPO=https://github.com/user/repo${RESET}"; \
		exit 1; \
	fi
	cd src && PYTHONPATH=$(PYTHONPATH) python -m moxi_chunk.repo_analyzer.main --repo $(REPO)

run-feature: # Alias for moxi-chunk
	$(MAKE) moxi-chunk

generate-sft-dataset: # Phase 3: chunks → SFT dataset (set OPENAI_API_KEY; optional: CHUNKS=path LIMIT=n)
	cd src && PYTHONPATH=$(PYTHONPATH) python -m moxi_train.generate_sft_dataset $(if $(CHUNKS),--chunks $(CHUNKS)) $(if $(LIMIT),--limit $(LIMIT))

validate-dataset: # Validate README training dataset (sample fields / lengths)
	cd src && PYTHONPATH=$(PYTHONPATH) python -m moxi_data.quality_control.dataset_validator

clean-training-data: # Clean README JSON in data/collection (backup, filter by min length)
	cd src && PYTHONPATH=$(PYTHONPATH) python -m moxi_data.quality_control.clean_dataset_json \
		--data-path ../data/collection/awesome_readme_clean.json \
		--min-length 200 \
		--backup

cleanup-data: # Clean up data/ (legacy script)
	./scripts/cleanup_training_data.sh

# ======================================
# --- Step 3: moxi train (SFT) ---
# ======================================

download-base-model: # Download the base model (Llama-3.2-3B-Instruct)
	cd src && PYTHONPATH=$(PYTHONPATH) poetry run python -m moxi_train.download_model

moxi-train: # Step 3: train SFT model (reads data/sft/) — local GPU
	cd src && PYTHONPATH=$(PYTHONPATH) poetry run python -m moxi_train.finetune.main

train-sft: # Alias for moxi-train
	$(MAKE) moxi-train

train-aws: # Upload data to S3 and print EC2 commands for cloud training (set AWS_S3_BUCKET in .env)
	cd src && PYTHONPATH=$(PYTHONPATH) python ../scripts/run_training_on_aws.py

train-dpo: # Train using Direct Preference Optimization (DPO) - Advanced
	cd src && PYTHONPATH=$(PYTHONPATH) python -m moxi_train.finetune.dpo_trainer

evaluate-model: # Evaluate the trained model
	cd src && PYTHONPATH=$(PYTHONPATH) python -m moxi_train.evaluation.evaluator

clean-invalid-repos: # Clean invalid repositories from cache and training dataset
	cd src && PYTHONPATH=$(PYTHONPATH) python ../scripts/clean_invalid_repos.py

# ======================================
# ---- Pipeline 4: Doc Generator -------
# ======================================

local-generate-docs: # Generate documentation for a repository (usage: make local-generate-docs REPO=https://github.com/user/repo [AUTO_WRITE=--auto-write])
	@if [ -z "$(REPO)" ]; then \
		echo "${YELLOW}Usage: make local-generate-docs REPO=https://github.com/user/repo${RESET}"; \
		echo "${YELLOW}       make local-generate-docs REPO=https://github.com/user/repo AUTO_WRITE=--auto-write${RESET}"; \
		exit 1; \
	fi
	cd src && PYTHONPATH=$(PYTHONPATH) python -m doc_generator.main $(AUTO_WRITE) $(REPO)

compare-models: # Compare custom model vs GPT-4 (A/B testing)
	cd src && PYTHONPATH=$(PYTHONPATH) python -m doc_generator.comparison.ab_testing

# ======================================
# ---------- Web UI (Gradio) -----------
# ======================================
# User-facing: web-ui (setup workflows). Dev-facing: pipeline-dashboard (workflow + counts).

web-ui: # User-facing: one-click setup for auto-documentation on repos
	cd src && PYTHONPATH=$(PYTHONPATH) python -m web_ui.main

# ======================================
# --------- Pipeline 5: CLI ------------
# ======================================

cli-help: # Show CLI help
	cd src && PYTHONPATH=$(PYTHONPATH) python -m cli.main --help

cli-generate: # Generate docs via CLI (usage: make cli-generate REPO=https://github.com/user/repo)
	@if [ -z "$(REPO)" ]; then \
		echo "${YELLOW}Usage: make cli-generate REPO=https://github.com/user/repo${RESET}"; \
		exit 1; \
	fi
	cd src && PYTHONPATH=$(PYTHONPATH) python -m cli.main generate $(REPO)

cli-analyze: # Analyze repo via CLI (usage: make cli-analyze REPO=https://github.com/user/repo)
	@if [ -z "$(REPO)" ]; then \
		echo "${YELLOW}Usage: make cli-analyze REPO=https://github.com/user/repo${RESET}"; \
		exit 1; \
	fi
	cd src && PYTHONPATH=$(PYTHONPATH) python -m cli.main analyze $(REPO)

# ======================================
# ----------- Docker -------------------
# ======================================

docker-build: # Build Docker images
	docker compose -f docker-compose.yml build

docker-up: # Start Docker containers
	docker compose -f docker-compose.yml up -d

docker-down: # Stop Docker containers
	docker compose -f docker-compose.yml down --remove-orphans

docker-logs: # Show Docker logs
	docker compose -f docker-compose.yml logs -f

# ======================================
# ----------- Testing ------------------
# ======================================

test: # Run all tests
	pytest tests/ -v

test-unit: # Run unit tests
	pytest tests/unit/ -v

test-integration: # Run integration tests
	pytest tests/integration/ -v

# ======================================
# ---------- Code Quality --------------
# ======================================

lint: # Run linter (ruff)
	ruff check src/ tests/

format: # Format code with ruff
	ruff format src/ tests/

format-check: # Check formatting without making changes
	ruff format --check src/ tests/

# ======================================
# ----------- Cleanup ------------------
# ======================================

clean: # Clean up temporary files and caches
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info

clean-data: # Clean downloaded data (WARNING: This will delete all data!)
	@echo "${YELLOW}WARNING: This will delete all downloaded data!${RESET}"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		rm -rf data/repos/*; \
		rm -rf training_data/raw/*; \
		rm -rf training_data/processed/*; \
		echo "${GREEN}Data cleaned!${RESET}"; \
	fi

# ======================================
# -------- Full Pipeline Run -----------
# ======================================

run-full-pipeline: # Run the complete pipeline end-to-end (WARNING: This takes hours!)
	@echo "${YELLOW}Starting full pipeline...${RESET}"
	$(MAKE) crawl-github-repos
	@echo "README data: make moxi-collect (writes to data/collection/)"
	$(MAKE) validate-dataset
	$(MAKE) train-sft
	$(MAKE) evaluate-model
	@echo "${GREEN}Pipeline completed!${RESET}"

# Memory monitoring
monitor-memory: # Monitor memory usage in real-time
	@./scripts/monitor_memory.sh

check-memory: # Quick memory check
	@python scripts/check_memory.py

.PHONY: help install install-dev local-start test-config test-logger local-analyze-repo \
        crawl-github-repos validate-dataset \
        download-base-model train-sft train-dpo evaluate-model \
        local-generate-docs compare-models cli-help cli-generate cli-analyze \
        web-ui \
        docker-build docker-up docker-down docker-logs \
        test test-unit test-integration lint format format-check \
        clean clean-data run-full-pipeline monitor-memory check-memory

