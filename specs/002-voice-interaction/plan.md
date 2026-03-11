# Implementation Plan: Voice Interaction for 47 Doors

**Branch**: `002-voice-interaction` | **Date**: 2026-02-06 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-voice-interaction/spec.md`

## Summary

Add real-time voice conversation to the 47 Doors support agent using the Azure OpenAI GPT-4o Realtime API with WebRTC transport. The existing 3-agent pipeline (QueryAgent → RouterAgent → ActionAgent) is exposed as Realtime API function tools, enabling the voice model to call them during spoken conversation. The frontend adds a microphone toggle button that establishes a direct WebRTC audio connection to Azure OpenAI, while a backend WebSocket relay handles tool call execution against the existing pipeline. Text chat remains fully functional alongside voice.

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript 5.x (frontend)
**Primary Dependencies**: FastAPI + Starlette WebSocket (backend), React 18 + native WebRTC API (frontend), Azure OpenAI Realtime API
**Storage**: Existing session/audit stores (in-memory mock or Cosmos DB) — no new storage needed
**Testing**: pytest (backend), Vitest (frontend)
**Target Platform**: Web browser (Chrome 90+, Firefox 85+, Edge 90+, Safari 15+)
**Project Type**: Web application (backend + frontend)
**Performance Goals**: <2s voice response latency, <5s tool execution
**Constraints**: No raw audio storage, PII never repeated in voice, graceful degradation to text
**Scale/Scope**: Same as base app (500 concurrent users); voice sessions are stateless on our backend (WebRTC is peer-to-peer with Azure)

## Constitution Check

*GATE: Must pass before implementation.*

| Principle | Compliance | Notes |
|-----------|-----------|-------|
| I. Bounded Agent Authority | ✅ PASS | Voice agent uses same bounded tools via Realtime API function calling. No new authority granted. Tools call existing agents that already enforce boundaries. |
| II. Human Escalation | ✅ PASS | `escalate_to_human` tool exposed to voice agent. All escalation triggers (policy keywords, sensitivity, explicit request) work identically through tool calls. |
| III. Privacy-First | ✅ PASS | Raw audio not stored. Transcripts PII-filtered before display/logging. System prompt instructs model not to repeat PII. Audit logs include `input_modality: "voice"`. |
| IV. Stateful Context | ✅ PASS | Voice sessions share session_id with text sessions. Modality switching preserves full conversation history. |
| V. Test-First | ✅ PASS | All voice endpoints and tool handlers will have tests. Mock Realtime service enables testing without Azure dependency. |
| VI. Accessibility | ✅ PASS | Mic button keyboard accessible. Screen reader announcements for state changes. Voice is additive, not a replacement for text. |
| VII. Graceful Degradation | ✅ PASS | WebRTC failure → text fallback. Realtime API unavailable → mic button disabled with message. Health check includes realtime_api status. |

## Architecture

### Data Flow

```
Student (browser)
  ├─ Text: POST /api/chat → FastAPI → 3-agent pipeline → JSON response
  │
  └─ Voice: WebRTC audio ──────────────────────→ Azure OpenAI Realtime API
                                                       │
           Browser ← WebRTC audio (agent speech) ──────┘
                                                       │
           When tool call needed:                      │
           Azure OpenAI → WebSocket → Backend ─────────┤
                          /api/realtime/ws             │
                          Tool handler invokes         │
                          existing 3-agent pipeline    │
                          Returns result via WS ───────→ Azure OpenAI
                                                       continues speaking
```

### Key Design Decisions

1. **WebRTC (not WebSocket audio)**: WebRTC provides the lowest latency for audio streaming. The browser connects directly to Azure OpenAI for audio — our backend never touches raw audio.

2. **Backend WebSocket relay for tools only**: The backend's role in voice is limited to (a) issuing ephemeral tokens for WebRTC auth, and (b) executing tool calls when the Realtime API invokes them. This minimizes backend complexity.

3. **Shared session context**: Voice and text use the same `session_id`. The voice tool handlers create/read from the same session store, enabling seamless modality switching.

4. **Mock support**: A `MockRealtimeService` returns a simulated ephemeral token and handles tool calls locally, enabling voice UI development without an Azure OpenAI deployment.

## Project Structure

### Documentation (this feature)

```text
specs/002-voice-interaction/
├── spec.md              # Feature specification
├── plan.md              # This file
└── tasks.md             # Task breakdown
```

### Source Code (changes to existing repo)

```text
backend/
├── app/
│   ├── api/
│   │   ├── routes.py              # MODIFY: mount realtime router
│   │   └── realtime.py            # NEW: POST /api/realtime/session, WS /api/realtime/ws
│   ├── services/
│   │   ├── interfaces.py          # MODIFY: add RealtimeServiceInterface
│   │   ├── azure/
│   │   │   └── realtime_service.py # NEW: Azure OpenAI Realtime API integration
│   │   └── mock/
│   │       └── realtime_service.py # NEW: Mock realtime service for dev/demo
│   ├── core/
│   │   ├── config.py              # MODIFY: add voice/realtime settings
│   │   └── dependencies.py        # MODIFY: register realtime service in DI
│   └── models/
│       └── schemas.py             # MODIFY: add VoiceMessage, input_modality field
├── tests/
│   ├── test_realtime_api.py       # NEW: tests for realtime endpoints
│   └── test_voice_tools.py        # NEW: tests for voice tool handlers

frontend/
├── src/
│   ├── components/
│   │   ├── VoiceChat.tsx          # NEW: voice session UI (waveform, status)
│   │   ├── MicButton.tsx          # NEW: microphone toggle button component
│   │   ├── ChatInput.tsx          # MODIFY: integrate MicButton
│   │   ├── ChatContainer.tsx      # MODIFY: display voice transcripts
│   │   └── MessageBubble.tsx      # MODIFY: voice message indicator icon
│   ├── hooks/
│   │   └── useVoiceChat.ts        # NEW: WebRTC lifecycle, audio streams, tool results
│   ├── api/
│   │   └── client.ts              # MODIFY: add realtime session endpoint
│   └── types/
│       └── index.ts               # MODIFY: add voice-related types

infra/
└── main.bicep                     # MODIFY: add gpt-4o-realtime-preview deployment
```

**Structure Decision**: Voice integration extends the existing web app structure. No new top-level directories needed. Backend gets a new `realtime.py` API module and realtime service implementations. Frontend gets a new `VoiceChat` component, `MicButton` component, and `useVoiceChat` hook. Both follow existing patterns.

## Complexity Tracking

No constitution violations. Complexity is contained:
- Backend: 2 new endpoints + 2 service implementations + tool handler bridging to existing agents
- Frontend: 2 new components + 1 hook + minor modifications to 3 existing components
- Infra: 1 new model deployment in existing Bicep
