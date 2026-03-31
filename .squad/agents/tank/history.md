# Project Context

- **Owner:** msftsean
- **Project:** 47 Doors — Universal Front Door Support Agent for university student support
- **Stack:** Python 3.11+ / FastAPI 0.109+, TypeScript 5 / React 18, Azure OpenAI, Azure AI Search, Pydantic v2.5+
- **Architecture:** Three-agent pipeline (QueryAgent → RouterAgent → ActionAgent) with voice interaction via Azure OpenAI GPT-4o Realtime API / WebRTC
- **Created:** 2026-03-13

## Learnings

<!-- Append new learnings below. Each entry is something lasting about the project. -->

### 2026-03-15 — Phone Call-In Feature (ACS Call Automation)

**Architecture decisions**

- ACS Call Automation bridges inbound PSTN calls to Azure OpenAI Realtime API via WebSocket media streaming (`MediaStreamingOptions`). Audio flows: PSTN caller → ACS → WebSocket → Azure OpenAI Realtime. Backend is never in the audio path — same pattern as browser WebRTC.
- Reused the same `gpt-4o-realtime-preview` deployment and 4-tool pipeline as browser voice. PHONE_SYSTEM_PROMPT is phone-specific (terse, no markdown, no scrolling back) but same agent identity.
- `PhoneServiceInterface` added to `backend/app/services/interfaces.py` following same ABC pattern as `RealtimeServiceInterface`. `AzurePhoneService` uses lazy-init `CallAutomationClient` with async double-checked locking — same pattern as `AzureRealtimeService`.
- Mock service (`MockPhoneService`) uses SYNCHRONOUS methods (not async). This is intentional — the service tests call it without `await`. The API layer uses `_call()` helper (`inspect.isawaitable`) to handle both sync mocks and async production services. This is the correct pattern for Pydantic-v2 codebases with mixed sync/async test coverage.
- ACS webhook events use TWO different event type names for subscription validation: `Microsoft.EventGrid.SubscriptionValidationEvent` AND `Microsoft.EventGrid.SubscriptionValidated`. Both must be handled.
- Event Grid delivers callbacks as JSON arrays. Call Automation callbacks use flat dicts with `event_type` and `call_connection_id` as direct top-level keys (not wrapped in `data`). The phone API normalizes both formats.
- ACS `listKeys().primaryConnectionString` provides the connection string for the `CallAutomationClient`. Managed identity is the preferred production auth path.

**Pydantic v2 gotcha — multiple model validators**

- Pydantic v2 only supports ONE `@model_validator(mode="after")` per class. Defining a second one with a different method name OVERRIDES the first silently (with a warning). Fix: combine all after-validators into a single method (`_auto_disable_features`). This affected the voice+phone auto-disable logic in `config.py`.

**Key file paths**

- `backend/app/services/azure/phone.py` — ACS Call Automation production service
- `backend/app/services/mock/phone.py` — Synchronous mock for test isolation
- `backend/app/api/phone.py` — `/api/phone/incoming` (Event Grid) + `/api/phone/callbacks` (Call Automation) + `/api/phone/health`
- `backend/app/models/phone_schemas.py` — `IncomingCallEvent`, `CallEventRequest`, `CallState`, `PhoneHealthResponse`, `EventGridValidationEvent`
- `infra/main.bicep` — ACS resource (always provisioned, not conditional), ACS connection string secret, Contributor role assignment for backend managed identity, `AZURE_ACS_ENDPOINT` env var + output
- `backend/app/core/config.py` — `phone_enabled`, `azure_acs_endpoint`, `azure_acs_connection_string`, `acs_phone_number`, `max_call_duration`

**New SDK dependency**

- Added `azure-communication-callautomation>=1.4.0` to both `requirements.txt` and `pyproject.toml`



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

### 2026-03-14 — Phase 1 Setup (T001, T002, T003)

**Config changes (T001)**

