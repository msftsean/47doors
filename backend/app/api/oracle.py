"""
Oracle API — image generation endpoint for the NYU ITP/IMA live demo.

Two endpoints:

  POST /api/oracle/image
    Body: {"text": "<agent response text>"}
    Returns: {"status": "ok|blocked|error", "image": "<data-url>"?, "reason": "..."?}

  POST /api/oracle/provoke
    Test-only helper that pushes a synthetic agent_speech event onto the
    transcript bus so presenters can rehearse without holding a phone.
    Disabled in production.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.services.oracle_service import (
    generate_oracle_image,
    image_b64_to_data_url,
)
from app.services.transcript_bus import transcript_bus

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class OracleImageRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)
    # Optional caller-supplied hint; useful for staged demo scripts
    mood_hint: str | None = Field(default=None, max_length=200)


class OracleImageResponse(BaseModel):
    status: str
    image: str | None = None
    visual_prompt: str | None = None
    reason: str | None = None
    error: str | None = None


class ProvokeRequest(BaseModel):
    """Push a synthetic event into the transcript bus for demo rehearsal."""

    kind: str = Field(..., pattern="^(user_speech|agent_speech|tool_call)$")
    text: str = Field(..., min_length=1, max_length=1000)
    call_id: str | None = None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/image", response_model=OracleImageResponse)
async def oracle_image(req: OracleImageRequest) -> OracleImageResponse:
    """Generate a cinematic image from an agent reply.

    Safe to call repeatedly — each request is independent.
    """
    # Optionally prepend a mood hint so the Oracle can emphasize a theme
    # (e.g., "doors opening", "listening figure") for a specific demo beat.
    composed = req.text
    if req.mood_hint:
        composed = f"{req.text}\n\nMood hint for the image: {req.mood_hint}"

    result = generate_oracle_image(composed)

    if result.status == "ok" and result.image_b64:
        return OracleImageResponse(
            status="ok",
            image=image_b64_to_data_url(result.image_b64),
            visual_prompt=result.visual_prompt,
        )
    if result.status == "blocked":
        return OracleImageResponse(
            status="blocked",
            visual_prompt=result.visual_prompt,
            reason=result.block_reason,
        )
    return OracleImageResponse(
        status="error",
        visual_prompt=result.visual_prompt,
        error=result.error,
    )


@router.post("/provoke")
async def oracle_provoke(req: ProvokeRequest) -> dict[str, str]:
    """Push a synthetic transcript event onto the bus (demo rehearsal only)."""
    settings = get_settings()
    if settings.environment == "production":
        raise HTTPException(status_code=403, detail="Disabled in production")

    call_id = req.call_id or f"rehearsal-{uuid4().hex[:8]}"
    event = {
        "type": req.kind,
        "call_id": call_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "text": req.text,
    }
    if req.kind == "tool_call":
        event = {
            "type": "tool_call",
            "call_id": call_id,
            "timestamp": event["timestamp"],
            "tool": "rehearsal_tool",
            "summary": req.text,
        }
    await transcript_bus.publish(event)
    return {"status": "published", "call_id": call_id}
