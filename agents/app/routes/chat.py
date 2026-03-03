"""POST /chat — FastAPI SSE streaming endpoint (tasks 4.11, 4.12, 4.15, 4.16).

Flow:
  1. Validate JWT → extract user context.
  2. Extract matter assignments for the user.
  3. Redact PII from the query before sending to LLM.
  4. Run orchestrator agent (retrieval → generate).
  5. Re-hydrate PII in the answer based on user access level.
  6. Stream tokens back to the client as SSE events.
  7. Send a final ``citations`` SSE event.
"""

from __future__ import annotations

import json
import os
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from app.auth.jwt_validator import get_current_user
from app.gateway.client import LLMGateway
from app.gateway.sanitizer import InputSanitizer
from app.pii.redactor import PIIRedactor, PIIRehydrator

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class ChatRequest(BaseModel):
    """Request body for POST /chat."""

    query: str
    matter_id: str
    thread_id: str | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_gateway() -> LLMGateway:
    """Build LLM gateway from environment variables."""
    return LLMGateway(
        model=os.getenv("LLM_MODEL", "claude-3-5-sonnet-20241022"),
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.0")),
        max_tokens=int(os.getenv("LLM_MAX_TOKENS", "1024")),
    )


async def _build_orchestrator(gateway: LLMGateway):
    """Lazily build the orchestrator agent (avoids import-time heavy deps)."""
    try:
        from pinecone import Pinecone  # type: ignore[import]

        from app.agents.orchestrator import OrchestratorAgent
        from app.agents.retrieval_agent import RetrievalAgent
        from app.rag.embedder import Embedder
        from app.retrieval.reranker import BGEReranker
        from app.retrieval.retriever import PineconeRetriever

        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY", ""))
        index = pc.Index(os.getenv("PINECONE_INDEX", "legal-docs"))
        embedder = Embedder(model_name=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"))

        retriever = PineconeRetriever(index=index, embedder=embedder)
        reranker = BGEReranker()
        retrieval_agent = RetrievalAgent(
            retriever=retriever,
            reranker=reranker,
            gateway=gateway,
        )
        return OrchestratorAgent(
            retrieval_agent=retrieval_agent,
            gateway=gateway,
        )
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Required dependency not installed: {exc}",
        ) from exc


def _check_matter_access(user: dict, matter_id: str) -> str:
    """Verify the user has access to *matter_id* and return their access level.

    Returns the user's access level string for the matter.

    Raises
    ------
    HTTPException
        403 if the user does not have access to the requested matter.
    """
    user_matter_ids: list[str] = user.get("matter_ids", [])
    if matter_id not in user_matter_ids:
        raise HTTPException(
            status_code=403,
            detail=f"You do not have access to matter {matter_id}.",
        )
    # Return role-based access level
    role = user.get("role", "viewer")
    if role in ("admin", "attorney"):
        return "full"
    elif role in ("paralegal", "associate"):
        return "restricted"
    else:
        return "read_only"


# ---------------------------------------------------------------------------
# Route handler
# ---------------------------------------------------------------------------


@router.post("/chat")
async def chat_endpoint(
    request: ChatRequest,
    user: dict = Depends(get_current_user),
) -> EventSourceResponse:
    """Stream a chat response as Server-Sent Events.

    Events emitted:
    - ``token`` — each text token as it is generated
    - ``citations`` — final JSON array of citations
    - ``error`` — if something goes wrong mid-stream
    """
    access_level = _check_matter_access(user, request.matter_id)

    sanitizer = InputSanitizer()
    san_result = sanitizer.check(request.query)
    if not san_result.is_safe:
        raise HTTPException(
            status_code=400,
            detail=f"Potentially malicious input detected: {san_result.flagged_patterns}",
        )

    redactor = PIIRedactor()
    redaction_result = redactor.redact(san_result.sanitized_text)
    redacted_query = redaction_result.redacted_text
    pii_mapping = redaction_result.mapping

    gateway = _build_gateway()

    async def event_stream() -> AsyncGenerator[dict, None]:
        try:
            orchestrator = await _build_orchestrator(gateway)
            result = await orchestrator.run(
                query=redacted_query,
                matter_id=request.matter_id,
                access_level=access_level,
            )

            answer: str = result.get("answer", "")
            citations: list = result.get("citations", [])

            # Re-hydrate PII in the answer
            rehydrator = PIIRehydrator()
            answer = rehydrator.rehydrate(answer, pii_mapping, access_level=access_level)

            # Stream answer tokens word-by-word (for mock-testable chunking)
            for token in answer.split():
                yield {"event": "token", "data": token + " "}

            # Final citations event
            yield {"event": "citations", "data": json.dumps(citations)}

        except HTTPException:
            raise
        except Exception as exc:  # pragma: no cover
            yield {"event": "error", "data": str(exc)}

    return EventSourceResponse(event_stream())
