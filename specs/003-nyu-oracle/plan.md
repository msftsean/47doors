# Implementation Plan: NYU Oracle

**Feature:** 003-nyu-oracle
**Branch:** `feature/nyu-oracle`
**Spec:** `specs/003-nyu-oracle/spec.md`
**Source patch:** `C:\Users\segayle\Downloads\nyu-oracle-patch\` (already written; this plan documents landing it)

---

## 1. Architecture Overview

The Oracle is **purely additive** on top of the voice/phone pipeline delivered in `002-voice-interaction`. No existing module is rewritten; no event schema changes.

```
 Phone caller ──► ACS ──► Azure OpenAI Realtime ──► transcript_bus ──► SSE /api/phone/transcripts/stream
                                                         │                       │
                                                         │                       ▼
                                                         │             ┌──────────────────┐
                                                         │             │  /oracle (new)   │
                                                         │             │  useOracle hook  │
                                                         │             └────────┬─────────┘
                                                         │                      │ POST /api/oracle/image
                                                         │                      ▼
                                                         │             ┌──────────────────┐
                                                         │             │ oracle_service   │
                                                         │             │  (distill + gen) │
                                                         │             └────────┬─────────┘
                                                         │                      │
                                                         │                      ▼
                                                         │             Azure OpenAI Images
                                                         │             (gpt-image-1)
                                                         │             + Azure Content Safety
                                                         │                      │
                                                         ▼                      ▼
                                           POST /api/oracle/provoke     status: ok | blocked | error
                                           (rehearsal injection)
