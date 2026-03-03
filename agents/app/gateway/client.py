"""LLM Gateway — Claude API wrapper with configurable model, temperature, max_tokens (task 4.1).

The gateway wraps the synchronous ``anthropic`` SDK inside async methods so that
the rest of the codebase can ``await`` LLM calls uniformly.  Streaming is
exposed as an async generator.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator

import anthropic

_DEFAULT_MODEL = "claude-3-5-sonnet-20241022"
_DEFAULT_TEMPERATURE = 0.0
_DEFAULT_MAX_TOKENS = 1024


class LLMGateway:
    """Thin async wrapper around the Anthropic messages API.

    Parameters
    ----------
    model:
        Anthropic model identifier.  Defaults to ``claude-3-5-sonnet-20241022``.
    temperature:
        Sampling temperature (0 – 1).  Defaults to 0.
    max_tokens:
        Maximum tokens to generate.  Defaults to 1024.
    api_key:
        Anthropic API key.  If *None*, the ``ANTHROPIC_API_KEY`` env-var is
        used (standard SDK behaviour).
    """

    def __init__(
        self,
        model: str = _DEFAULT_MODEL,
        temperature: float = _DEFAULT_TEMPERATURE,
        max_tokens: int = _DEFAULT_MAX_TOKENS,
        api_key: str | None = None,
    ) -> None:
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client = anthropic.Anthropic(api_key=api_key)

    # ------------------------------------------------------------------
    # Non-streaming completion
    # ------------------------------------------------------------------

    async def complete(
        self,
        prompt: str,
        system: str | None = None,
    ) -> str:
        """Return the full LLM response as a string.

        Parameters
        ----------
        prompt:
            User-turn text.
        system:
            Optional system prompt.
        """
        kwargs: dict = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system

        # Run sync SDK call in a thread-pool so we don't block the event loop.
        loop = asyncio.get_event_loop()
        message = await loop.run_in_executor(
            None,
            lambda: self._client.messages.create(**kwargs),
        )
        return message.content[0].text

    # ------------------------------------------------------------------
    # Streaming completion
    # ------------------------------------------------------------------

    async def stream(
        self,
        prompt: str,
        system: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """Yield response tokens one-by-one as they arrive.

        Parameters
        ----------
        prompt:
            User-turn text.
        system:
            Optional system prompt.
        """
        kwargs: dict = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system

        loop = asyncio.get_event_loop()
        queue: asyncio.Queue[str | None] = asyncio.Queue()

        def _stream_sync() -> None:
            with self._client.messages.stream(**kwargs) as stream:
                for event in stream:
                    if event.type == "content_block_delta" and hasattr(event, "delta"):
                        delta = event.delta
                        if hasattr(delta, "text"):
                            # Schedule putting on the queue from the thread
                            loop.call_soon_threadsafe(queue.put_nowait, delta.text)
            loop.call_soon_threadsafe(queue.put_nowait, None)  # sentinel

        await loop.run_in_executor(None, _stream_sync)

        while True:
            token = await queue.get()
            if token is None:
                break
            yield token
