# Implementation Plan: Voice Interaction

**Branch**: `002-voice-interaction` | **Date**: 2026-03-15 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-voice-interaction/spec.md`
**Constitution**: v1.1.0 (voice-specific principles in III, VI, VII)
**Status**: ✅ MVP Live on Azure — Phases 1-3 + Phase 7 complete

## Summary

Add real-time voice interaction to the 47 Doors support agent using Azure OpenAI GPT-4o Realtime API via WebRTC. The existing 3-agent pipeline (QueryAgent → RouterAgent → ActionAgent) is exposed as Realtime API function tools. Voice shares session context with text chat, enabling seamless modality switching. Mock mode enables development and demos without Azure credentials.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript 5 (frontend)
**Primary Dependencies**: FastAPI 0.109+, Pydantic v2.5+, React 18, Vite, Azure OpenAI SDK
**Storage**: In-memory session store (existing pattern), audit logs (append-only)
**Testing**: pytest (backend), Vitest + Playwright (frontend)
**Target Platform**: Modern browsers (Chrome 90+, Firefox 85+, Edge 90+, Safari 15+), Linux/Windows server
**Project Type**: Web application (backend + frontend)
**Performance Goals**: <2s voice response latency (end-of-utterance to first agent audio), <5s tool execution, <30s total request resolution
**Constraints**: No raw audio storage, PII-filtered transcripts only, ephemeral tokens ≤60s TTL, WebRTC direct to Azure (no audio through backend)
**Scale/Scope**: Single-tenant demo/EDU deployment, 1 concurrent voice session per browser tab

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|-----------|------|--------|
| I. Bounded Agent Authority | Voice tool calls route through same 3-agent pipeline — no bypass | ✅ PASS |
| II. Human Escalation | Voice escalation uses same triggers as text (policy keywords, sensitivity) | ✅ PASS |
| III. Privacy-First Data Handling | No raw audio stored; 3-layer PII filter; ephemeral tokens; no PII echo | ✅ PASS |
| IV. Stateful Context | Voice and text share session_id; transcripts appended to chat thread | ✅ PASS |
| V. Test-First Development | Tests written before implementation at each phase | ✅ PASS |
| VI. Accessibility | Keyboard mic toggle, ARIA live regions, visual state indicators | ✅ PASS |
| VII. Graceful Degradation | Realtime/WebRTC failure → text-only fallback with context preserved | ✅ PASS |
| Voice Channel Security | Ephemeral tokens, WS session validation, no API key exposure | ✅ PASS |

**All gates pass. Proceeding to Phase 0.**

## Project Structure

### Documentation (this feature)

```text
specs/002-voice-interaction/
├── plan.md              # This file
├── spec.md              # Feature specification (25 FRs, 5 user stories)
├── research.md          # Phase 0: technology decisions
├── data-model.md        # Phase 1: entity definitions
├── quickstart.md        # Phase 1: developer setup guide
├── contracts/           # Phase 1: API contracts (OpenAPI)
│   └── voice-api.yaml   # Voice endpoints schema
├── checklists/          # Quality validation
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2: task breakdown (via /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── core/
│   │   └── config.py            # + voice config fields
│   ├── models/
│   │   ├── voice_enums.py       # NEW: VoiceSessionStatus, VoiceRole
│   │   └── voice_schemas.py     # NEW: VoiceMessage, RealtimeSessionResponse, ToolDefinition
│   ├── services/
│   │   ├── interfaces.py        # + RealtimeServiceInterface
│   │   ├── mock/
│   │   │   └── realtime.py      # NEW: MockRealtimeService
│   │   └── azure/
│   │       └── realtime.py      # NEW: AzureRealtimeService
│   ├── api/
│   │   └── realtime.py          # NEW: POST /session, WS /ws endpoints
│   └── dependencies.py          # + RealtimeService DI wiring
└── tests/
    └── test_voice/              # NEW: voice-specific tests
        ├── test_config.py
        ├── test_models.py
        ├── test_mock_service.py
        ├── test_endpoints.py
        └── test_pii_filter.py

frontend/
├── src/
│   ├── types/
│   │   └── voice.ts             # NEW: VoiceState, VoiceMessage, etc.
│   ├── hooks/
│   │   └── useVoice.ts          # NEW: WebRTC + state machine
│   ├── components/
│   │   ├── VoiceMicButton.tsx   # NEW: mic toggle with states
│   │   ├── VoiceTranscript.tsx  # NEW: real-time transcript bubbles
│   │   └── VoiceStatusIndicator.tsx # NEW: connection status
│   └── containers/
│       └── ChatContainer.tsx    # MODIFIED: integrate voice components
└── tests/
    └── voice/                   # NEW: voice UI tests
        ├── VoiceMicButton.test.tsx
        ├── useVoice.test.ts
        └── voice-e2e.spec.ts
```

**Structure Decision**: Web application pattern (existing). Voice feature adds new files within existing `backend/app/` and `frontend/src/` directories. No new top-level directories needed.

## Complexity Tracking

> No Constitution Check violations. No complexity justifications required.

## Implementation Notes (Post-Deployment)

### Authentication Pivot
The original plan called for API key auth (`api-key` header). During deployment, Azure subscription policy `MngEnvMCAP262307` enforced `disableLocalAuth: true`, requiring a full pivot to managed identity:
- `AzureRealtimeService` uses `ManagedIdentityCredential` (not `DefaultAzureCredential`)
- Container App system-assigned MI has `Cognitive Services OpenAI User` role
- Token scope: `https://cognitiveservices.azure.com/.default`
- `backend/.dockerignore` created to prevent `.env` (containing stale API key) from leaking into Docker image

### API Endpoint Discovery
- Ephemeral token: `POST {endpoint}/openai/v1/realtime/client_secrets` (not `/openai/realtime/sessions`)
- Response format: `{"value": "eph_...", "expires_at": "...", "session": {...}}` (top-level, not nested under `client_secret`)
- WebRTC SDP exchange: `POST {endpoint}/openai/v1/realtime/calls` (not `?api-version=...&deployment=...`)

### Dependencies Added
- `aiohttp>=3.9.0` — required by `azure.identity.aio` for async credential acquisition
- Must be added to BOTH `requirements.txt` AND `pyproject.toml`
