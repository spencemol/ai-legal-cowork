"""Integration tests for the end-to-end ingestion pipeline (tasks 3.8, 3.9, 3.10, 3.11).

Mocks:
  - DocumentParser      (no LlamaParse API key needed)
  - Embedder            (no sentence-transformers / PyTorch needed)
  - PineconeStore index (no Pinecone API key needed)
  - RestAPIClient HTTP  (no running Node API needed)

RED: These tests fail until all ingestion modules are implemented.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.rag.api_client import RestAPIClient
from app.rag.embedder import Embedder
from app.rag.ingestion import ingest_document, ingest_many
from app.rag.models import DocumentInfo, PageContent, ParsedDocument
from app.rag.parser import DocumentParser
from app.rag.pinecone_store import PineconeStore

# ---------------------------------------------------------------------------
# Helper: build a fake parsed document for a given file path
# ---------------------------------------------------------------------------


def make_parsed_doc(file_path: str, file_hash: str) -> ParsedDocument:
    return ParsedDocument(
        file_path=file_path,
        file_hash=file_hash,
        pages=[
            PageContent(
                page_number=1,
                text=(
                    "The plaintiff alleges breach of contract. "
                    "The defendant denies the claim. "
                    "Parties will attend mediation next month."
                ),
            )
        ],
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_index():
    idx = MagicMock()
    idx.upsert = MagicMock()
    idx.describe_index_stats = MagicMock(return_value={"total_vector_count": 3})
    return idx


@pytest.fixture
def pinecone_store(fake_index):
    return PineconeStore(index=fake_index)


@pytest.fixture
def fake_model():
    class FakeModel:
        """Returns plain list-of-lists so numpy is not required."""

        def encode(self, texts, **kwargs):
            return [[0.0] * 384 for _ in texts]

    return FakeModel()


@pytest.fixture
def embedder(fake_model):
    return Embedder(model=fake_model)


# ---------------------------------------------------------------------------
# Task 3.8 — end-to-end ingest_document
# ---------------------------------------------------------------------------


class TestIngestDocumentNewFile:
    """New file: not previously indexed → full pipeline runs."""

    @pytest.fixture
    def new_pdf(self, tmp_path):
        f = tmp_path / "contract.pdf"
        f.write_bytes(b"%PDF fake content for hashing")
        return str(f)

    @pytest.fixture
    def parser(self, new_pdf):
        """Parser that returns a fake parsed document."""
        client = MagicMock()
        client.aload_data = AsyncMock(
            return_value=[
                MagicMock(
                    text="The plaintiff alleges breach. The defendant denies it.",
                    metadata={"page_label": "1"},
                )
            ]
        )
        return DocumentParser(llama_client=client)

    @pytest.fixture
    def api_client(self, new_pdf, mocker):
        client = MagicMock(spec=RestAPIClient)
        client.get_documents_for_matter = AsyncMock(return_value=[])
        client.register_document = AsyncMock(return_value="doc-new-001")
        client.update_document_status = AsyncMock()
        return client

    async def test_returns_document_id_and_processed_true(
        self, new_pdf, parser, embedder, pinecone_store, api_client
    ):
        doc_id, was_processed = await ingest_document(
            file_path=new_pdf,
            matter_id="matter-001",
            api_client=api_client,
            parser=parser,
            embedder=embedder,
            pinecone_store=pinecone_store,
        )
        assert doc_id == "doc-new-001"
        assert was_processed is True

    async def test_registers_document_with_api(
        self, new_pdf, parser, embedder, pinecone_store, api_client
    ):
        await ingest_document(
            file_path=new_pdf,
            matter_id="matter-001",
            api_client=api_client,
            parser=parser,
            embedder=embedder,
            pinecone_store=pinecone_store,
        )
        api_client.register_document.assert_called_once()
        call_kwargs = api_client.register_document.call_args.kwargs
        assert call_kwargs["matter_id"] == "matter-001"
        assert call_kwargs["file_name"] == "contract.pdf"

    async def test_status_updated_to_processing_then_indexed(
        self, new_pdf, parser, embedder, pinecone_store, api_client
    ):
        await ingest_document(
            file_path=new_pdf,
            matter_id="matter-001",
            api_client=api_client,
            parser=parser,
            embedder=embedder,
            pinecone_store=pinecone_store,
        )
        calls = [call.kwargs["status"] for call in api_client.update_document_status.call_args_list]
        assert "processing" in calls
        assert "indexed" in calls
        assert calls.index("processing") < calls.index("indexed")

    async def test_vectors_upserted_to_pinecone(
        self, new_pdf, parser, embedder, pinecone_store, fake_index, api_client
    ):
        await ingest_document(
            file_path=new_pdf,
            matter_id="matter-001",
            api_client=api_client,
            parser=parser,
            embedder=embedder,
            pinecone_store=pinecone_store,
        )
        fake_index.upsert.assert_called()

    async def test_vector_ids_use_document_id(
        self, new_pdf, parser, embedder, pinecone_store, fake_index, api_client
    ):
        await ingest_document(
            file_path=new_pdf,
            matter_id="matter-001",
            api_client=api_client,
            parser=parser,
            embedder=embedder,
            pinecone_store=pinecone_store,
        )
        batch = fake_index.upsert.call_args.kwargs["vectors"]
        assert all(v["id"].startswith("doc-new-001_") for v in batch)

    async def test_vector_metadata_includes_matter_id(
        self, new_pdf, parser, embedder, pinecone_store, fake_index, api_client
    ):
        await ingest_document(
            file_path=new_pdf,
            matter_id="matter-001",
            api_client=api_client,
            parser=parser,
            embedder=embedder,
            pinecone_store=pinecone_store,
        )
        batch = fake_index.upsert.call_args.kwargs["vectors"]
        for v in batch:
            assert v["metadata"]["matter_id"] == "matter-001"


class TestIngestDocumentDedup:
    """Same file hash already indexed → skip without re-embedding."""

    @pytest.fixture
    def existing_pdf(self, tmp_path):
        f = tmp_path / "existing.pdf"
        f.write_bytes(b"%PDF existing content")
        return str(f)

    @pytest.fixture
    def api_client_with_existing_doc(self, existing_pdf):
        from app.rag.hasher import hash_file

        existing_hash = hash_file(existing_pdf)
        existing = DocumentInfo(
            id="doc-existing-001",
            file_name="existing.pdf",
            file_path=existing_pdf,
            file_hash=existing_hash,
            status="indexed",
            matter_id="matter-001",
        )
        client = MagicMock(spec=RestAPIClient)
        client.get_documents_for_matter = AsyncMock(return_value=[existing])
        client.register_document = AsyncMock()
        client.update_document_status = AsyncMock()
        return client

    async def test_returns_existing_doc_id_and_processed_false(
        self, existing_pdf, api_client_with_existing_doc, embedder, pinecone_store
    ):
        parser = MagicMock()  # should not be called
        doc_id, was_processed = await ingest_document(
            file_path=existing_pdf,
            matter_id="matter-001",
            api_client=api_client_with_existing_doc,
            parser=parser,
            embedder=embedder,
            pinecone_store=pinecone_store,
        )
        assert doc_id == "doc-existing-001"
        assert was_processed is False

    async def test_parser_not_called_for_dedup(
        self, existing_pdf, api_client_with_existing_doc, embedder, pinecone_store
    ):
        parser = MagicMock(spec=DocumentParser)
        parser.parse = AsyncMock()

        await ingest_document(
            file_path=existing_pdf,
            matter_id="matter-001",
            api_client=api_client_with_existing_doc,
            parser=parser,
            embedder=embedder,
            pinecone_store=pinecone_store,
        )
        parser.parse.assert_not_called()

    async def test_pinecone_not_called_for_dedup(
        self, existing_pdf, api_client_with_existing_doc, embedder, fake_index
    ):
        pinecone_store = PineconeStore(index=fake_index)
        parser = MagicMock(spec=DocumentParser)
        parser.parse = AsyncMock()

        await ingest_document(
            file_path=existing_pdf,
            matter_id="matter-001",
            api_client=api_client_with_existing_doc,
            parser=parser,
            embedder=embedder,
            pinecone_store=pinecone_store,
        )
        fake_index.upsert.assert_not_called()


class TestIngestDocumentFailure:
    """On parsing error → status set to 'failed', exception re-raised."""

    @pytest.fixture
    def bad_pdf(self, tmp_path):
        f = tmp_path / "bad.pdf"
        f.write_bytes(b"corrupted content")
        return str(f)

    @pytest.fixture
    def api_client_empty(self):
        client = MagicMock(spec=RestAPIClient)
        client.get_documents_for_matter = AsyncMock(return_value=[])
        client.register_document = AsyncMock(return_value="doc-bad-001")
        client.update_document_status = AsyncMock()
        return client

    async def test_status_set_to_failed_on_parser_error(
        self, bad_pdf, api_client_empty, embedder, pinecone_store
    ):
        parser = MagicMock(spec=DocumentParser)
        parser.parse = AsyncMock(side_effect=RuntimeError("parse failed"))

        with pytest.raises(RuntimeError, match="parse failed"):
            await ingest_document(
                file_path=bad_pdf,
                matter_id="matter-001",
                api_client=api_client_empty,
                parser=parser,
                embedder=embedder,
                pinecone_store=pinecone_store,
            )

        calls = [call.kwargs["status"] for call in api_client_empty.update_document_status.call_args_list]
        assert "failed" in calls


# ---------------------------------------------------------------------------
# Task 3.9 — POST /ingest endpoint via ingest_many helper
# ---------------------------------------------------------------------------


class TestIngestMany:
    @pytest.fixture
    def three_pdfs(self, tmp_path):
        files = []
        for i in range(3):
            f = tmp_path / f"doc_{i}.pdf"
            f.write_bytes(f"PDF content {i}".encode())
            files.append(str(f))
        return files

    @pytest.fixture
    def api_client_all_new(self):
        client = MagicMock(spec=RestAPIClient)
        client.get_documents_for_matter = AsyncMock(return_value=[])
        client.register_document = AsyncMock(side_effect=[f"doc-{i}" for i in range(3)])
        client.update_document_status = AsyncMock()
        return client

    @pytest.fixture
    def parser_all_ok(self):
        client = MagicMock()
        client.aload_data = AsyncMock(
            return_value=[
                MagicMock(text="Legal text.", metadata={"page_label": "1"})
            ]
        )
        return DocumentParser(llama_client=client)

    async def test_returns_ingestion_result(
        self, three_pdfs, api_client_all_new, parser_all_ok, embedder, pinecone_store
    ):
        from app.rag.ingestion import ingest_many

        result = await ingest_many(
            file_paths=three_pdfs,
            matter_id="matter-001",
            api_client=api_client_all_new,
            parser=parser_all_ok,
            embedder=embedder,
            pinecone_store=pinecone_store,
        )

        assert result.total_files == 3
        assert result.processed == 3
        assert result.skipped == 0
        assert result.failed == 0
        assert len(result.document_ids) == 3

    async def test_counts_skipped_files(
        self, three_pdfs, embedder, pinecone_store
    ):
        """First file already indexed (dedup) → skipped=1, processed=2."""
        from app.rag.hasher import hash_file

        # Only the first file is "already indexed"
        first_hash = hash_file(three_pdfs[0])
        existing = DocumentInfo(
            id="doc-already",
            file_name="doc_0.pdf",
            file_path=three_pdfs[0],
            file_hash=first_hash,
            status="indexed",
            matter_id="matter-001",
        )

        client = MagicMock(spec=RestAPIClient)
        client.get_documents_for_matter = AsyncMock(return_value=[existing])
        client.register_document = AsyncMock(side_effect=["doc-1", "doc-2"])
        client.update_document_status = AsyncMock()

        llama_client = MagicMock()
        llama_client.aload_data = AsyncMock(
            return_value=[MagicMock(text="text", metadata={"page_label": "1"})]
        )
        parser = DocumentParser(llama_client=llama_client)

        result = await ingest_many(
            file_paths=three_pdfs,
            matter_id="matter-001",
            api_client=client,
            parser=parser,
            embedder=embedder,
            pinecone_store=pinecone_store,
        )

        assert result.skipped == 1
        assert result.processed == 2
        assert result.failed == 0

    async def test_counts_failed_files(self, three_pdfs, embedder, pinecone_store):
        """One file fails to parse → failed=1, others succeed."""
        call_count = [0]

        async def mock_register(*args, **kwargs):
            call_count[0] += 1
            return f"doc-{call_count[0]}"

        client = MagicMock(spec=RestAPIClient)
        client.get_documents_for_matter = AsyncMock(return_value=[])
        client.register_document = AsyncMock(side_effect=mock_register)
        client.update_document_status = AsyncMock()

        parse_call = [0]

        async def parse_side_effect(fp):
            parse_call[0] += 1
            if parse_call[0] == 2:
                raise RuntimeError("parse error")
            return ParsedDocument(
                file_path=fp,
                file_hash="hash",
                pages=[PageContent(page_number=1, text="some legal text")],
            )

        parser = MagicMock(spec=DocumentParser)
        parser.parse = AsyncMock(side_effect=parse_side_effect)

        result = await ingest_many(
            file_paths=three_pdfs,
            matter_id="matter-001",
            api_client=client,
            parser=parser,
            embedder=embedder,
            pinecone_store=pinecone_store,
        )

        assert result.failed == 1
        assert result.processed + result.skipped == 2
        assert result.total_files == 3
