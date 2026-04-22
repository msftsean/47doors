# Feature Specification: NYU Oracle — Live Voice-to-Image Projector with Visible Guardrails

**Feature ID:** 003-nyu-oracle
**Branch:** `feature/nyu-oracle`
**Status:** Implementation-ready (patch files exist in `C:\Users\segayle\Downloads\nyu-oracle-patch\`)
**Stage date:** NYU ITP/IMA talk — Thursday, April 23, 2026, 10:40 AM
**Related:** builds on `002-voice-interaction` (phone bridge + SSE transcript bus); does not modify it

---

## 1. Problem

When the 47DOORS voice agent answers a student-support phone call, its only surface today is audio + a developer-facing transcript viewer at `/live`. For an on-stage NYU ITP/IMA talk we need a **projector-scale, audience-facing** surface that:

- makes the otherwise-invisible voice interaction legible at the back of a lecture hall,
- turns each agent reply into a cinematic image so the room has something to *look at*,
- and — most importantly — makes **safety guardrails visible** by rendering Azure Content Safety blocks as a deliberate on-screen "BLOCKED" state rather than silently failing.

The ethical thesis of the talk is *"guardrails are architecture, not censorship."* The feature must therefore treat a content-policy block as a first-class, beautifully-rendered state, not an error.

---

## 2. Users

| User | Role during demo |
|---|---|
| **Projector audience** (ITP/IMA students, faculty) | Passive viewer of `/oracle` on the lecture-hall screen. Sees typography + imagery + BLOCKED state. Never touches a keyboard. |
| **Presenter / phone operator** | Dials the existing ACS phone number from stage. Their voice drives the Oracle. Does not interact with the Oracle browser directly. |
| **Stage operator** (the person running the laptop) | Opens `/oracle` full-screen on the projector before the talk. May press **Shift+B** to manually trigger the BLOCKED state if the live attack prompt fails to provoke it. May use `POST /api/oracle/provoke` to rehearse without a phone call. |

Out of scope as users: end students using the real support agent (they never see `/oracle`; it is a dedicated projector URL).

---

## 3. User Stories

### US-1 (P0) — Audience sees live voice rendered as image
**As** the projector audience
**I want** every agent spoken reply to appear as italic-serif typography backed by a cinematic full-bleed image
**So that** I can follow the conversation visually from the back of a 200-seat room.

**Acceptance:**
- When the voice agent speaks on a live phone call, `/oracle` renders the agent's reply text within ≤ 8 s of speech completing.
- A matching generated image cross-fades in behind the text when the image is ready.
- User turns are rendered in italic serif; agent turns are rendered as an "oracle reply."

### US-2 (P0) — Blocked content is rendered, not swallowed
**As** the presenter
**I want** Azure Content Safety / OpenAI policy violations to render as a crimson BLOCKED screen with the reason text
**So that** the audience can physically see a guardrail fire as a designed moment.

**Acceptance:**
- Backend receives `BadRequestError` with `content_policy_violation` code from the Images API.
- Backend does **not** raise; it returns `{"status": "blocked", "reason": "<message>"}` with HTTP 200.
- Frontend replaces the scene with a full-bleed crimson BLOCKED state showing the reason in italic serif.
- `blockedCount` on the stat strip increments.

### US-3 (P0) — Rehearsable without a phone
**As** the stage operator
**I want** to synthesize fake SSE events from curl
**So that** I can rehearse the full flow (user turn → agent turn → image → block) in a hotel room without dialing the ACS number.

**Acceptance:**
- `POST /api/oracle/provoke` with `{"kind":"agent_speech","text":"..."}` publishes onto the existing transcript bus.
- `/oracle` reacts identically to live phone events.
- Endpoint returns HTTP 403 when `ENVIRONMENT=production`.

### US-4 (P1) — Manual BLOCKED override
**As** the stage operator
**I want** to press **Shift+B** on the projector laptop to force the BLOCKED state
**So that** if the live attack prompt accidentally produces a benign image, I can still deliver the ethics beat.

**Acceptance:**
- Pressing Shift+B while `/oracle` is focused replaces the current scene with a simulated BLOCKED state.
- Pressing Shift+B again (or any new agent turn) clears it.

### US-5 (P1) — Idle state is intentional
**As** the audience before the phone rings
**I want** the screen to show a calm "awaiting the oracle" panel, not a spinner or error
**So that** the surface looks designed from the moment the room walks in.

---

## 4. Functional Requirements

### FR-1 — Dedicated projector route
- `/oracle` MUST render full-bleed with no existing header/nav chrome.
- Implemented via the same `isDirect*Route` pattern already present at `frontend/src/App.tsx:24`.

### FR-2 — SSE subscription
- Frontend MUST subscribe to the existing `/api/phone/transcripts/stream` SSE endpoint.
- MUST handle event types: `call_started`, `call_ended`, `user_speech`, `agent_speech`, `tool_call`.
- MUST auto-reconnect on transient disconnect (default `EventSource` behavior is sufficient).

### FR-3 — Image generation endpoint
`POST /api/oracle/image`

Request:
```json
{ "text": "<agent reply text>", "mood_hint": "<optional>" }
```

Response (HTTP 200 in all three cases):
```json
{ "status": "ok",      "image": "data:image/png;base64,...", "visual_prompt": "..." }
{ "status": "blocked", "reason": "Content policy violation", "visual_prompt": "..." }
{ "status": "error",   "error":  "<message>",                "visual_prompt": "..." }
```

- MUST distill agent text into a cinematic visual prompt via a short LLM call using the existing `azure_openai_deployment`.
- MUST call Azure OpenAI Images with deployment `oracle_image_deployment` (default `gpt-image-1`, fallback `dall-e-3`) at API version `2025-04-01-preview`, size `1792x1024`, `response_format=b64_json`.
- MUST catch `openai.BadRequestError` and, if the body has a `content_policy_violation` code (or any BadRequestError), return `status: "blocked"` with the message as `reason` — MUST NOT raise.
- MUST return `status: "error"` with a human-readable message for all other exceptions.
- MUST return `status: "error"` with `"Azure OpenAI not configured"` when credentials are missing (mock mode).

### FR-4 — Rehearsal endpoint
`POST /api/oracle/provoke`

- Body: `{ "kind": "user_speech|agent_speech|tool_call", "text": "...", "call_id": "..." }`
- Publishes a synthetic event onto the existing `transcript_bus` so `/oracle` and `/live` both receive it.
- MUST return HTTP 403 when `settings.environment == "production"`.

### FR-5 — Scene state machine (frontend)
- State = `{ status, callActive, userUtterance, scene, previousScene, toolHint, responseCount, blockedCount }`.
- On `agent_speech`: create a new scene with `loading=true`, move the prior scene to `previousScene`, fire `POST /api/oracle/image`.
- On image response: merge `imageUrl`, `blocked`, `blockReason`, `loading=false` into current scene (match by scene id).
- `previousScene` MUST clear ~1200 ms after it becomes non-null to finish the crossfade.
- Only the current scene is retained — no scrollback, no history buffer.

### FR-6 — Visual vocabulary
- Agent replies: large italic serif (Cormorant Garamond), with a small uppercase-mono "the oracle speaks" eyebrow.
- User utterances: smaller italic serif overline ("you asked:").
- Tool calls: subtle cyan mono pill.
- BLOCKED: full-bleed crimson background, the word `BLOCKED` in enormous sans, the block reason in italic serif, optional attempted-prompt in small mono (debug).

### FR-7 — Manual BLOCKED override
- Pressing **Shift+B** on `/oracle` MUST render the BLOCKED state without contacting the backend.
- Reason text for manual trigger: `"Simulated block (operator override)"`.
- Pressing Shift+B again or receiving a new `agent_speech` event clears it.

### FR-8 — Config
New setting: `oracle_image_deployment: str = Field(default="gpt-image-1")` in `app/core/config.py`.
Environment variable: `ORACLE_IMAGE_DEPLOYMENT`.

### FR-9 — Router mounting
`oracle_router` MUST mount at `{api_prefix}/oracle` via `app.include_router(...)` in `backend/app/main.py`, following the same pattern as `phone_router` and `transcripts_router`.

---

## 5. Non-Functional Requirements

### NFR-1 — Latency
- Time from `agent_speech` event on the bus to text-on-screen: ≤ 500 ms (SSE fan-out).
- Time from `agent_speech` to image cross-fade-in: target ≤ 6 s, ceiling ≤ 12 s (Azure Images gen time).
- The frontend MUST render text immediately; image arrival is async.

### NFR-2 — Safety
- Content-policy blocks MUST be surfaced as a designed state (see FR-3, US-2). They are a feature, not an error.
- The demo MUST NOT log or display the violating *user* prompt — only the model's block reason.
- `provoke` endpoint MUST be disabled in production (FR-4).

### NFR-3 — Observability
- Backend MUST log (INFO) the visual prompt used, the deployment name, and the result status (`ok`/`blocked`/`error`).
- Backend MUST log (INFO, not WARNING) when a block fires — this is expected behavior during the talk.
- Backend MUST log (EXCEPTION) on unexpected failures in `generate_oracle_image`.

### NFR-4 — Mock-mode resilience
- When `azure_openai_endpoint` is unset, the endpoint MUST return `status: "error"` cleanly so the frontend renders an idle/error panel rather than crashing.
- The page MUST continue to show live SSE text even if the image endpoint is unreachable.

### NFR-5 — Zero-impact on existing features
- No change to chat, `/live`, phone, realtime, media-ws, or transcripts endpoints.
- Only additive: one new router, one new setting, one new frontend route.
- See `CLAUDE.md`: *"Do NOT modify existing text chat functionality."*

### NFR-6 — Accessibility
- `/oracle` is a projector surface, not an interactive app; WCAG AA contrast for typography on dark backgrounds is required.
- Fonts fall back to system serif / monospace if Google Fonts fail to load.

---

## 6. Guardrail / Safety Requirements (Explicit)

| ID | Requirement |
|---|---|
| GR-1 | Azure Content Safety MUST remain enabled (default) on the image deployment. |
| GR-2 | `BadRequestError` from the Images SDK MUST be caught and surfaced as `status: "blocked"`. |
| GR-3 | Block reason text SHOULD be taken from `exc.body["message"]` when available; fallback string `"Content policy violation"`. |
| GR-4 | The `user` prompt that triggered a block MUST NOT be displayed on the BLOCKED screen — only the agent's reply text and the policy reason. |
| GR-5 | The demo's intentional attack script (documented in `INTEGRATION.md`) MUST route through the live ACS phone number; no backend bypass exists. |
| GR-6 | Shift+B simulation MUST be visually indistinguishable from a real block *except* for the reason string `"Simulated block (operator override)"`. |

---

## 7. Out of Scope

- Persisting or replaying Oracle scenes across sessions.
- Multi-call or split-screen views.
- Image moderation *separate* from Azure Content Safety (we trust the built-in layer).
- Authentication on `/oracle` — it is public on the demo environment; no PII is rendered beyond what is already on `/live`.
- Deployment runbook, talk script, traffic-split strategy, rehearsal procedures (covered elsewhere).
- Modifications to chat, voice, phone, or realtime pipelines.
- Audio playback of the agent reply on `/oracle` (audio stays on the phone call).

---

## 8. Dependencies & Assumptions

- **Depends on:** existing `transcript_bus` (`backend/app/services/transcript_bus.py`) and SSE endpoint `/api/phone/transcripts/stream` from feature `002-voice-interaction`.
- **Depends on:** existing Azure OpenAI resource with a chat deployment (reused for prompt distillation).
- **Requires:** a new image deployment (`gpt-image-1` or `dall-e-3`) on the *same* Azure OpenAI endpoint.
- **Assumes:** the presenter will use a Chromium-based browser at 1920×1080 minimum on the projector.
- **Assumes:** network connectivity to Google Fonts CDN; system fallbacks are acceptable.
