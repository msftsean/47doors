# Tasks: Voice Interaction for 47 Doors

**Input**: Design documents from `/specs/002-voice-interaction/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Configuration, types, and service interfaces needed before any voice work

- [ ] T001 Add voice/realtime configuration settings to `backend/app/core/config.py`: `voice_enabled` (bool, default true), `azure_openai_realtime_deployment` (str), `azure_openai_realtime_api_version` (str, default "2025-04-01-preview"), `realtime_voice` (str, default "alloy"), `realtime_vad_threshold` (float, default 0.5)
- [ ] T002 [P] Add `RealtimeServiceInterface` to `backend/app/services/interfaces.py` with methods: `create_session() -> dict` (returns ephemeral token + endpoint), `get_tool_definitions() -> list[dict]` (returns Realtime API tool schemas), `execute_tool(tool_name, arguments, session_id) -> dict` (executes tool against agent pipeline)
- [ ] T003 [P] Add voice-related types to `frontend/src/types/index.ts`: `VoiceState` enum (idle, connecting, listening, processing, speaking, error, disabled), `VoiceMessage` type extending `Message` with `modality` field, `RealtimeSessionResponse` type
- [ ] T004 [P] Add `input_modality` field ("text" | "voice") to the `AuditLog` model in `backend/app/models/schemas.py` and update `ChatMessage` or equivalent to include `modality` field
- [ ] T005 [P] Add `gpt-4o-realtime-preview` model deployment to `infra/main.bicep` in the existing Azure OpenAI resource (same resource, new deployment with model `gpt-4o-realtime-preview`, version `2025-04-01`)

**Checkpoint**: All types, interfaces, and config are in place. Implementation can begin.

---

## Phase 2: Backend Voice Services (Blocking)

**Purpose**: Backend endpoints and services that the frontend voice feature depends on

- [ ] T006 Implement `MockRealtimeService` in `backend/app/services/mock/realtime_service.py`: returns a fake ephemeral token from `create_session()`, returns tool definitions matching the 4 tools, `execute_tool()` delegates to existing QueryAgent/RouterAgent/ActionAgent pipeline via the DI container
- [ ] T007 Implement `AzureRealtimeService` in `backend/app/services/azure/realtime_service.py`: `create_session()` calls Azure OpenAI REST API to create ephemeral token for WebRTC auth, `get_tool_definitions()` returns the 4 tool schemas, `execute_tool()` delegates to existing agent pipeline (same as mock)
- [ ] T008 Register `RealtimeServiceInterface` in `backend/app/core/dependencies.py`: use `MockRealtimeService` when `mock_mode=true`, `AzureRealtimeService` when `mock_mode=false`
- [ ] T009 Create `backend/app/api/realtime.py` with two endpoints:
  - `POST /api/realtime/session` — calls `realtime_service.create_session()`, returns ephemeral token + WebRTC endpoint URL + tool definitions + voice config
  - `WebSocket /api/realtime/ws` — accepts WebSocket connection, receives tool call messages from the frontend (relayed from Realtime API), executes them via `realtime_service.execute_tool()`, returns results. Handles session_id tracking for stateful context.
- [ ] T010 Mount the realtime router in `backend/app/api/routes.py`: import and include the realtime router with prefix `/api/realtime`
- [ ] T011 Update health check in `backend/app/api/routes.py`: add `realtime_api` service status (checks if realtime deployment is reachable or if mock mode)

**Checkpoint**: Backend voice endpoints are functional. `POST /api/realtime/session` returns tokens, WebSocket relay handles tool calls.

---

## Phase 3: User Story 1 - Voice Support Request (Priority: P1) MVP

**Goal**: Student can click mic, speak a request, and hear the agent respond with ticket + KB articles

### Backend Tests for US1

- [ ] T012 [P] [US1] Write test `backend/tests/test_realtime_api.py::test_create_session` — verify POST /api/realtime/session returns ephemeral token, endpoint URL, tool definitions, and voice config
- [ ] T013 [P] [US1] Write test `backend/tests/test_voice_tools.py::test_analyze_and_route_query_tool` — verify the `analyze_and_route_query` tool handler invokes QueryAgent → RouterAgent → ActionAgent and returns ticket_id + KB articles
- [ ] T014 [P] [US1] Write test `backend/tests/test_voice_tools.py::test_search_knowledge_base_tool` — verify the `search_knowledge_base` tool returns top 3 articles
- [ ] T015 [P] [US1] Write test `backend/tests/test_realtime_api.py::test_websocket_tool_execution` — verify WebSocket receives tool call, executes via pipeline, returns result JSON

### Frontend Implementation for US1

- [ ] T016 [US1] Create `frontend/src/hooks/useVoiceChat.ts`:
  - `startVoiceSession()`: calls POST /api/realtime/session, gets token, creates RTCPeerConnection to Azure OpenAI endpoint, sets up audio tracks (local mic → remote), establishes data channel for tool call events
  - `stopVoiceSession()`: closes RTCPeerConnection, cleans up audio streams
  - `voiceState`: reactive state (idle → connecting → listening → processing → speaking → idle)
  - `handleToolCall(toolName, args)`: sends tool call to backend WebSocket, receives result, sends result back to Realtime API via data channel
  - `transcript`: array of voice message transcripts received from Realtime API events
  - Exposes: `{ startVoiceSession, stopVoiceSession, voiceState, transcript, isVoiceSupported }`
- [ ] T017 [P] [US1] Create `frontend/src/components/MicButton.tsx`:
  - Microphone icon button with 6 visual states: idle (gray), connecting (yellow pulse), listening (green pulse), processing (spinner), speaking (solid green wave), error (red), disabled (gray muted)
  - onClick toggles voice session via useVoiceChat hook
  - Keyboard accessible: Enter to activate, Escape to deactivate
  - ARIA label updates with current state
  - Props: `voiceState`, `onToggle`, `disabled`
- [ ] T018 [US1] Create `frontend/src/components/VoiceChat.tsx`:
  - Displays when voice session is active
  - Shows real-time audio level indicator (volume bar or waveform using AudioContext analyser)
  - Shows current voice state text ("Listening...", "Processing...", "Agent is speaking...")
  - Shows live transcript as it comes in from Realtime API events
- [ ] T019 [US1] Modify `frontend/src/components/ChatInput.tsx`: add MicButton to the right of the send button. Pass voice state and toggle handler from useVoiceChat. When voice is active, optionally dim the text input (but keep it functional for hybrid mode).
- [ ] T020 [US1] Modify `frontend/src/components/MessageBubble.tsx`: when message has `modality: "voice"`, display a small speaker icon (HeroIcons `SpeakerWaveIcon`) next to the message timestamp
- [ ] T021 [US1] Modify `frontend/src/components/ChatContainer.tsx`: integrate VoiceChat component (shown above chat when voice active). Append voice transcripts to the message list as they arrive from the useVoiceChat hook.
- [ ] T022 [US1] Add `createRealtimeSession()` function to `frontend/src/api/client.ts`: POST to /api/realtime/session, returns session token + config

**Checkpoint**: Full voice conversation works end-to-end. Student clicks mic → speaks → hears response with ticket ID and KB articles. This is the MVP.

---

## Phase 4: User Story 2 - Voice Escalation (Priority: P2)

**Goal**: Voice agent correctly escalates policy/sensitive/human-request queries

### Tests for US2

- [ ] T023 [P] [US2] Write test `backend/tests/test_voice_tools.py::test_escalate_to_human_tool` — verify the `escalate_to_human` tool creates an escalation ticket and returns confirmation
- [ ] T024 [P] [US2] Write test `backend/tests/test_voice_tools.py::test_policy_keyword_escalation_via_voice` — verify that when `analyze_and_route_query` detects policy keywords in a voice query, the result includes escalation

### Implementation for US2

- [ ] T025 [US2] Verify voice system prompt in `backend/app/services/azure/realtime_service.py` includes escalation instructions: "If the student mentions appeals, waivers, refunds, Title IX, mental health, or asks to speak to a human, use the escalate_to_human tool immediately"
- [ ] T026 [US2] Verify `escalate_to_human` tool definition includes clear description for the model: "Transfer the student to a human support agent. Use this when the student explicitly asks for a human, mentions policy-related topics (appeals, waivers, refunds), or discusses sensitive topics (Title IX, mental health, discrimination, threats)."

**Checkpoint**: Voice escalation works identically to text escalation. All policy/sensitivity/human triggers fire correctly.

---

## Phase 5: User Story 3 - Hybrid Text+Voice (Priority: P3)

**Goal**: Students can switch between text and voice within the same session

- [ ] T027 [US3] Ensure `useVoiceChat.ts` accepts and uses the same `session_id` from `useChat.ts`. When voice starts, pass the current session_id to the backend. When voice transcript messages are generated, add them to the same chat message list.
- [ ] T028 [US3] Modify `frontend/src/hooks/useChat.ts`: accept voice transcript messages and append them to the messages array. Ensure `session_id` is accessible to `useVoiceChat`.
- [ ] T029 [US3] Write test: send a text message creating a ticket, then send a voice tool call for `check_ticket_status` with the same session_id — verify the ticket is found in session context

**Checkpoint**: Student can type a message, switch to voice, reference the previous message, and get correct context-aware response.

---

## Phase 6: User Story 4 - Voice Accessibility (Priority: P4)

**Goal**: Voice is fully accessible via keyboard, screen reader, and assistive tech

- [ ] T030 [P] [US4] Add ARIA live region announcements to `VoiceChat.tsx`: announce "Voice mode activated", "Listening", "Processing your request", "Agent is responding", "Voice mode ended" via `aria-live="polite"` region
- [ ] T031 [P] [US4] Ensure `MicButton.tsx` has proper focus management: receives focus via Tab, Enter activates, Escape deactivates, `aria-pressed` reflects state, `aria-label` updates dynamically (e.g., "Start voice conversation" / "End voice conversation")
- [ ] T032 [US4] Ensure voice transcripts render in the existing screen reader live region used by chat messages (the `aria-live` region in ChatContainer)

**Checkpoint**: Voice mode is fully navigable and understandable without visual cues.

---

## Phase 7: User Story 5 - Error Handling & Degradation (Priority: P5)

**Goal**: Voice fails gracefully to text mode in all error scenarios

- [ ] T033 [US5] Add error handling to `useVoiceChat.ts`:
  - WebRTC connection failure → set voiceState to "error", show notification, mic button shows red state
  - Microphone permission denied → show "Microphone access is required for voice mode" message
  - Browser doesn't support WebRTC → set `isVoiceSupported` to false, mic button not rendered
  - Connection drops mid-session → auto-fallback to text, show "Voice connection lost" notification, preserve conversation
- [ ] T034 [US5] Add `voice_enabled` check to `ChatInput.tsx`: if config returns `voice_enabled: false`, do not render MicButton at all
- [ ] T035 [P] [US5] Write test `backend/tests/test_realtime_api.py::test_session_when_voice_disabled` — verify POST /api/realtime/session returns 503 with message when `voice_enabled=false`
- [ ] T036 [P] [US5] Add `voice_enabled` and realtime deployment status to the `/api/health` response. Frontend checks this on load to determine if mic button should be shown.

**Checkpoint**: All failure modes handled. Text chat always works regardless of voice status.

---

## Phase 8: Polish & Cross-Cutting

**Purpose**: Final cleanup, documentation, and validation

- [ ] T037 [P] Update `backend/requirements.txt` if any new dependencies needed (likely just `websockets` if not already covered by FastAPI/Starlette)
- [ ] T038 [P] Update `docker-compose.yml` if WebSocket port mapping or environment variables are needed
- [ ] T039 [P] Add voice-related environment variables to `.env.example`: `AZURE_OPENAI_REALTIME_DEPLOYMENT`, `VOICE_ENABLED`
- [ ] T040 Run full test suite and verify no regressions in text chat functionality
- [ ] T041 Manual validation: complete a full voice conversation in mock mode (mic → speak → hear response → ticket created)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Backend Services)**: Depends on Phase 1 (interfaces, config, types)
- **Phase 3 (US1 - MVP)**: Depends on Phase 2 (backend endpoints must exist for frontend to connect)
- **Phase 4 (US2)**: Depends on Phase 3 (voice connection must work first)
- **Phase 5 (US3)**: Depends on Phase 3 (voice must work independently before hybrid)
- **Phase 6 (US4)**: Depends on Phase 3 (accessibility on top of working voice)
- **Phase 7 (US5)**: Depends on Phase 3 (error handling for existing voice feature)
- **Phase 8 (Polish)**: Depends on all previous phases

### Parallel Opportunities

- Phase 1: T001, T002, T003, T004, T005 are all independent files — run all in parallel
- Phase 2: T006 and T007 can run in parallel (different service implementations)
- Phase 3: T012-T015 (tests) can all run in parallel; T017 can run in parallel with T016
- Phase 4-7: Can be worked on in parallel by different developers after Phase 3

### MVP Cutline

**Phases 1-3 deliver a fully functional voice MVP.** Phases 4-7 are enhancements that can be deferred if needed. Phase 8 should always run before merge.

---

## Implementation Strategy

### MVP First (Phases 1-3)

1. Complete Phase 1: Setup (all parallel, ~30 min)
2. Complete Phase 2: Backend services (~2 hours)
3. Complete Phase 3: Frontend voice UI + integration (~3 hours)
4. **STOP and VALIDATE**: Full voice conversation works end-to-end
5. Demo to stakeholders

### Full Delivery (All Phases)

1. MVP (Phases 1-3) → Demo
2. Phase 4: Escalation verification (~1 hour)
3. Phase 5: Hybrid mode (~1 hour)
4. Phase 6: Accessibility (~1 hour)
5. Phase 7: Error handling (~1 hour)
6. Phase 8: Polish + regression testing (~1 hour)

**Total estimated effort**: 3-5 days for full feature, 1-2 days for MVP
