"""Quick local test of the oracle image endpoint."""
import sys
import httpx

TEXT = (
    "To apply for graduation, submit form DR-204 through the registrar "
    "portal by April 1st. You will receive confirmation within five "
    "business days."
)

try:
    r = httpx.post(
        "http://127.0.0.1:8000/api/oracle/image",
        json={"text": TEXT},
        timeout=120.0,
    )
    print(f"HTTP {r.status_code}")
    data = r.json()
    print(f"status: {data.get('status')}")
    if data.get("visual_prompt"):
        print(f"visual_prompt: {data['visual_prompt'][:200]}")
    if data.get("image"):
        print(f"image: {len(data['image'])} chars, prefix: {data['image'][:60]}")
    if data.get("reason"):
        print(f"reason: {data['reason']}")
    if data.get("error"):
        print(f"error: {data['error']}")
except Exception as e:
    print(f"EXC: {e!r}")
    sys.exit(1)
