"""
Oracle gallery service — pre-baked image selection for the stage demo.

Live gpt-image-1 generation costs ~60s per image, which kills the pacing of a
stage demo. This module serves images from a pre-baked, on-disk gallery
(`backend/data/oracle-gallery/{category}/{N}.png`) selected by a cheap
keyword-first sentiment classifier with an LLM fallback.

Same response shape as `oracle_service.generate_oracle_image` so the frontend
sees no difference.
"""

from __future__ import annotations

import base64
import json
import logging
import threading
from collections import defaultdict
from pathlib import Path

from app.core.config import get_settings
from app.services.oracle_service import (
    OracleImageResult,
    _build_azure_openai_client,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GALLERY_ROOT = Path(__file__).resolve().parents[2] / "data" / "oracle-gallery"
MANIFEST_PATH = GALLERY_ROOT / "manifest.json"

CATEGORIES = (
    "wonder",
    "institutional",
    "melancholy",
    "warning",
    "chaos",
    "bloom",
    "dream",
    "neutral",
)

# Tie-break order when keyword scores are equal. Institutional first because
# the Tisch demo question must always land there; neutral last as the safe
# default.
_PRIORITY = (
    "institutional",
    "wonder",
    "dream",
    "bloom",
    "melancholy",
    "warning",
    "chaos",
    "neutral",
)

_KEYWORD_MAP: dict[str, list[str]] = {
    "institutional": [
        "school", "university", "tisch", "stern", "program", "class",
        "academic", "admission", "requirement", "major", "library", "hall",
        "lecture", "campus", "department", "faculty", "registrar",
    ],
    "wonder": [
        "lantern", "mirror", "door", "key", "vast", "corridor", "threshold",
        "question", "curious", "wonder", "open", "discovery",
    ],
    "dream": [
        "floating", "still water", "cloud", "spiral", "music", "season",
        "surreal", "dream", "twilight", "ethereal",
    ],
    "bloom": [
        "flower", "dawn", "ascend", "rise", "spiral", "growth",
        "luminous", "blossom", "bloom", "petal", "sunrise",
    ],
    "melancholy": [
        "candle", "empty", "wilting", "alone", "fade", "dim", "shadow",
        "silence", "lonely", "abandoned", "hollow", "grief",
    ],
    "warning": [
        "match", "frayed", "trembl", "ajar", "brittle", "bleeding", "edge",
        "warning", "caution", "fragile",
    ],
    "chaos": [
        "splinter", "fall", "crash", "break", "tear", "storm", "collapse",
        "shatter", "fracture", "chaos", "torn",
    ],
    "neutral": [
        "balanced", "calm", "quiet", "still", "gentle", "soft", "ordinary",
        "neutral", "stone", "sphere",
    ],
}


# ---------------------------------------------------------------------------
# Manifest loading (cached)
# ---------------------------------------------------------------------------

_manifest_cache: dict | None = None
_manifest_lock = threading.Lock()
_rotation_counters: dict[str, int] = defaultdict(int)
_rotation_lock = threading.Lock()


def _load_manifest() -> dict:
    """Load and cache manifest.json. Returns empty mapping if missing."""
    global _manifest_cache
    if _manifest_cache is not None:
        return _manifest_cache
    with _manifest_lock:
        if _manifest_cache is not None:
            return _manifest_cache
        if not MANIFEST_PATH.exists():
            logger.warning(
                "Oracle gallery manifest not found at %s — "
                "gallery mode will return errors until generate_gallery.py runs.",
                MANIFEST_PATH,
            )
            _manifest_cache = {"categories": {}}
        else:
            try:
                _manifest_cache = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
            except Exception as exc:  # noqa: BLE001
                logger.exception("Failed to parse oracle gallery manifest: %s", exc)
                _manifest_cache = {"categories": {}}
        return _manifest_cache


def _reset_cache_for_tests() -> None:
    """Test-only helper to clear the in-process manifest cache."""
    global _manifest_cache
    with _manifest_lock:
        _manifest_cache = None
    with _rotation_lock:
        _rotation_counters.clear()


# ---------------------------------------------------------------------------
# Sentiment classification
# ---------------------------------------------------------------------------


def _score_keywords(text: str) -> dict[str, int]:
    """Count keyword hits per category in lowercased text."""
    lowered = text.lower()
    scores: dict[str, int] = {}
    for category, keywords in _KEYWORD_MAP.items():
        scores[category] = sum(1 for kw in keywords if kw in lowered)
    return scores


def _classify_keywords(text: str) -> str | None:
    """Return best category by keyword score, or None if zero hits."""
    scores = _score_keywords(text)
    if not any(scores.values()):
        return None
    best_score = max(scores.values())
    tied = [c for c, s in scores.items() if s == best_score]
    if len(tied) == 1:
        return tied[0]
    for c in _PRIORITY:
        if c in tied:
            return c
    return tied[0]


def _classify_llm(text: str) -> str:
    """LLM fallback when no keywords matched. Returns one of CATEGORIES."""
    settings = get_settings()
    if not settings.azure_openai_endpoint:
        return "neutral"
    try:
        client = _build_azure_openai_client(settings.azure_openai_api_version)
        slugs = ", ".join(CATEGORIES)
        resp = client.chat.completions.create(
            model=settings.azure_openai_deployment,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Classify the mood of the following sentence into "
                        f"exactly one of these slugs: {slugs}. "
                        "Reply with ONLY the slug, lowercase, no punctuation."
                    ),
                },
                {"role": "user", "content": text[:300]},
            ],
            max_tokens=10,
            temperature=0.0,
        )
        raw = (resp.choices[0].message.content or "").strip().lower()
        for c in CATEGORIES:
            if c in raw:
                return c
    except Exception as exc:  # noqa: BLE001
        logger.warning("LLM sentiment fallback failed, using neutral: %s", exc)
    return "neutral"