```

### Key design points

1. **No new event types.** The Oracle consumes the existing `TranscriptEvent` union produced by the phone bridge.
2. **Single-scene memory.** The frontend keeps only the *current* scene and one previous scene (for a 1.2 s cross-fade). No scrollback.
3. **Two Azure clients, one endpoint.** Prompt distillation reuses the chat deployment; image generation uses a dedicated image deployment at `api_version=2025-04-01-preview`. Both go through the same `AZURE_OPENAI_ENDPOINT`.
4. **Block-as-response, not block-as-exception.** `oracle_service.generate_oracle_image` catches `BadRequestError` and returns an `OracleImageResult(status="blocked", ...)`. The API layer returns HTTP 200 with `{"status":"blocked"}`. This is the most load-bearing decision in the feature — see spec GR-2.

---

## 2. File Inventory

### New files (to be copied verbatim from patch)

| Source | Destination |
|---|---|
| `C:\Users\segayle\Downloads\nyu-oracle-patch\oracle_service.py` | `backend\app\services\oracle_service.py` |
| `C:\Users\segayle\Downloads\nyu-oracle-patch\oracle.py` | `backend\app\api\oracle.py` |
| `C:\Users\segayle\Downloads\nyu-oracle-patch\oracle.ts` | `frontend\src\types\oracle.ts` |
| `C:\Users\segayle\Downloads\nyu-oracle-patch\useOracle.ts` | `frontend\src\hooks\useOracle.ts` |
| `C:\Users\segayle\Downloads\nyu-oracle-patch\OraclePage.tsx` | `frontend\src\components\OraclePage.tsx` |

### Modified files (diffs only)

**`backend\app\main.py`**
```python
from app.api.oracle import router as oracle_router
# ...
app.include_router(oracle_router, prefix=f"{settings.api_prefix}/oracle", tags=["Oracle"])
```

**`backend\app\core\config.py`** — in `Settings`:
```python
oracle_image_deployment: str = Field(
    default="gpt-image-1",
    description="Azure OpenAI Images deployment (gpt-image-1 or dall-e-3)",
)
```

**`backend\.env`**
```
ORACLE_IMAGE_DEPLOYMENT=gpt-image-1
```

**`frontend\src\App.tsx`** (follow `isDirectLiveRoute` pattern at line 24):
```tsx
const isDirectOracleRoute = window.location.pathname.toLowerCase() === '/oracle';
// ...
import { OraclePage } from './components/OraclePage';
// In App(), before the normal layout return:
if (isDirectOracleRoute) return <OraclePage />;
```

### Shift+B addition (post-copy edit)

The `useOracle` hook or `OraclePage` component needs a small `useEffect` that listens for `keydown` with `event.shiftKey && event.key === 'B'` and locally dispatches a synthetic `scene_image` with `{status: 'blocked', reason: 'Simulated block (operator override)'}` — see spec FR-7. Exact location: inside `OraclePage.tsx` alongside the existing `useOracle()` call.

---

## 3. Data Flow

### Happy path (one agent turn)
1. Phone caller speaks → ACS → Realtime API → `transcript_bus.publish({type: "agent_speech", text, call_id, timestamp})`.
2. All SSE subscribers (`/live` and `/oracle`) receive the event.
3. `useOracle` reducer handles `agent_speech`: creates a new scene, sets `status="speaking"`, moves prior scene to `previousScene`.
4. `useEffect` fires `POST /api/oracle/image {text: scene.agentText}`.
5. Backend: `oracle_service.generate_oracle_image()`:
   - a. Builds `AzureOpenAI` chat client → distills `agent_text` → one-sentence visual prompt + style suffix.
   - b. Builds `AzureOpenAI` image client (api_version `2025-04-01-preview`) → `images.generate(model=oracle_image_deployment, prompt=..., size="1792x1024", response_format="b64_json")`.
   - c. Returns `OracleImageResult(status="ok", image_b64=..., visual_prompt=...)`.
6. API layer wraps b64 as `data:image/png;base64,...` and returns JSON.
7. Frontend dispatches `scene_image`; scene’s `imageUrl` populates; image cross-fades in.
8. ~1.2 s later, `previousScene` clears.

### Blocked path
Steps 1–4 identical. Step 5.b raises `openai.BadRequestError`. Step 5.c returns `OracleImageResult(status="blocked", block_reason=...)`. Step 6 returns `{status:"blocked", reason:"..."}` HTTP 200. Frontend flips to crimson BLOCKED state; `blockedCount++`.

### Rehearsal path
`POST /api/oracle/provoke {kind:"agent_speech", text:"..."}` → `transcript_bus.publish(...)` → identical to happy path from step 2.

---

## 4. Configuration

| Variable | Default | Purpose |
|---|---|---|
| `AZURE_OPENAI_ENDPOINT` | (existing) | Shared with chat/voice |
| `AZURE_OPENAI_API_KEY` | (existing) | Local; managed identity in prod |
| `AZURE_OPENAI_API_VERSION` | (existing) | Used for chat distillation |
| `AZURE_OPENAI_DEPLOYMENT` | (existing) | Chat deployment, reused for distillation |
| `ORACLE_IMAGE_DEPLOYMENT` | `gpt-image-1` | **New.** Image deployment name |
| `ENVIRONMENT` | (existing) | When `=production`, `/api/oracle/provoke` returns 403 |

Image API version is pinned **in code** at `2025-04-01-preview` inside `oracle_service.py`; it is not a setting. This is intentional — only the image endpoint uses this version.

---

## 5. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| `gpt-image-1` not deployed or quota exhausted at talk time | Medium | Demo failure | (a) Verify deployment Wednesday; (b) fallback `dall-e-3` via env var swap; (c) Shift+B override for BLOCKED beat still works |
| Image gen latency > 12 s | Medium | Audience sees text-only for too long | Text renders immediately; loading shimmer communicates "thinking". Accepted. |
| Content Safety doesn't fire on the scripted attack prompt | Medium | Ethics beat lands weak | Shift+B operator override (FR-7); pre-rehearsed attack prompt documented in INTEGRATION.md |
| SSE stream reconnection storm | Low | Flickering on projector | `EventSource` default backoff; idempotent reducer |
| `provoke` endpoint exposed in prod | Low | Spam / abuse surface | Guarded by `settings.environment == "production"` → 403 |
| `BadRequestError` body shape changes across `openai` SDK versions | Low | Block reason becomes `None` | `getattr(exc, "body", {})` + fallback string `"Content policy violation"` |
| User prompt inadvertently shown in BLOCKED state | Low | Privacy / ethics hit | BLOCKED state reads only `block_reason` + current `scene.agentText` — never `user_speech` |

---

## 6. Test Strategy

Per constitution Principle V (tests before implementation), this feature is TDD **where feasible**. The patch files are reference implementation; we treat them as "the implementation we are validating."

### Backend unit tests — `backend\tests\test_oracle_service.py` (NEW)

- `test_distill_visual_prompt_appends_style_suffix` — monkeypatch chat client to return a fixed mood string; assert result ends with `_VISUAL_STYLE`.
- `test_distill_visual_prompt_fallback_on_exception` — chat client raises; assert fallback `"An abstract scene evoking: ..."` path.
- `test_generate_returns_error_when_endpoint_missing` — settings with empty endpoint → `status="error"`, `error="Azure OpenAI not configured"`.

### Backend API tests — `backend\tests\test_oracle_api.py` (NEW)

- `test_image_happy_path` — monkeypatch `generate_oracle_image` to return `OracleImageResult(status="ok", image_b64="AAA", visual_prompt="p")`; POST `/api/oracle/image {"text":"hello"}` → 200, `image` startswith `data:image/png;base64,`.
- `test_image_blocked_path` — monkeypatch to return `OracleImageResult(status="blocked", block_reason="violence")`; POST → 200, `status=="blocked"`, `reason=="violence"`.
- `test_image_error_path` — monkeypatch to return `status="error"` → 200, `status=="error"`, `error` populated.
- `test_image_rejects_empty_text` — POST `{"text":""}` → 422.
- `test_provoke_publishes_to_bus` — subscribe a listener to `transcript_bus`; POST `/api/oracle/provoke`; assert event received with correct shape.
- `test_provoke_forbidden_in_production` — patch settings `environment="production"`; POST → 403.

### Frontend smoke checks

- `npx tsc --noEmit` — must pass.
- `npx vite build` — must succeed.
- Manual: open `/oracle`, fire three curl `provoke` calls (call_started, user_speech, agent_speech), confirm text + image render; press Shift+B, confirm BLOCKED.

### Test command

```powershell
cd backend; python -m pytest tests\test_oracle_service.py tests\test_oracle_api.py -x -q
```

---

## 7. Constitution Check

| Principle | Status | Notes |
|---|---|---|
| I. Bounded Agent Authority | ✅ | Oracle is a rendering layer only; performs no agent actions, no ticket creation, no routing. |
| II. Contract-First Integration | ✅ | Consumes existing `TranscriptEvent` contract; new endpoints specified in spec §4. |
| III. Privacy-First Data Handling | ✅ | No new PII stored; BLOCKED state explicitly excludes user prompt text (GR-4). |
| IV. Observability | ✅ | Structured INFO logs on every generation attempt; exception logs on failures. |
| V. Tests Before Implementation | ⚠ | Reference implementation already written; unit tests authored *before* landing the patch files (see tasks T-04 precedes T-01/T-02 landing). |
| VI. Accessibility | ✅ | High-contrast typography; system-font fallbacks. |
| VII. Graceful Degradation | ✅ | Mock mode returns `error` status without crashing; SSE auto-reconnects; fonts fall back. |

No principles violated. No waivers required.

---

## 8. Rollout

1. Local smoke test (see §6 manual check).
2. Merge `feature/nyu-oracle` → `main` after review.
3. Redeploy via existing Container Apps pipeline (no new infra).
4. Set `ORACLE_IMAGE_DEPLOYMENT` env var in the Container App.
5. Open `https://<prod>/oracle` on projector, fullscreen, test with one `provoke` before going live.

Deployment runbook is maintained **outside this spec** (in the user's Downloads folder). This plan stops at "code merged + env var set."