- Added 6 voice fields to `Settings` in `backend/app/core/config.py` under a `# Voice / Realtime API Settings` section.
- Used `model_validator(mode="after")` (Pydantic v2) to auto-set `voice_enabled=False` when `azure_openai_realtime_deployment` is empty AND `mock_mode=False`. Validator confirmed working: mock_mode=True keeps voice_enabled=True, mock_mode=False with empty deployment flips it to False.
- `max_voice_session_duration` added (600 s default) as requested in the task brief; tasks.md did not list it but the spec and user instructions both required it.

**Env stubs (T002)**

- Appended 6 voice vars to `backend/.env.example` with a `# Voice / Realtime API Configuration` comment block.
- Used `gpt-4o-realtime-preview` as the deployment stub value (matches tasks.md; user task brief used `gpt-4o-realtime` — tasks.md value preferred as canonical).

**Bicep (T003)**

- Added `openAiRealtimeDeployment` resource inside the Azure OpenAI resource block in `infra/main.bicep`, model `gpt-4o-realtime-preview`, version `2025-04-01`, sku Standard, capacity 1.
- Added `dependsOn: [openAiDeployment]` to sequence deployments and avoid throttle conflicts during provisioning.
- Added output `AZURE_OPENAI_REALTIME_DEPLOYMENT` so azd wires the deployment name into app settings automatically.

### 2026-03-14 — Live Azure Deployment (azd up)

**Deployment verified and documented**

- `azd up` completed successfully. All services running live on Azure (MOCK_MODE=false).
- **Container App URL**: `https://frontdoor-6wfum6gndxawy-backend.blackflower-446b9850.eastus2.azurecontainerapps.io`
- **Resource Group**: `rg-vvoice`
- **Azure OpenAI Endpoint**: `https://frontdoor-6wfum6gndxawy-openai.openai.azure.com/`
- **OpenAI Deployments**: `gpt-4o` (text) + `gpt-4o-realtime-preview` (voice/WebRTC)
- **Cosmos DB**: `https://frontdoor-zfyhb6f72odyg-cosmos.documents.azure.com:443/`
- **AI Search**: `https://frontdoor-6wfum6gndxawy-search.search.windows.net`
- **Container Registry**: `frontdoor6wfum6gndxawyacr.azurecr.io`
- **Region**: `eastus2`
- **Subscription**: `ME-MngEnvMCAP262307-segayle-1`
- Health checks verified: `/api/health` → LLM connecting (ticketing, knowledge_base, session_store up); `/api/realtime/health` → realtime_available: true, mock_mode: false, voice_enabled: true
- Updated DEMO_RUNBOOK.md and docs/index.html: replaced all placeholder `${AZURE_CONTAINERAPP_URL}` and old resource group/subscription references with live values. Runbook is now Azure-first throughout.

### 2026-03-14 — Frontend Container App Deployment

**Architecture decisions**

- Frontend deployed as a separate Container App alongside the backend, both in the same Container App Environment.
- nginx reverse-proxies `/api/` requests to the backend, making all API calls same-origin from the browser's perspective — eliminates CORS issues entirely.
- `BACKEND_URL` is injected via env var and resolved at container startup using `envsubst` (only `${BACKEND_URL}` is substituted; nginx variables like `$host`, `$uri` are preserved).
- Dockerfile default `BACKEND_URL=http://backend:8000` preserves docker-compose backward compatibility.
- Added WebSocket upgrade headers (`Upgrade`, `Connection`) and long read timeout (86400s) to nginx `/api/` location for voice relay WebSocket support.
- Frontend Container App: 0.25 vCPU, 0.5Gi memory, 1-2 replicas — lightweight since it only serves static files + proxies.
- Backend Container App retains external ingress (health checks, direct API access); frontend also gets external ingress (user-facing).
- New Bicep output `AZURE_FRONTEND_URL` for the frontend's public URL.

**Key file paths**

