PYTEST = .venv/bin/pytest
RUFF   = .venv/bin/ruff

.PHONY: install install-ml install-rag install-all \
        test test-unit test-integration test-watch \
        lint lint-fix dev

# ---------------------------------------------------------------------------
# Dependency management
# ---------------------------------------------------------------------------

install:
	uv sync

install-ml:
	uv sync --extra ml

install-rag:
	uv sync --extra rag

install-all:
	uv sync --extra all

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

## Run the full test suite (base install; all external deps mocked)
test:
	$(PYTEST) -q

## Unit tests only: hasher, chunker, embedder, parser, pinecone_store, api_client
test-unit:
	$(PYTEST) tests/ingestion/test_hasher.py \
	          tests/ingestion/test_chunker.py \
	          tests/ingestion/test_embedder.py \
	          tests/ingestion/test_parser.py \
	          tests/ingestion/test_pinecone_store.py \
	          tests/ingestion/test_api_client.py \
	          -v

## Integration tests: end-to-end pipeline + /ingest endpoint (all mocked)
test-integration:
	$(PYTEST) tests/ingestion/test_ingestion_integration.py \
	          tests/ingestion/test_ingest_endpoint.py \
	          -v

## Watch mode: re-run all tests on file changes
test-watch:
	$(PYTEST) --tb=short -q -f

# ---------------------------------------------------------------------------
# Linting
# ---------------------------------------------------------------------------

lint:
	$(RUFF) check .

lint-fix:
	$(RUFF) check --fix .

# ---------------------------------------------------------------------------
# Dev server
# ---------------------------------------------------------------------------

dev:
	uv run uvicorn app.main:app --reload