def classify_sentiment(text: str) -> str:
    """Classify vision_text into one of the 8 gallery categories."""
    if not text or not text.strip():
        return "neutral"
    kw = _classify_keywords(text)
    if kw is not None:
        return kw
    return _classify_llm(text)


# ---------------------------------------------------------------------------
# Image selection
# ---------------------------------------------------------------------------


def _pick_image_path(category: str) -> Path | None:
    """Round-robin pick a file path for the category from the manifest."""
    manifest = _load_manifest()
    files = manifest.get("categories", {}).get(category, [])
    if not files:
        return None
    with _rotation_lock:
        idx = _rotation_counters[category] % len(files)
        _rotation_counters[category] += 1
    return GALLERY_ROOT / files[idx]


# ---------------------------------------------------------------------------
# Text safety check (gallery-mode replacement for image Content Safety)
# ---------------------------------------------------------------------------

# Maps hard-stop keyword -> safety category tag that the frontend's BLOCKED
# overlay renders. Kept tiny and deterministic so the violence demo still
# fires reliably on stage.
_SAFETY_KEYWORDS: dict[str, str] = {
    "stab": "violence",
    "blood": "violence",
    "wound": "violence",
    "kill": "violence",
    "rape": "sexual",
    "nazi": "abuse",
    "nude": "sexual",
    "sexual": "sexual",
}


def _text_safety_check(agent_text: str) -> OracleImageResult | None:
    """Return a blocked OracleImageResult if agent_text trips a safety keyword.

    Gallery mode skips Content Safety on the image (we're not generating one),
    but we still want the BLOCKED overlay to fire for the stage violence demo.
    Returns None when text is safe.
    """
    if not agent_text:
        return None
    lowered = agent_text.lower()
    hits: list[str] = []
    for kw, tag in _SAFETY_KEYWORDS.items():
        if kw in lowered and tag not in hits:
            hits.append(tag)
    if not hits:
        return None
    reason = f"safety_violations=[{'|'.join(hits)}]"
    logger.info("Gallery mode text safety block: %s", reason)
    return OracleImageResult(
        status="blocked",
        block_reason=reason,
        visual_prompt=agent_text[:200],
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def get_gallery_image(vision_text: str) -> OracleImageResult:
    """Return a pre-baked image based on vision_text sentiment classification."""
    category = classify_sentiment(vision_text)
    path = _pick_image_path(category)

    if path is None:
        msg = f"No gallery images registered for category '{category}'"
        logger.error(msg)
        return OracleImageResult(
            status="error",
            error=msg,
            visual_prompt=vision_text,
        )

    if not path.exists():
        msg = f"Gallery file missing on disk: {path}"
        logger.error(msg)
        return OracleImageResult(
            status="error",
            error=msg,
            visual_prompt=vision_text,
        )

    try:
        b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to read gallery image %s", path)
        return OracleImageResult(
            status="error",
            error=f"Could not read gallery image: {exc}",
            visual_prompt=vision_text,
        )

    logger.info("Oracle gallery hit: category=%s file=%s", category, path.name)
    return OracleImageResult(
        status="ok",
        image_b64=b64,
        visual_prompt=vision_text,
    )
