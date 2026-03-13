# Project Context

- **Owner:** msftsean
- **Project:** 47 Doors — Universal Front Door Support Agent for university student support
- **Stack:** Python 3.11+ / FastAPI 0.109+, TypeScript 5 / React 18, Azure OpenAI, Azure AI Search, Pydantic v2.5+
- **Architecture:** Three-agent pipeline (QueryAgent → RouterAgent → ActionAgent) with voice interaction via Azure OpenAI GPT-4o Realtime API / WebRTC
- **Created:** 2026-03-13

## Learnings

<!-- Append new learnings below. Each entry is something lasting about the project. -->

### 2026-03-13 — Voice Interaction Phase 0/1 Research & Data Model

**Architecture decisions**

- WebRTC transports audio direct browser → Azure; backend is never in the audio path (no audio storage, no codec pipeline).
- Ephemeral token endpoint `POST /api/realtime/session` issues ≤60 s TTL credentials; Azure API key stays server-side only.
- Tool calls flow over a dedicated WS relay `/api/realtime/ws/{session_id}`; voice pipeline MUST route through the same QueryAgent → RouterAgent → ActionAgent chain (Constitution I).
- Three-layer PII filter: pre-tool, post-tool, pre-speech (Constitution III).
- Mock mode: full `RealtimeService` mock implementing `RealtimeServiceInterface` — activated by existing `settings.use_mock_services`.
- Six-state UI machine: idle → connecting → listening → processing → speaking → idle (+ error from connecting/listening/processing).
- Voice and text share the same `session_id` UUID; voice transcript entries appended with `input_modality = "voice"` discriminator.
- `eastus2` primary region — only region with `gpt-4o-realtime-preview` availability matching existing infra region.

**Key file paths**

- `backend/app/models/schemas.py` — Pydantic v2 model patterns; `@field_validator` + `@classmethod`; `Optional[T]` with `default=None`
- `backend/app/models/enums.py` — `str, Enum` pattern for all enumerations
- `backend/app/services/interfaces.py` — ABC interface pattern for all service integrations (voice service will follow same structure)
- `backend/app/core/config.py` — `mock_mode` / `use_mock_services` pattern; `SettingsConfigDict` with `.env` loading
- `specs/002-voice-interaction/research.md` — Phase 0 decision log (10 decisions)
- `specs/002-voice-interaction/data-model.md` — Phase 1 entity definitions (7 backend models, 3 frontend types)

**Patterns to replicate for Phase 1 implementation**

- New voice models go in `backend/app/models/voice_schemas.py` and `backend/app/models/voice_enums.py`
- Service interface goes in `backend/app/services/interfaces.py` (extend existing file, same ABC pattern)
- Config additions go in `backend/app/core/config.py` under a new `# Voice / Realtime Settings` section
- Frontend types go in `frontend/src/types/voice.ts`
