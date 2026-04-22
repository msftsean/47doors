"""
Oracle image generation service.

Transforms short agent response text into a cinematic visual prompt,
then generates an image via Azure OpenAI Images API (gpt-image-1 / dall-e-3).

Designed for the 47 DOORS NYU ITP/IMA live demo ("THE ORACLE"):
when the voice agent speaks, the screen conjures a matching image.

Content policy violations are surfaced explicitly so the frontend can
render the "BLOCKED" guardrail state — that visual absence is the lesson.
"""

from __future__ import annotations

import base64
import logging
from dataclasses import dataclass
from typing import Literal

from openai import AzureOpenAI, BadRequestError

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def _build_azure_openai_client(api_version: str) -> AzureOpenAI:
    """Build an AzureOpenAI client using API key if set, else managed identity.

    Mirrors the auth fallback in knowledge_service.py — production resources
    with `disableLocalAuth=true` require a bearer token provider.
    """
    settings = get_settings()
    if settings.azure_openai_api_key:
        return AzureOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=api_version,
        )
    from azure.identity import DefaultAzureCredential, get_bearer_token_provider

    credential = DefaultAzureCredential()
    token_provider = get_bearer_token_provider(
        credential, "https://cognitiveservices.azure.com/.default"
    )
    return AzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        azure_ad_token_provider=token_provider,
        api_version=api_version,
    )


@dataclass
class OracleImageResult:
    """Result of an Oracle image generation call."""

    status: Literal["ok", "blocked", "error"]
    # base64-encoded PNG (data URL ready) when status == "ok"
    image_b64: str | None = None
    # The condensed visual prompt actually sent to the image model
    visual_prompt: str | None = None
    # When status == "blocked", the safety / policy reason to display
    block_reason: str | None = None
    # When status == "error", human-readable error message
    error: str | None = None


# ---------------------------------------------------------------------------
# Visual prompt distillation
# ---------------------------------------------------------------------------
# The agent response is operational text ("Your ticket ID is TCK-042...").
# We distill it into a cinematic, emotive visual prompt — a mood, not a
# literal illustration. This is what makes the demo feel like "The Oracle"
# instead of "ChatGPT with pictures."

_VISUAL_STYLE = (
    "Cinematic, ethereal, painterly. Soft volumetric light. "
    "Muted jewel-tones with deep shadow. No text, no letters, no UI. "
    "Editorial photography meets oil painting. 16:9 composition. "
    "Evokes mood and metaphor, never literal."
)


def _distill_visual_prompt(agent_text: str, llm_client: AzureOpenAI, deployment: str) -> str:
    """Use a tiny LLM call to turn agent reply into a visual mood prompt."""
    system = (
        "You are a visual art director translating spoken replies into "
        "one-sentence image prompts. Extract the emotional core and one "
        "concrete metaphor. Never include the literal words of the reply. "
        "Output ONLY the prompt sentence, no preamble, no quotes."
    )
    try:
        resp = llm_client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": agent_text[:500]},
            ],
            max_tokens=80,
            temperature=0.7,
        )
        mood = (resp.choices[0].message.content or "").strip().strip('"')
        if not mood:
            mood = "a figure in warm light, waiting"
        return f"{mood}. {_VISUAL_STYLE}"
    except Exception as exc:  # noqa: BLE001
        logger.warning("Visual prompt distillation failed, using fallback: %s", exc)
        # Fallback: keyword-soup the agent text
        return f"An abstract scene evoking: {agent_text[:120]}. {_VISUAL_STYLE}"


# ---------------------------------------------------------------------------
# Image generation
# ---------------------------------------------------------------------------

def generate_oracle_image(agent_text: str) -> OracleImageResult:
    """Generate an Oracle image for a given agent reply.

    Returns an OracleImageResult whose status indicates ok / blocked / error.
    """
    settings = get_settings()

    if not settings.azure_openai_endpoint:
        return OracleImageResult(status="error", error="Azure OpenAI not configured")

    # LLM client for prompt distillation (reuses the text deployment)
    llm_client = _build_azure_openai_client(settings.azure_openai_api_version)

    visual_prompt = _distill_visual_prompt(
        agent_text, llm_client, settings.azure_openai_deployment
    )

    # Image client — uses the same endpoint / key but a dedicated deployment.
    # Configure via ORACLE_IMAGE_DEPLOYMENT env var (e.g., "gpt-image-1" or "dall-e-3").
    image_deployment = getattr(settings, "oracle_image_deployment", None) or "gpt-image-1"
    image_api_version = "2025-04-01-preview"

    image_client = _build_azure_openai_client(image_api_version)

    # Note: gpt-image-1 uses different params than dall-e-3:
    #   - size: 1024x1024 | 1024x1536 | 1536x1024 | auto (NOT 1792x1024)
    #   - quality: low | medium | high | auto (NOT standard/hd)
    #   - response_format: not supported (returns b64_json by default)
    is_gpt_image = image_deployment.startswith("gpt-image")
    generate_kwargs: dict = {
        "model": image_deployment,
        "prompt": visual_prompt,
        "n": 1,
        "size": "1536x1024" if is_gpt_image else "1792x1024",
    }
    if is_gpt_image:
        generate_kwargs["quality"] = "medium"
    else:
        generate_kwargs["quality"] = "standard"
        generate_kwargs["response_format"] = "b64_json"

    try:
        result = image_client.images.generate(**generate_kwargs)
        b64 = result.data[0].b64_json
        return OracleImageResult(
            status="ok",
            image_b64=b64,
            visual_prompt=visual_prompt,
        )

    except BadRequestError as exc:
        # Azure Content Safety / OpenAI moderation typically raises BadRequestError
        # with a content_policy_violation code. Surface it as a "blocked" state.
        body = getattr(exc, "body", {}) or {}
        code = body.get("code") if isinstance(body, dict) else None
        message = body.get("message") if isinstance(body, dict) else str(exc)
        logger.info("Image generation blocked by policy: %s", message)
        return OracleImageResult(
            status="blocked",
            visual_prompt=visual_prompt,
            block_reason=message or "Content policy violation",
        )

    except Exception as exc:  # noqa: BLE001
        logger.exception("Oracle image generation failed")
        return OracleImageResult(status="error", error=str(exc), visual_prompt=visual_prompt)


def image_b64_to_data_url(b64: str) -> str:
    """Wrap a base64 PNG string as a data URL the browser can render."""
    return f"data:image/png;base64,{b64}"
