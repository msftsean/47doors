# Project Context

- **Owner:** msftsean
- **Project:** 47 Doors — Universal Front Door Support Agent for university student support
- **Stack:** Python 3.11+ / FastAPI 0.109+, TypeScript 5 / React 18, Azure OpenAI, Azure AI Search, Pydantic v2.5+
- **Architecture:** Three-agent pipeline (QueryAgent → RouterAgent → ActionAgent) with voice interaction via Azure OpenAI GPT-4o Realtime API / WebRTC
- **Created:** 2026-03-13

## Learnings

<!-- Append new learnings below. Each entry is something lasting about the project. -->

### 2026-03-13 — Voice API Artifacts (002-voice-interaction)

**Architecture decisions:**
- Audio never transits the backend — WebRTC connects browser → Azure OpenAI directly. Backend only relays tool call results via `/api/realtime/ws`.
- Ephemeral token TTL ≤ 60 s is a hard constitutional constraint (Voice Channel Security); tokens are single-use and non-renewable.
- `session_id` is shared between text chat and voice sessions — voice attaches to the existing `Session` entity so modality switching preserves context.

**Key file paths:**
- OpenAPI contract: `specs/002-voice-interaction/contracts/voice-api.yaml`
- Quickstart guide: `specs/002-voice-interaction/quickstart.md`
- Planned backend router: `backend/app/api/realtime.py` (not yet created)
- Planned frontend hook: `frontend/src/hooks/useVoice.ts` (not yet created)
- Existing router pattern: `backend/app/api/routes.py` (FastAPI `APIRouter`, mounted at `settings.api_prefix` = `/api`)
- Vite proxy config: `frontend/vite.config.ts` — `/api` → `http://127.0.0.1:8000`; WebSocket proxy is handled automatically.
- Env example: `backend/.env.example` — `MODE=mock` is the default; voice adds `AZURE_OPENAI_REALTIME_DEPLOYMENT`.

**Patterns to follow:**
- Router uses `APIRouter()` with full `responses={}` dicts for all non-200 status codes.
- All response models use Pydantic v2 schemas defined in `backend/app/models/`.
- Health check pattern: always returns HTTP 200; use field values (`realtime_available`) for capability detection, not HTTP status.
- WebSocket close code conventions: 4001 = invalid token, 4002 = session expired (custom range above 4000 for app-level errors).
