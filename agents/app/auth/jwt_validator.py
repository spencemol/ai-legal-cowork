"""JWT validation for FastAPI — verify HS256 tokens from Node REST API (task 4.15).

Reads the shared secret from ``JWT_SECRET`` env-var (same secret used by the
Node REST API).  Invalid or missing tokens raise ``HTTPException(401)``.
"""

from __future__ import annotations

import os

from fastapi import HTTPException, Request
from jose import JWTError, jwt

_ALGORITHM = "HS256"


def _get_secret() -> str:
    secret = os.getenv("JWT_SECRET", "")
    # Return even if empty — the decode step will raise a JWTError (→ 401).
    # We only raise 500 if the application is truly misconfigured and a token
    # successfully decoded with an empty secret (which should never happen with
    # well-formed JWTs).
    return secret


def decode_token(token: str) -> dict:
    """Decode and verify a JWT token.

    Parameters
    ----------
    token:
        Raw JWT string (without ``"Bearer "`` prefix).

    Returns
    -------
    dict
        Decoded payload.

    Raises
    ------
    HTTPException
        401 if the token is missing, malformed, expired, or has an invalid
        signature.
    """
    secret = _get_secret()
    try:
        payload = jwt.decode(token, secret, algorithms=[_ALGORITHM])
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid or expired token: {exc}",
        ) from exc


def extract_bearer_token(request: Request) -> str:
    """Extract the raw JWT from the ``Authorization: Bearer <token>`` header.

    Raises
    ------
    HTTPException
        401 if the header is missing or not in ``Bearer <token>`` format.
    """
    auth_header: str | None = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Authorization header is missing.")

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Authorization header must be in 'Bearer <token>' format.",
        )
    return parts[1]


async def get_current_user(request: Request) -> dict:
    """FastAPI dependency — extract and validate the JWT from the request.

    Usage::

        @router.post("/chat")
        async def chat(user: dict = Depends(get_current_user)):
            ...

    Returns
    -------
    dict
        Decoded JWT payload (includes ``sub``, ``role``, ``matter_ids``, etc.).
    """
    token = extract_bearer_token(request)
    return decode_token(token)
