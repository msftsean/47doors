"""Tests for the Oracle gallery service (stage-demo image router)."""

from __future__ import annotations

import base64
import json
from pathlib import Path

import pytest

from app.services import oracle_gallery
from app.services.oracle_gallery import (
    _text_safety_check,
    classify_sentiment,
    get_gallery_image,
)


@pytest.fixture
def fake_gallery(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Build a tiny on-disk gallery with 2 categories and patch module paths."""
    root = tmp_path / "oracle-gallery"
    (root / "institutional").mkdir(parents=True)
    (root / "neutral").mkdir(parents=True)

    # 1x1 transparent PNG bytes — small but a valid file.
    png_bytes = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNgYAAAAAMAASsJTYQAAAAASUVORK5CYII="
    )
    (root / "institutional" / "1.png").write_bytes(png_bytes)
    (root / "neutral" / "1.png").write_bytes(png_bytes)

    manifest = {
        "categories": {
            "institutional": ["institutional/1.png"],
            "neutral": ["neutral/1.png"],
        },
        "generated_at": "2026-04-22T00:00:00Z",
    }
    (root / "manifest.json").write_text(json.dumps(manifest))

    monkeypatch.setattr(oracle_gallery, "GALLERY_ROOT", root)
    monkeypatch.setattr(oracle_gallery, "MANIFEST_PATH", root / "manifest.json")
    oracle_gallery._reset_cache_for_tests()
    yield root
    oracle_gallery._reset_cache_for_tests()


def test_keyword_classifier_routes_library_to_institutional() -> None:
    assert classify_sentiment("a grand library at dusk") == "institutional"


def test_empty_text_falls_back_to_neutral() -> None:
    assert classify_sentiment("") == "neutral"
    assert classify_sentiment("   ") == "neutral"


def test_get_gallery_image_returns_ok(fake_gallery: Path) -> None:
    result = get_gallery_image("a grand library at dusk")
    assert result.status == "ok"
    assert result.image_b64
    # Decodes cleanly — it's the 1x1 PNG we wrote.
    assert base64.b64decode(result.image_b64)


def test_get_gallery_image_missing_file_returns_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Manifest references a file that isn't on disk."""
    root = tmp_path / "broken-gallery"
    root.mkdir()
    (root / "manifest.json").write_text(
        json.dumps(
            {
                "categories": {"neutral": ["neutral/1.png"]},
                "generated_at": "now",
            }
        )
    )
    monkeypatch.setattr(oracle_gallery, "GALLERY_ROOT", root)
    monkeypatch.setattr(oracle_gallery, "MANIFEST_PATH", root / "manifest.json")
    oracle_gallery._reset_cache_for_tests()

    result = get_gallery_image("")  # routes to neutral
    assert result.status == "error"
    assert "missing" in (result.error or "").lower()
    oracle_gallery._reset_cache_for_tests()


def test_text_safety_check_blocks_violence() -> None:
    blocked = _text_safety_check("there was blood everywhere")
    assert blocked is not None
    assert blocked.status == "blocked"
    assert "violence" in (blocked.block_reason or "")


def test_text_safety_check_passes_clean_text() -> None:
    assert _text_safety_check("a quiet library at dusk") is None
