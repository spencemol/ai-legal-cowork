# Legal AI Tool — Python Agent Backend

FastAPI + LangGraph agent backend for the Legal AI desktop application.
Provides the ingestion pipeline (Phase 3), AI chat endpoint (Phase 4), and
multi-agent orchestration (Phases 4 and 7).

---

## Quick Start

```bash
# Install base dependencies (no heavy ML packages)
make install           # uv sync

# Install ML / RAG extras for production use
make install-ml        # sentence-transformers + PyTorch (~500 MB on macOS arm64)
make install-rag       # pinecone + llama-parse
make install-all       # everything

# Start the dev server
make dev               # uvicorn app.main:app --reload  → http://localhost:8000
```

### Makefile targets

| Target | What it does |
|--------|-------------|
| `make install` | `uv sync` — base deps only (tests work without ML extras) |
| `make install-ml` | `uv sync --extra ml` — sentence-transformers + PyTorch |
| `make install-rag` | `uv sync --extra rag` — pinecone + llama-parse |
| `make install-all` | `uv sync --extra all` — full production install |
| `make test` | Full test suite (all 68 tests, quiet) |
| `make test-unit` | Unit tests for all six ingestion modules (verbose) |
| `make test-integration` | Pipeline + endpoint integration tests (verbose) |
| `make test-watch` | Re-run tests on file change (`pytest -f`) |
| `make lint` | `ruff check .` |
| `make lint-fix` | `ruff check --fix .` |
| `make dev` | `uvicorn app.main:app --reload` |

### Required environment variables for `/ingest`

| Variable | Default | Description |
|----------|---------|-------------|
| `NODE_API_URL` | `http://localhost:3000` | Node REST API base URL |
| `NODE_API_JWT` | — | JWT token for Node API calls |
| `PINECONE_API_KEY` | — | Pinecone API key |
| `PINECONE_INDEX` | `legal-docs` | Pinecone index name |
| `LLAMA_CLOUD_API_KEY` | — | LlamaParse (LlamaCloud) API key |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | sentence-transformers model name |

---

## Project Structure

```
agents/
├── app/
│   ├── main.py                  # FastAPI app + route registration
│   ├── rag/                     # Phase 3 — Ingestion Pipeline
│   │   ├── models.py            # Pydantic models shared across the pipeline
│   │   ├── hasher.py            # SHA-256 file hasher
│   │   ├── parser.py            # LlamaParse document parser wrapper
│   │   ├── chunker.py           # Sentence-boundary text chunker
│   │   ├── embedder.py          # sentence-transformers embedding wrapper
│   │   ├── pinecone_store.py    # Pinecone batched upsert wrapper
│   │   ├── api_client.py        # Node REST API HTTP client
│   │   └── ingestion.py         # End-to-end pipeline orchestration
│   └── routes/
│       └── ingest.py            # POST /ingest endpoint
└── tests/
    ├── test_health.py
    └── ingestion/               # Phase 3 test suite
        ├── conftest.py          # Shared fixtures
        ├── test_hasher.py
        ├── test_chunker.py
        ├── test_embedder.py
        ├── test_parser.py
        ├── test_pinecone_store.py
        ├── test_api_client.py
        ├── test_ingestion_integration.py
        └── test_ingest_endpoint.py
```

---

## Phase 3 — Ingestion Pipeline

Implements tasks 3.1–3.11 from `tasks.md`.  The pipeline converts raw document
files into 384-dimensional vectors stored in Pinecone with per-vector metadata
for matter-scoped access control.

### Pipeline Flow

```
POST /ingest
  │  { file_paths: [...], matter_id: "..." }
  │
  ▼
ingest_many()           ── iterates file_paths, returns IngestionResult
  │
  ▼
ingest_document()       ── single file
  │
  ├─ hash_file()                 ─── SHA-256 hex digest  (hasher.py)
  │
  ├─ RestAPIClient               ─── dedup check: GET /matters/:id/documents
  │   └─ skip if file_hash + status="indexed" already exists
  │
  ├─ RestAPIClient               ─── register: POST /matters/:id/documents
  │
  ├─ update_document_status("processing")
  │
  ├─ DocumentParser.parse()      ─── LlamaParse: file → PageContent[]  (parser.py)
  │
  ├─ chunk_text() per page       ─── sentence-boundary chunking         (chunker.py)
  │
  ├─ Embedder.embed()            ─── all-MiniLM-L6-v2 → 384-dim floats  (embedder.py)
  │
  ├─ PineconeStore.upsert()      ─── batched upsert with metadata        (pinecone_store.py)
  │    id:       "{document_id}_{chunk_index}"
  │    metadata: document_id, matter_id, chunk_index, chunk_text,
  │              file_name, page_number, access_level, content_type
  │
  └─ update_document_status("indexed" | "failed")
```

