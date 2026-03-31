# Project Context

- **Owner:** msftsean
- **Project:** 47 Doors — Universal Front Door Support Agent for university student support
- **Stack:** Python 3.11+ / FastAPI 0.109+, TypeScript 5 / React 18, Azure OpenAI, Azure AI Search, Pydantic v2.5+
- **Architecture:** Three-agent pipeline (QueryAgent → RouterAgent → ActionAgent) with voice interaction via Azure OpenAI GPT-4o Realtime API / WebRTC
- **Created:** 2026-03-13

## Learnings

<!-- Append new learnings below. Each entry is something lasting about the project. -->

### Phone Call-In Feature Tests — 2026-03-19

**What was tested:**
- `test_phone_schemas.py` — All 5 Pydantic models: `IncomingCallEvent`, `CallEventRequest`,
  `CallState`, `PhoneHealthResponse`, `EventGridValidationEvent`. Covered valid construction,
  missing required fields, optional fields defaulting to None, Literal status validation
  (ringing/connected/disconnected/failed), edge cases (empty strings, very long caller IDs,
  non-E.164 formats, boolean coercion).
- `test_phone_service.py` — `MockPhoneService` contracts: `handle_incoming_call` (unique IDs,
  anonymous callers), `handle_call_event` for all known event types (CallConnected,
  PlayCompleted, CallDisconnected) and unknown types (graceful handling), `health_check`
  tuple structure, concurrency isolation (5 parallel calls, distinct IDs, no cross-state
  contamination).
- `test_phone_endpoints.py` — Three endpoints via `TestClient`: `GET /api/phone/health`
  (200, all three boolean fields present, mock_mode=True in test env), `POST
  /api/phone/incoming` (Event Grid SubscriptionValidation handshake echoing validationCode,
  IncomingCall events, empty/invalid payloads → 400/422), `POST /api/phone/callbacks`
  (CallConnected, CallDisconnected, PlayCompleted, optional result_info, unknown event type,
  empty/missing-field bodies → 400/422).

**Patterns used:**
- Lazy imports inside test methods so tests fail with ImportError when Tank's code isn't there
  yet (not at collection time) — same pattern as `test_voice/test_models.py`
- `_make_valid(**overrides)` helper factories for multi-field model tests
- Class-per-contract grouping (`class TestCallState:`, `class TestIncomingCall:`, etc.)
- `pytest.raises(Exception)` (not `ValidationError`) for Pydantic v2 compat
- Conftest's `MOCK_MODE=true` via `autouse=True` `set_test_env` fixture drives all env setup;
  no per-file env manipulation needed
- Endpoint tests use `TestClient(app)` fixture (sync) — no async client needed for HTTP tests
- Event Grid validation handshake tested as a distinct class from IncomingCall events

**Edge cases covered:**
- `CallState` rejects `"active"` and `"unknown"` (not in the phone Literal — not the voice Literal)
- Empty payload (`b""`) and malformed JSON on POST endpoints → 400 or 422
- Empty JSON array `[]` on incoming endpoint → 400 or 422
- `EventGridValidationEvent` without `validationUrl` (optional field)
- Multiple concurrent simulated calls produce distinct `call_connection_id` values
- Anonymous/non-E.164 caller IDs flow through without rejection

**Key decision:**
- Did NOT enforce E.164 format at the schema level — the spec says `caller_id: str` with no
  format constraint. Tested the pass-through explicitly rather than testing a constraint that
  doesn't exist. See `mouse-phone-tests.md` decision file.
