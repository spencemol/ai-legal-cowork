"""Shared fixtures for Phase 7 tests — Research & Drafting Agents."""

from __future__ import annotations

import pytest


@pytest.fixture()
def sample_chunks() -> list[dict]:
    """Sample firm document chunks for use in tests."""
    return [
        {
            "doc_id": "doc-001",
            "chunk_id": "chunk-001",
            "text": "The defendant breached the contract on January 1, 2024.",
            "page": 1,
            "file_name": "contract.pdf",
            "matter_id": "matter-001",
        },
        {
            "doc_id": "doc-002",
            "chunk_id": "chunk-002",
            "text": "Damages were assessed at $500,000 under applicable law.",
            "page": 3,
            "file_name": "damages_report.pdf",
            "matter_id": "matter-001",
        },
    ]


@pytest.fixture()
def sample_web_results() -> list[dict]:
    """Sample web search results."""
    return [
        {
            "title": "Contract Breach Law Overview",
            "url": "https://example.com/contract-breach",
            "snippet": "Contract breach occurs when one party fails to perform...",
        },
        {
            "title": "Damages in Contract Law",
            "url": "https://example.com/damages",
            "snippet": "Expectation damages aim to put the non-breaching party...",
        },
    ]


@pytest.fixture()
def sample_legal_db_results() -> list[dict]:
    """Sample legal database results."""
    return [
        {
            "title": "Smith v. Jones",
            "citation": "123 F.3d 456 (9th Cir. 2020)",
            "snippet": "The court held that breach of contract requires...",
            "source": "westlaw",
            "url": "https://westlaw.example.com/smith-v-jones",
        },
    ]


@pytest.fixture()
def nda_context() -> dict:
    """Sample context for NDA template rendering."""
    return {
        "party_a": "Acme Corporation",
        "party_b": "Beta LLC",
        "effective_date": "March 1, 2026",
        "duration": "2 years",
        "governing_law": "California",
    }


@pytest.fixture()
def engagement_letter_context() -> dict:
    """Sample context for engagement letter template rendering."""
    return {
        "client_name": "John Doe",
        "matter_title": "Contract Dispute",
        "attorney_name": "Jane Smith",
        "date": "March 1, 2026",
        "firm_name": "Smith & Associates",
    }


@pytest.fixture()
def motion_context() -> dict:
    """Sample context for motion template rendering."""
    return {
        "case_number": "2026-CV-00123",
        "court_name": "Superior Court of California",
        "plaintiff": "Acme Corporation",
        "defendant": "Beta LLC",
        "motion_type": "Motion for Summary Judgment",
        "attorney_name": "Jane Smith",
        "date": "March 1, 2026",
    }
