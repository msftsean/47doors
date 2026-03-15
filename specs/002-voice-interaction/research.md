# Research Decisions: Voice Interaction (002-voice-interaction)

**Phase**: 0 — Pre-implementation research
**Author**: Tank (Backend Dev)
**Date**: 2026-03-13
**Feature**: Real-time voice conversation via Azure OpenAI GPT-4o Realtime API

---

## 1. WebRTC vs WebSocket Audio Transport

**Decision**: WebRTC direct-to-Azure (audio bypasses the backend entirely).

**Rationale**:
- Audio goes browser → Azure OpenAI Realtime API directly over WebRTC data channels, eliminating one network hop and reducing end-to-end latency by ~150–300 ms.
- Backend is not in the audio path, so it does not process, buffer, or store raw audio — satisfying Constitution Principle III with zero engineering overhead.
- Azure OpenAI GPT-4o Realtime API has native WebRTC support; the backend only needs to issue an ephemeral token and relay tool-call results.

**Alternatives considered**:
- **WebSocket through backend**: Backend proxies audio bytes both ways. Adds latency, requires an audio codec pipeline (Opus decode/re-encode), and forces raw audio through the backend — violating the no-audio-storage principle. Rejected.
- **HTTP chunked audio upload**: Incompatible with real-time bidirectional voice; high latency. Rejected.

---

## 2. Ephemeral Token Strategy

**Decision**: Backend issues short-lived ephemeral tokens (≤60 s TTL) from `POST /api/realtime/session`.

**Rationale**:
- The Azure OpenAI API key never leaves the backend. The browser receives only a scoped, time-limited credential that authorises exactly one Realtime session.
- A 60-second TTL limits the blast radius if a token is intercepted — it expires before it can be reused.
- Aligns with the existing `mock_mode` pattern in `config.py`: in mock mode the endpoint returns a fake token without calling Azure.

**Alternatives considered**:
- **Long-lived API key in frontend**: Exposes the master credential in the browser bundle. Rejected — violates Constitution Principle III (voice channel security).
- **OAuth client-credentials flow with Entra ID**: More robust long-term, but over-engineered for the current scope. Noted as a Phase 6 hardening option.

---

## 3. Tool Call Relay Architecture

**Decision**: WebSocket relay on the backend handles tool-call exchange only; audio is never routed through this channel.

**Rationale**:
- The Realtime API can invoke backend tools (e.g., `analyze_and_route_query`). These calls must reach the existing 3-agent pipeline (QueryAgent → RouterAgent → ActionAgent), which runs server-side.
- A dedicated WS endpoint (`/api/realtime/ws/{session_id}`) handles: receive `tool_call` event from Realtime API → execute pipeline → return `tool_result`.
- Constitution Principle I: tool calls from voice MUST route through the same bounded pipeline, not bypass agents via direct function access.

**Alternatives considered**:
- **HTTP callbacks from Realtime API**: Azure Realtime API does not support outbound HTTP tool callbacks — tool results must be sent back over the same connection. Rejected (not supported).
- **Frontend executes tools locally**: Exposes internal service logic to the browser and violates agent boundary enforcement. Rejected.

---

## 4. PII Filtering in Voice

**Decision**: Three-layer PII filter applied at: (1) pre-tool-call on transcribed input, (2) post-tool-result before speaking, (3) pre-speech-synthesis on final response text.

**Rationale**:
- Constitution Principle III is explicit: no PII echo in voice responses, transcripts stored only as PII-safe context.
- Three layers prevent PII from leaking into: the pipeline payload, tool results spoken aloud, or the audio waveform itself.
- Reuses the existing `pii_detected` / `pii_types` fields from `QueryResult` (schemas.py) — no new detection logic required for layer 1.

**Alternatives considered**:
- **Single filter at transcript storage**: PII could still be spoken aloud before it is scrubbed from storage. Rejected.
- **Azure Content Safety API**: Adds an external round-trip; overkill for PII redaction already covered by the existing pipeline. Noted for post-MVP evaluation.

---

## 5. Mock Mode Strategy

**Decision**: Full mock `RealtimeService` implementing the same `RealtimeServiceInterface`, activated when `settings.use_mock_services` is `True`.

**Rationale**:
- The codebase already uses `mock_mode: bool` in `Settings` with `use_mock_services` property. Voice follows the same factory pattern used for `LLMService`, `TicketService`, etc.
- In mock mode: `POST /api/realtime/session` returns a fake token; the WS endpoint echoes scripted tool call sequences; audio input is simulated with pre-recorded utterances.
- Enables full frontend development and CI testing without Azure credentials or microphone access.

