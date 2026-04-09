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

### GPT-4o to GPT-4.1 Migration — Test Impact — 2026-03-20

**What was scanned and updated:**
- Systematically searched all backend test files (`backend/tests/`) for hardcoded model references:
  - `gpt-4o` (found in 4 files, 5 occurrences)
  - `gpt-4o-realtime-preview` (found in 1 file, 2 occurrences)
  - Old API versions `2024-05-01-preview`, `2024-02-15-preview`, etc. (found in test_gpt4o_evals.py)

**Files updated:**
1. `backend/tests/conftest.py` line 255: Changed `AZURE_OPENAI_DEPLOYMENT` from `"gpt-4o"` to `"gpt-4.1"`
2. `backend/tests/test_voice/test_config.py` lines 21, 32: Updated Settings fixtures from `"gpt-4o"` to `"gpt-4.1"`
3. `backend/tests/test_voice/test_models.py` lines 141, 161: Updated RealtimeSessionResponse fixtures from `"gpt-4o-realtime-preview"` to `"gpt-4.1-realtime-preview"`
4. `backend/tests/test_gpt4o_evals.py` lines 52, 216–217: Updated deployment defaults from `"gpt-4o"` to `"gpt-4.1"` and API version from `"2024-05-01-preview"` to `"2024-12-01-preview"`

**Test results:**
- All 447 tests pass; 97 eval tests skipped (require real Azure credentials, intentional)
- No regressions detected
- Conftest fixture-driven environment setup ensures all tests pick up the new deployment name

**Key decision:**
- Assumed `"gpt-4.1"` as the migration target and `"2024-12-01-preview"` as the API version.
  Tank's infra changes confirmed these choices (check `.squad/decisions.md` for full record).
- Realtime deployment migration confirmed as `gpt-realtime` (Tank's decision on naming).

**Session coordination:** Parallel spawn 2026-04-08T17:25 with Tank. Orchestration log: `.squad/orchestration-log/2026-04-08T17-25-mouse.md`

### Playwright Deployment Eval Suite — 2026-04-09

**What was created:**
- `frontend/tests/e2e/eval.spec.ts` — 24-test evaluation suite for live deployment testing
- Updated `frontend/playwright.config.ts` — added `BASE_URL` env var override, skips local `webServer` when targeting live

**Existing test baseline (run against live deployment):**
- 43 total existing tests: 32 passed, 10 failed, 1 skipped
- 5 smoke tests failed: hardcoded `http://localhost:8000` backend URLs (ECONNREFUSED)
- 4 accessibility tests failed: real axe-core violations (color contrast, WCAG compliance)
- 1 chat test failed: "Talk to Human" button not found (timeout — likely UI label mismatch)
- 1 voice test skipped: placeholder only

**Eval suite results (live deployment):**
- 24 total eval tests: 22 passed, 2 failed
- Homepage, chat, sessions, error handling, voice UI, performance: ALL PASS
- Two KB quality failures detected (real issues, not test bugs):
  1. "How do I register for classes?" → AI asked clarifying question instead of answering
  2. "How do I apply for financial aid?" → AI routed to IT Support instead of Financial Aid
- Performance: page loads ~1.3s, chat API ~3-4s avg, health endpoint ~1s (warm), 5.4s (cold start)

**Config patterns established:**
- `BASE_URL` env var overrides `baseURL` in playwright config (defaults to localhost:5173)
- `BACKEND_URL` env var for direct API tests (auto-derived from BASE_URL by replacing `-frontend` with `-backend`)
- `webServer` block conditionally skipped when `BASE_URL` is set (no local server startup for live testing)
- Health endpoint threshold set to 10s to accommodate Azure Container App cold starts
- All eval tests tagged with `@eval` for selective execution

**Key finding:**
- The 3-agent pipeline (QueryAgent → RouterAgent → ActionAgent) misroutes some queries:
  registration goes to clarification loop, financial aid goes to IT.
  These are real demo risks that should be addressed before the next demo.