### Module Reference

#### `app/rag/hasher.py` — SHA-256 hasher (task 3.1)

```python
from app.rag.hasher import hash_file

digest = hash_file("/path/to/brief.pdf")   # 64-char hex string
```

Reads in 64 KiB chunks; accepts `str` or `pathlib.Path`.

---

#### `app/rag/parser.py` — Document parser (task 3.2)

```python
from llama_parse import LlamaParse
from app.rag.parser import DocumentParser

llama = LlamaParse(api_key="...", result_type="markdown")
parser = DocumentParser(llama_client=llama)

doc = await parser.parse("/path/to/brief.pdf")
# doc.pages  → list[PageContent(page_number, text)]
# doc.file_hash → SHA-256 digest
```

`llama_client` is injected so tests can pass a fake without an API key.
Page numbers come from `metadata["page_label"]`; falls back to sequential
1-based numbering when the field is absent.

---

#### `app/rag/chunker.py` — Sentence-boundary chunker (task 3.3)

```python
from app.rag.chunker import chunk_text, ChunkConfig

chunks = chunk_text(
    text,
    config=ChunkConfig(max_chars=2048, overlap_chars=256),
    page_number=1,
)
# chunks → list[TextChunk(text, chunk_index, page_number, char_count)]
```

Algorithm:
1. Split text into sentences at terminal-punctuation boundaries (`[.!?]\s+`).
2. Greedily accumulate sentences until `max_chars` would be exceeded.
3. A sentence exceeding `max_chars` alone is emitted as-is (never dropped).
4. Next chunk starts at an overlap point: enough trailing sentences to
   cover ≥ `overlap_chars` characters, with a guaranteed minimum 1-sentence
   advance to prevent infinite loops.

Defaults: `max_chars=2048` (~512 tokens), `overlap_chars=256` (~64 tokens).

---

#### `app/rag/embedder.py` — Embedding module (task 3.4)

```python
from app.rag.embedder import Embedder

# Production (requires uv sync --extra ml)
embedder = Embedder()   # lazy-loads all-MiniLM-L6-v2 on first use

# Testable with injected model
embedder = Embedder(model=my_mock_model)

vectors = embedder.embed(["clause one", "clause two"])
# → list[list[float]], each inner list has 384 elements
```

The real `SentenceTransformer` is imported inside `_get_model()` so the
module is importable without PyTorch.  Accepts both numpy arrays (production)
and plain list-of-lists (test fakes).

---

#### `app/rag/pinecone_store.py` — Pinecone upsert (task 3.5)

```python
from pinecone import Pinecone
from app.rag.pinecone_store import PineconeStore

pc = Pinecone(api_key="...")
store = PineconeStore(index=pc.Index("legal-docs"), batch_size=100)

store.upsert(vector_records)   # list[VectorRecord]
stats = store.describe_stats() # {"total_vector_count": N, ...}
```

`PineconeStore` wraps a `VectorIndex` Protocol (any object with `upsert` and
`describe_index_stats`) so tests inject a `FakeIndex` without an API key.

Pinecone vector schema:

```
id:       "{document_id}_{chunk_index}"
values:   [384-dim float array]
metadata:
  document_id   UUID
  matter_id     UUID
  chunk_index   INT
  chunk_text    STRING  (truncated to 1000 chars)
  file_name     STRING
  page_number   INT | None
  access_level  STRING  ("full" | "restricted" | "read_only")
  content_type  STRING  ("brief" | "transcript" | "email" | "contract" | …)
```

---

#### `app/rag/api_client.py` — Node REST API client (tasks 3.6, 3.7)

