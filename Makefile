REPO_DIR := $(shell pwd)
export LOOM_RESULTS_DIR ?= $(REPO_DIR)/results
export LOOM_CONFIGS_DIR ?= $(REPO_DIR)/configs

.PHONY: install install-termux lock upgrade serve scrape demo test ci-check clean

# Positional-arg style for "make scrape <target_name> [<params_json>]"
ifneq (,$(filter scrape,$(MAKECMDGOALS)))
SCRAPE_ARGS := $(wordlist 2, $(words $(MAKECMDGOALS)), $(MAKECMDGOALS))
SCRAPE_TARGET := $(word 1, $(SCRAPE_ARGS))
SCRAPE_PARAMS := $(if $(word 2, $(SCRAPE_ARGS)), $(word 2, $(SCRAPE_ARGS)), {})
%:
	@:
endif

install:
	pip install -e ".[dev,api]"

install-termux:
	pkg install -y python-cryptography python-lxml
	sed -i 's/^include-system-site-packages = false$$/include-system-site-packages = true/' .venv/pyvenv.cfg
	pip install -e ".[dev,api]"
	pip uninstall -y cryptography

serve:
	mkdir -p $(LOOM_RESULTS_DIR)
	uvicorn loom.api.main:app --host 0.0.0.0 --port 8000 --reload

scrape:
	@if [ -z "$(SCRAPE_TARGET)" ]; then \
		echo "Usage: make scrape <target_name> [<params_json>]"; \
		echo "Example: make scrape demo_dom_pagination '{\"page\":1}'"; \
		exit 1; \
	fi
	@echo "Submitting $(SCRAPE_TARGET) job..."
	@JOB=$$(curl -s -X POST http://localhost:8000/jobs \
		-H "Content-Type: application/json" \
		-d '{"target_name":"$(SCRAPE_TARGET)","params":$(SCRAPE_PARAMS)}' \
		| python -c "import sys,json; print(json.load(sys.stdin)['job_id'])"); \
	echo "job_id=$$JOB"; \
	for i in 1 2 3 4 5 6 7 8 9 10; do \
		S=$$(curl -s http://localhost:8000/jobs/$$JOB); \
		echo "$$S"; \
		case "$$S" in *finished*|*failed*) break;; esac; \
		sleep 2; \
	done; \
	echo "Result:"; \
	curl -s http://localhost:8000/jobs/$$JOB/result | python -m json.tool

demo:
	@$(MAKE) --no-print-directory scrape demo_dom_pagination '{"page":1}'

test:
	pytest -q

ci-check:
	ruff check .
	ruff format --check .
	pytest -q

clean:
	rm -rf build dist *.egg-info results/*.json
