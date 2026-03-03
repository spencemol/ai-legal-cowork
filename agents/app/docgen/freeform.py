"""Freeform LLM drafting module (task 7.9).

Generates legal documents from a natural-language prompt and retrieved
context chunks via the LLM gateway.
"""

from __future__ import annotations

_SYSTEM_PROMPT = """\
You are an expert legal document drafter.  Given a drafting request and any
relevant context from the firm's document repository, produce a well-structured,
professionally worded legal document.  Output only the document text — do not
include meta-commentary or explanations outside the document itself.
"""


class FreeformDrafter:
    """Draft legal documents using the LLM gateway.

    Parameters
    ----------
    llm_gateway:
        LLM gateway instance with an ``async complete(prompt, system=None) -> str``
        method (compatible with :class:`~app.gateway.client.LLMGateway`).
    """

    def __init__(self, llm_gateway) -> None:  # noqa: ANN001
        self.gateway = llm_gateway

    async def draft(self, prompt: str, context_chunks: list[dict]) -> str:
        """Generate a legal document from *prompt* and *context_chunks*.

        Parameters
        ----------
        prompt:
            Natural-language drafting instruction
            (e.g. ``"Draft an NDA for Acme Corp and Beta LLC"``).
        context_chunks:
            List of retrieved document chunks from the firm's repository.
            Each chunk should have at least a ``"text"`` key.

        Returns
        -------
        str
            Generated legal document text.
        """
        context_section = ""
        if context_chunks:
            context_lines = "\n\n".join(
                f"[{i + 1}] {chunk['text']}" for i, chunk in enumerate(context_chunks)
            )
            context_section = (
                f"\n\nRelevant context from firm documents:\n\n{context_lines}"
            )

        full_prompt = f"Drafting request: {prompt}{context_section}"

        return await self.gateway.complete(full_prompt, system=_SYSTEM_PROMPT)