```python
from app.rag.api_client import RestAPIClient

client = RestAPIClient(base_url="http://localhost:3000", jwt_token="...")

docs   = await client.get_documents_for_matter("matter-uuid")
doc_id = await client.register_document(matter_id, file_name, file_path, file_hash, mime_type)
await    client.update_document_status(doc_id, "indexed")
```

All methods are async (httpx).  The Node API uses camelCase JSON keys;
`_doc_from_api()` maps both `camelCase` and `snake_case` variants.

---

#### `app/rag/ingestion.py` — Pipeline orchestration (tasks 3.6–3.8)

```python
from app.rag.ingestion import ingest_document, ingest_many

# Single file
doc_id, was_processed = await ingest_document(
    file_path, matter_id, api_client, parser, embedder, pinecone_store
)

# Batch (used by POST /ingest)
result = await ingest_many(file_paths, matter_id, api_client, parser, embedder, pinecone_store)
# result.processed / result.skipped / result.failed
```

**Dedup logic** (task 3.6): calls `get_documents_for_matter`, checks if any
existing doc has the same `file_hash` and `status="indexed"`.  If yes,
returns `(existing_doc_id, False)` without parsing or embedding.

**Status lifecycle** (task 3.7):
```
pending  →  register  →  processing  →  (parse + chunk + embed + upsert)  →  indexed
                                     →  (on any exception)                →  failed
```

---

#### `app/routes/ingest.py` — REST endpoint (task 3.9)

```
POST /ingest
Content-Type: application/json

{
  "file_paths": ["/legal/docs/brief.pdf", "/legal/docs/nda.pdf"],
  "matter_id":  "550e8400-e29b-41d4-a716-446655440000"
}

→ 200 OK
{
  "matter_id":    "550e8400-...",
  "total_files":  2,
  "processed":    1,
  "skipped":      1,
  "failed":       0,
  "document_ids": ["doc-abc", "doc-already-indexed"]
}
```

`run_ingestion()` builds all pipeline dependencies from environment variables.
Tests patch `run_ingestion` directly so the endpoint can be exercised without
running Node API, Pinecone, or LlamaParse.

---

## Running Tests

All 68 tests run without any external service (no Pinecone key, no LlamaParse
API key, no PyTorch required):

```bash
uv run pytest                    # all 68 tests
uv run pytest tests/ingestion/   # Phase 3 tests only (66 tests)
uv run pytest -v --tb=short      # verbose output
```

### Test strategy

| Layer | How mocked |
|-------|-----------|
| LlamaParse (parser) | Injected `FakeLlamaParser` with `aload_data()` |
| sentence-transformers (embedder) | Injected `FakeModel` returning `list[list[float]]` |
| Pinecone (pinecone_store) | Injected `FakeIndex` tracking `upsert` calls |
| Node REST API (api_client) | `mocker.patch("httpx.AsyncClient.get/post/patch")` |
| Full pipeline (ingestion) | All four above combined; `ingest_document` / `ingest_many` |
| `/ingest` endpoint | `patch("app.routes.ingest.run_ingestion")` via `TestClient` |

Heavy dependencies (`sentence-transformers`, `pinecone`, `llama-parse`) are
installed only via `uv sync --extra ml/rag/all` and lazy-imported inside
methods, so the entire test suite runs on the base `uv sync` install.

### Test files

| File | Tests | What it covers |
|------|-------|----------------|
| `test_hasher.py` | 7 | Hex digest, determinism, Path/str, empty file |
| `test_chunker.py` | 13 | max_chars, overlap, sequential indices, page numbers, edge cases |
| `test_embedder.py` | 8 | 384-dim output, batch, model delegation, lazy default |
| `test_parser.py` | 7 | Pages, page numbers, file hash, empty doc, fallback numbering |
| `test_pinecone_store.py` | 7 | IDs, values, metadata, batching, empty input |
| `test_api_client.py` | 7 | GET docs, register, status PATCH, camelCase payload |
| `test_ingestion_integration.py` | 13 | New file, dedup skip, parse error → failed, ingest_many counts |
| `test_ingest_endpoint.py` | 4 | 200 schema, 422 validation, empty list |

---

## Linting

```bash
uv run ruff check .       # lint
uv run ruff check --fix . # auto-fix
```