**Alternatives considered**:
- **Feature flag disabling voice entirely in CI**: Leaves the voice code path untested. Rejected.
- **Conditional logic inside the real service**: Mixes production and mock paths, harder to audit. Rejected.

---

## 6. Voice State Machine

**Decision**: Six-state machine: `idle → connecting → listening → processing → speaking → idle`, with `error` reachable from `connecting`, `listening`, and `processing`.

**Rationale**:
- Maps 1:1 to the UI states defined in spec VFR-014 (visual indicators per state) and drives ARIA live-region announcements for accessibility (Constitution Principle VI).
- Six states are the minimum needed to accurately represent the WebRTC lifecycle: token fetch (`connecting`), VAD-active microphone (`listening`), pipeline execution (`processing`), and TTS playback (`speaking`).
- Clear, deterministic transitions simplify error recovery: any `error` state returns to `idle` after a configurable retry delay.

**Alternatives considered**:
- **Binary on/off**: Too coarse — cannot drive distinct UI indicators for listening vs. speaking. Rejected.
- **Eight-state machine (adding `initializing` and `closing`)**: Adds complexity without additional UI value. Folded into `connecting` and `idle` respectively.

**State diagram**:
```
idle → connecting → listening → processing → speaking → idle
                                           ↘
                                            error → idle
connecting → error → idle
listening  → error → idle
```

---

## 7. Session Sharing Between Modalities

**Decision**: Voice and text share the same `session_id`; voice transcripts are appended to the unified conversation history as `VoiceMessage` entries with `input_modality = "voice"`.

**Rationale**:
- Constitution Principle IV (session continuity): modality switch must not lose context.
- Spec requirements VFR-010 (voice transcript in chat thread) and VFR-011 (modality-switch context preservation) both mandate this.
- Using the existing `session_id` (UUID) as the join key requires no schema migration — the `Session` model in `schemas.py` already tracks `conversation_history`.

**Alternatives considered**:
- **Separate voice sessions with a cross-reference link**: Doubles session management complexity and can desync under race conditions. Rejected.
- **Voice-only session with no text linkage**: Violates VFR-010/011 and loses conversation context across modality switches. Rejected.

---

## 8. Audio Storage Policy

**Decision**: No raw audio is stored anywhere — not on the backend, not in blob storage, not in logs.

**Rationale**:
- Constitution Principle III: audio is the most sensitive PII vector (voice biometrics, background speech, etc.).
- Spec VNFR-005 explicitly prohibits raw audio storage.
- WebRTC direct transport means audio bytes never even reach the backend server, making this policy trivially enforced at the architectural level.
- Only the PII-filtered text transcript is stored in the session.

**Alternatives considered**:
- **Temporary audio buffering for retry/replay**: Increases latency, creates GDPR/FERPA exposure. Rejected.
- **Opt-in audio recording for quality improvement**: Out of scope for MVP; requires explicit consent flow. Noted for a future privacy-review-gated phase.

---

## 9. Degradation Strategy

**Decision**: Cascading fallback — WebRTC failure → WebSocket audio attempt → graceful text-only mode with session context preserved.

**Rationale**:
- Constitution Principle VII (Graceful Degradation): the system must remain functional when subsystems fail.
- Students on restrictive networks (firewalls blocking UDP/WebRTC) must still receive support.
- Text-only fallback reuses the fully operational `/api/chat` endpoint; session context is preserved so the student does not lose their conversation.

**Fallback chain**:
1. **WebRTC fails** (ICE timeout, firewall): Attempt WebSocket audio relay.
2. **WebSocket audio fails** (network error, timeout): Display in-app banner: *"Voice is unavailable — please type your request."* Chat input is enabled.
3. **Backend realtime endpoint fails** (Azure outage): Same text-only fallback; error surfaced in health check.

**Alternatives considered**:
- **Hard error on WebRTC failure**: Blocks students who need support. Rejected.
- **Silent retry loop**: Confuses the user; wastes bandwidth. Rejected.

---

## 10. Azure Region Selection

**Decision**: `eastus2` as primary region for the Azure OpenAI Realtime API endpoint.

**Rationale**:
- `gpt-4o-realtime-preview` is available in `eastus2` (and `westus2`); it is not globally available.
- `eastus2` offers the lowest median latency to the primary university user base (US East Coast campuses).
- Matches the region already used for the existing Azure OpenAI deployment in project infrastructure (`infra/`).

**Alternatives considered**:
- **westus2**: Higher latency for East Coast users; suitable as a failover region.
- **swedencentral**: Available region for Realtime API but adds ~120 ms RTT for US users. Not suitable as primary.
- **Multi-region active-active**: Unnecessary complexity for MVP; noted as Phase 6 resilience option.