- `azure.yaml` — `frontend` service registered alongside `backend`
- `infra/main.bicep` — `frontendContainerApp` resource (lines ~375-427)
- `frontend/Dockerfile` — envsubst templating for BACKEND_URL at startup
- `frontend/nginx.conf` — configurable `${BACKEND_URL}` + WebSocket headers

### 2026-03-14 — Fix 502 Bad Gateway on Frontend → Backend Proxy

**Root cause**

- nginx was proxying to the backend via HTTPS (`proxy_pass https://backend-fqdn`) but NOT sending TLS SNI (Server Name Indication).
- Azure Container Apps uses a shared reverse proxy within each environment. All apps in the same environment share internal IPs (100.100.x.x range). Azure's proxy uses SNI to route TLS connections to the correct container app.
- Without SNI, Azure's proxy couldn't determine which app owned the connection → reset during SSL handshake → nginx logged `peer closed connection in SSL handshake (104: Connection reset by peer)`.
- Secondary issue: `proxy_set_header Host $host` was forwarding the frontend's FQDN as the Host header to the backend. After TLS termination, Azure would use the Host header for HTTP routing — the wrong FQDN could misroute the request.

**Fix applied**

- Added `proxy_ssl_server_name on;` to nginx.conf — enables SNI so Azure can identify the target container app.
- Changed `proxy_set_header Host $host;` → `proxy_set_header Host $proxy_host;` — sends the backend's FQDN as the Host header, matching the intended destination.

**Azure Container Apps networking lesson**

- When Container App A proxies to Container App B via the external FQDN inside the same environment, the FQDN resolves to an internal IP (100.100.x.x), not the public IP. TLS is still required, and **SNI is mandatory** for Azure's shared proxy to route correctly.
- For any nginx proxy_pass to an HTTPS upstream on Azure Container Apps, always use `proxy_ssl_server_name on;`.

### 2026-03-14 — Fix 503 Error on Realtime Session Endpoint

**Root cause**

- Frontend was getting 503 errors when calling `POST /api/realtime/session`.
- Backend logs showed: `Azure OpenAI Realtime API returned 404: {"error":{"code":"404","message": "Resource not found"}}`
- The code was using the wrong Azure OpenAI Realtime API endpoint path.

**Investigation**

- Initial code used: `/openai/realtime/sessions?api-version={version}` (404)
- First fix attempt: `/openai/deployments/{deployment}/realtime/sessions?api-version={version}` (404)
- Discovered Azure OpenAI has TWO different endpoint patterns for Realtime API:
  - **Region-based endpoint** (preview): `https://{region}.realtimeapi-preview.ai.azure.com/v1/realtime/sessions` (requires Bearer token)
  - **Resource-based endpoint** (current): `https://{resource}.openai.azure.com/openai/v1/realtime/client_secrets` (requires api-key OR Bearer token)

**Correct endpoint pattern per Microsoft Learn documentation**

- URL: `{endpoint}/openai/v1/realtime/client_secrets` (no deployment in path, no api-version query param)
- Method: POST
- Body: Session configuration with nested structure:
  ```json
  {
    "session": {
      "type": "realtime",
      "model": "{deployment_name}",
      "audio": { "output": { "voice": "alloy" } },
      "instructions": "..." (optional)
    }
  }
  ```
- Response: `{ "value": "{ephemeral_token}" }` (60s TTL)

**Secondary issue discovered**

- Azure OpenAI resource had `disableLocalAuth: true` set, blocking API key authentication.
- This means the Realtime API endpoint requires **Microsoft Entra ID (Azure AD) Bearer tokens**, not API keys.
- Current `AzureRealtimeService` uses `api-key` header authentication.

**Fix applied**

- Updated `backend/app/services/azure/realtime.py`:
  - Changed URL from `/openai/realtime/sessions?api-version=...` to `/openai/v1/realtime/client_secrets`
  - Changed request body structure to match Azure's session configuration format
  - Changed response parsing to extract token from `data.get("value", "")`
