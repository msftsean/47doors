"""
One-shot CLI script to bake the Oracle stage-demo gallery.

Generates 8 categories × 3 prompt variants = 24 PNGs into
backend/data/oracle-gallery/{category}/{N}.png and writes a manifest.json.

Resumable: skips files that already exist, so a rate-limit interruption
just means re-running.

Usage:
    cd backend
    python -m scripts.generate_gallery
    # or:
    python scripts/generate_gallery.py

Requires Azure OpenAI env vars (same as the runtime — see .env.example):
    AZURE_OPENAI_ENDPOINT
    AZURE_OPENAI_API_KEY        (or managed identity)
    ORACLE_IMAGE_DEPLOYMENT     (default "gpt-image-1")

Costs real money and ~20 minutes — do not run from automation.
"""

from __future__ import annotations

import base64
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Make 'app' importable when the script is run directly.
_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.core.config import get_settings  # noqa: E402
from app.services.oracle_service import (  # noqa: E402
    _VISUAL_STYLE,
    _build_azure_openai_client,
)

GALLERY_ROOT = _BACKEND_ROOT / "data" / "oracle-gallery"
MANIFEST_PATH = GALLERY_ROOT / "manifest.json"

# Curated prompts — tuned for the NYU talk. Order is the order they're baked.
PROMPTS: dict[str, list[str]] = {
    "wonder": [
        "A single lit lantern carried into a vast room of mirrors, reflections receding into infinity",
        "An open doorway at the end of a long corridor, warm light spilling onto a marble floor",
        "A small figure holding an antique brass key before a wall of identical numbered doors",
    ],
    "institutional": [
        "A grand library reading room at dusk, dust motes suspended in slanting golden light, empty leather chairs",
        "Tall ivy-covered stone gates standing alone in a misty quad, the path beyond fading into fog",
        "An empty lecture hall with rows of wooden desks, a single shaft of light hitting a chalkboard covered in equations",
    ],
    "melancholy": [
        "A candle burning down to its final inch in an empty cathedral, long shadows pooling around it",
        "An abandoned greenhouse with cracked panes, a single wilting flower on a dust-covered table",
        "A figure seated alone on a bench in autumn rain, head bowed, scattered leaves around their feet",
    ],
    "warning": [
        "A weathered hand holding up a single match against an oncoming wall of darkness",
        "A bridge of frayed rope stretching across a chasm, frame trembling in the wind",
        "A red-painted door slightly ajar at the end of a stark white hallway, light bleeding through the gap",
    ],
    "chaos": [
        "A conductor's baton splintering mid-wave, fragments suspended in the air, the orchestra dissolving into shadow",
        "A grand chandelier in mid-fall, crystals catching light as it crashes through a ballroom",
        "A storm tearing through a paper city, pages of architecture lifting into the wind",
    ],
    "bloom": [
        "A single white flower forcing its way through cracked black asphalt, dawn light catching its petals",
        "A tree growing out of an abandoned piano, branches reaching toward stained-glass light",
        "A flock of paper birds rising in a spiral from an open book, ascending into a luminous sky",
    ],
    "dream": [
        "A figure walking on the surface of still water at twilight, footprints leaving rings of pale light",
        "A room where every wall is a window into a different season, snow falling on one side, blossoms on another",
        "A staircase made of floating sheet music ascending into clouds, notes spilling like rain",
    ],
    "neutral": [
        "A perfectly balanced stack of smooth river stones at the center of a still pond, dawn mist rising",
        "A single sphere of blown glass resting on a polished obsidian plinth in an empty white gallery",
        "Concentric circles of soft light expanding across a calm gray sea at dusk",
    ],
}


def _full_prompt(mood_sentence: str) -> str:
    return f"{mood_sentence}. {_VISUAL_STYLE}"


def _ensure_dirs() -> None:
    for category in PROMPTS:
        (GALLERY_ROOT / category).mkdir(parents=True, exist_ok=True)


def _write_manifest() -> None:
    manifest = {
        "categories": {
            cat: [f"{cat}/{i + 1}.png" for i in range(len(prompts))]
            for cat, prompts in PROMPTS.items()
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote manifest: {MANIFEST_PATH}")


def main() -> int:
    settings = get_settings()
    if not settings.azure_openai_endpoint:
        print("ERROR: AZURE_OPENAI_ENDPOINT is not set.", file=sys.stderr)
        return 1

    deployment = settings.oracle_image_deployment or "gpt-image-1"
    is_gpt_image = deployment.startswith("gpt-image")

    print(f"Gallery root:  {GALLERY_ROOT}")
    print(f"Image model:   {deployment}")
    print(f"Total images:  {sum(len(v) for v in PROMPTS.values())}")
    print()

    _ensure_dirs()

    client = _build_azure_openai_client("2025-04-01-preview")

    total = sum(len(v) for v in PROMPTS.values())
    done = 0
    for category, prompts in PROMPTS.items():
        for i, mood in enumerate(prompts, start=1):
            done += 1
            relpath = f"{category}/{i}.png"
            outpath = GALLERY_ROOT / relpath
            if outpath.exists() and outpath.stat().st_size > 0:
                print(f"[{done}/{total}] {relpath} (skip — exists)")
                continue

            prompt = _full_prompt(mood)
            kwargs: dict = {
                "model": deployment,
                "prompt": prompt,
                "n": 1,
                "size": "1536x1024" if is_gpt_image else "1792x1024",
            }
            if is_gpt_image:
                kwargs["quality"] = "medium"
            else:
                kwargs["quality"] = "standard"
                kwargs["response_format"] = "b64_json"

            try:
                t0 = time.time()
                result = client.images.generate(**kwargs)
                b64 = result.data[0].b64_json
                outpath.write_bytes(base64.b64decode(b64))
                dt = time.time() - t0
                print(f"[{done}/{total}] {relpath} \u2713  ({dt:.1f}s)")
            except Exception as exc:  # noqa: BLE001
                print(
                    f"[{done}/{total}] {relpath} FAILED: {exc}",
                    file=sys.stderr,
                )
                # Keep going so a single failure doesn't kill the batch.
                continue

    _write_manifest()
    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
