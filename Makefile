SHELL := /bin/bash

.PHONY: lint lint-python lint-r style-r lint-scripts test-biocontainers test

# All tool directories in this repository.
TOOL_DIRS := $(sort $(wildcard tools/*/))

# Override to use a specific planemo executable, e.g.:
# make lint PLANEMO=planemo
PLANEMO ?= planemo
FLAKE8 ?= flake8
R_STYLER ?= ./.github/styler.R

lint:
	@for d in $(TOOL_DIRS); do \
		echo "[lint] $$d"; \
		(cd "$$d" && $(PLANEMO) lint .); \
	done

# Lint Python scripts in all tool directories.
# Matches CI usage of flake8 with flake8-import-order.
lint-python:
	@$(FLAKE8) --version >/dev/null
	@$(FLAKE8) $(TOOL_DIRS)

# Check R formatting/lint via styler in dry-run mode.
lint-r:
	@for d in $(TOOL_DIRS); do \
		echo "[lint-r] $$d"; \
		$(R_STYLER) "$$d" --dry on; \
	done

# Apply styler formatting to R files.
style-r:
	@for d in $(TOOL_DIRS); do \
		echo "[style-r] $$d"; \
		$(R_STYLER) "$$d" --dry off; \
	done

lint-scripts: lint-python lint-r lint

test-biocontainers:
	@for d in $(TOOL_DIRS); do \
		echo "[test-biocontainers] $$d"; \
		(cd "$$d" && $(PLANEMO) test --biocontainers .); \
	done

test:
	@for d in $(TOOL_DIRS); do \
		echo "[test] $$d"; \
		(cd "$$d" && $(PLANEMO) test .); \
	done