- Committed: `ecf372d`, `65a4ea3` — "fix(voice): Correct Azure OpenAI Realtime API endpoint path"
- Deployed backend with code fix
- Testing confirmed: 404 errors fixed, now getting 403 `AuthenticationTypeDisabled` (expected)

**Outstanding issue**

- API key auth is disabled on the Azure OpenAI resource (`disableLocalAuth: true`).
- Attempted to add `disableLocalAuth: false` to `infra/main.bicep` — property didn't take effect after `azd provision`.
- **Two options documented in `.squad/decisions.md`:**
  1. **Enable API key auth** (simpler): Run `az resource update --ids "/subscriptions/.../frontdoor-6wfum6gndxawy-openai" --set properties.disableLocalAuth=false`
  2. **Switch to Entra ID tokens** (more secure): Modify `AzureRealtimeService` to use `DefaultAzureCredential` and `Authorization: Bearer {token}` header instead of `api-key: {key}`

**Key file paths**

- `backend/app/services/azure/realtime.py` — Fixed session creation endpoint (deployed)
- `infra/main.bicep` — Added `disableLocalAuth: false` property (didn't work, needs investigation)
- `.squad/decisions.md` — Documented diagnosis and two resolution options

### 2026-03-14 — Realtime Auth Fix (via Anvil)

**Resolution completed by Anvil**

- **Bicep patch** (`infra/main.bicep`): Re-enabled API key auth with `disableLocalAuth: false` (verified to take effect)
- **Service enhancement** (`backend/app/services/azure/realtime.py`): Implemented async `DefaultAzureCredential` with API key fallback, auto-token-refresh before expiration
- **Config update** (`backend/app/core/config.py`): Made `azure_openai_api_key` optional
- **Error handling**: Status-code-specific messages (401: auth failed, 403: missing role, 5xx: service down)
- **Result**: 503 errors eliminated, realtime session endpoint fully operational, 76 voice tests passing
- **Commit**: `c44b389` — "feat(voice): Re-enable API key auth, add async DefaultAzureCredential with fallback"
- **Pushed**: ✅ to main

### 2026-03-15 — Fix Voice Transcript Config (Session Config Patch)

**Problem**

- Voice feature was live but transcripts never appeared in the UI.
- Root cause #1: `input_audio_transcription` was missing from the session config sent to Azure OpenAI `/client_secrets`. Without it, the Realtime API never emits `conversation.item.input_audio_transcription.completed` events — user speech is never transcribed.
- Root cause #2: `VOICE_SYSTEM_PROMPT` was defined at module top (line 6) but never actually sent. The `create_session()` method only included `instructions` when the caller explicitly passed one, which never happened in practice.

**Fix applied**

1. **`backend/app/services/azure/realtime.py`**
   - Added `"input_audio_transcription": {"model": "whisper-1"}` to the `session_config["session"]` dict.
   - Changed conditional `if instructions: session_config["session"]["instructions"] = instructions` → `session_config["session"]["instructions"] = instructions or VOICE_SYSTEM_PROMPT`. Now the system prompt is always sent.

2. **`backend/app/services/mock/realtime.py`**
   - Imported `VOICE_SYSTEM_PROMPT` from the Azure module (single source of truth).
   - Mirrored both config additions (`input_audio_transcription` + default instructions) for API contract consistency.
   - Stored config in `self._last_session_config` for test introspection.

**Verification:** 76 voice tests passing. Import checks clean for both Azure and mock services.

**Team Coordination:** Paired with Switch's frontend `session.update` data-channel implementation (parallel spawn 2026-03-15T01:53) for belt-and-suspenders transcription enablement. Backend config change ensures system prompt and transcription are always available; frontend change adds runtime safety net.

**Orchestration Log:** `.squad/orchestration-log/2026-03-15T01-53-tank.md`
