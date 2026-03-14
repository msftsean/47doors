# Squad Decisions

## Active Decisions

### Model Selection Directive
**Timestamp:** 2026-03-13T13-09-59  
**Authority:** User (msftsean via Copilot)  
**Decision:** 
- Code-writing agents (Tank, Switch, Mouse, Neo): use `claude-sonnet-4.6`
- Non-code agents (Scribe, documentation, evals, Morpheus when not reviewing): use `claude-haiku-4.6`

**Rationale:** Optimize for cost vs. quality based on task type. Code work requires full Sonnet capability; administrative/documentation work can use faster Haiku model.

### Azure Resources Ready for Live Testing
**Timestamp:** 2026-03-13T17:34  
**Authority:** User (msftsean via Copilot)  
**Decision:** Azure resources provisioned and ready for live voice testing.
- **Resource Group:** `rg-47doors-voice` (eastus2)
- **Resource Name:** `oai-47doors-voice`
- **Deployments:** `gpt-4o` + `gpt-4o-realtime`

**Rationale:** User directive to plan for live Azure testing, not just mock mode. Infrastructure is in place and ready for Phase 3+ endpoint validation.

### Azure-First Deployment Strategy
**Timestamp:** 2026-03-13T18:46:00Z  
**Authority:** User (msftsean via Morpheus)  
**Decision:** Spec update to make Azure Container Apps the primary deployment target.

- **VFR-026**: Azure Container Apps via `azd up` is PRIMARY
- **VFR-027**: Local dev as secondary path via `uvicorn`
- **VFR-028**: No code changes needed between deployments
- **VFR-029**: Health checks work identically in both environments

**Rationale:** User directive — production and demo environments should run on Azure, not locally. Mock mode repositioned as development/testing tool.

### Phase 1 Setup — Voice Config, Env, Bicep
**Timestamp:** 2026-03-14  
**Authority:** Tank (Backend Dev)  
**Decision:** Voice configuration strategy for `backend/app/core/config.py`

**Key Decisions:**
- Used Pydantic v2 `model_validator(mode="after")` for voice validation (consistent with codebase v2.5+ usage)
- Voice config fields:
  - `voice_enabled` (default `True`): Kill switch, disabled when `azure_openai_realtime_deployment == ""` AND `mock_mode == False`
  - `azure_openai_realtime_deployment` (default `""`): Empty value auto-disables voice in prod mode
  - `azure_openai_realtime_api_version` (default `"2025-04-01-preview"`): Realtime endpoint version
  - `realtime_voice` (default `"alloy"`): Azure voice selection
  - `realtime_vad_threshold_ms` (default `500`): Voice activity detection threshold
  - `max_voice_session_duration` (default `600`): Session timeout (10 min)

- `.env.example`: Added `AZURE_OPENAI_REALTIME_DEPLOYMENT=gpt-4o-realtime-preview` as stub
- `infra/main.bicep`: Added `openAiRealtimeDeployment` resource with:
  - `dependsOn: [openAiDeployment]` to serialize operations (avoid rate-limit throttling)
  - Capacity: 1 TPM-unit (minimal, scale manually as needed)
  - Output: `AZURE_OPENAI_REALTIME_DEPLOYMENT` for azd auto-wiring

**Rationale:** Phase 1 unblocks deployment configuration. Mock mode enables local development; validator logic ensures voice is disabled in production without credentials.

### Voice Data Model Architecture
**Timestamp:** 2026-03-13  
**Authority:** Tank (Backend Dev)  
**Decision:** Additive-only model strategy for voice entities

**Key Decisions:**
1. **File Organization**
   - New voice models in `backend/app/models/voice_schemas.py` and `backend/app/models/voice_enums.py` (not appended to existing files)
   - Reduces merge conflicts with parallel feature work
   - Keeps existing `schemas.py` lean (430+ lines already)

2. **Data Model Integration**
   - `VoiceMessage.input_modality: Literal["voice"]` acts as discriminator (text/voice coexist in shared history)
   - Cheaper than union types or separate history stores
   - Aligns with spec VFR-010 (shared transcript) + Constitution Principle IV (session continuity)
   - `VoiceState.transcript` is append-only with `max_length=100` (matches `Session.conversation_history` cap pattern)

3. **Auth & Persistence**
   - No new auth model — reuse `Session.session_id: UUID` as voice↔text join key
   - Zero schema migration required; UUID index already exists
   - Trivially maps to future persistence layer (Cosmos DB): `WHERE session_id = ?`

4. **Tool Call Models**
   - `ToolCallRequest` / `ToolCallResponse` marked explicitly transient ("never persisted" in docstring)
   - Prevents PII leaks from tool arguments/results into audit logs before PII-filter pass
   - Aligns with Constitution Principle I (pipeline integrity)

**Rationale:** Additive strategy reduces friction with parallel work. Discriminator pattern is simpler and aligns with existing session model. Explicit transience markers document the PII-safety constraint for future implementers.

### Azure Static Web Apps Auth for Runbook Site
**Timestamp:** 2026-03-14  
**Authority:** Switch (Frontend Dev)  
**Decision:** Use Azure Static Web Apps (SWA) with Azure AD (Microsoft Entra ID) authentication for docs runbook site

**Key Decisions:**
- **Identity provider:** Azure AD only (Microsoft login)
- **Auth enforcement:** All routes require `authenticated` role; 401 auto-redirects to `/.auth/login/aad`
- **User display:** `/.auth/me` endpoint surfaced in nav bar; degrades gracefully on local dev
- **Blocked providers:** GitHub, Twitter (return 404)

**Affected Files:**
- `docs/staticwebapp.config.json` — SWA route rules and auth config
- `docs/index.html` — `.nav-auth` bar + `/.auth/me` JS
- `.github/workflows/deploy-docs-swa.yml` — CI/CD deployment
- `docs/AZURE_SWA_SETUP.md` — Operator setup guide

**Rationale:** EDU/Microsoft audience context. SWA built-in auth requires no app-level middleware. Restricts runbook access (internal tooling, demo sequences) to authenticated Microsoft accounts. Local dev parity via graceful `/.auth/me` fallback.

### Azure OpenAI Managed Identity Authentication
**Timestamp:** 2026-03-13T23:00Z  
**Authority:** Anvil (Production Fix)  
**Decision:** Use system-assigned managed identity for Azure OpenAI authentication instead of API keys

**Key Decisions:**
- **Backend Authentication:**
  - `AzureRealtimeService` uses `DefaultAzureCredential` from `azure-identity` for token-based auth
  - API key support retained as fallback for local development (optional parameter)
  - Token auto-refresh before expiration (checks `expires_on` timestamp)
  
- **Infrastructure Changes (`infra/main.bicep`):**
  - Set `disableLocalAuth: true` on Azure OpenAI resource (enforce managed identity)
  - Removed `azure-openai-api-key` secret from backend container app
  - Added `identity: { type: 'SystemAssigned' }` to backend container app
  - Created role assignment: `Cognitive Services OpenAI User` role for backend managed identity
  - Removed `AZURE_OPENAI_API_KEY` environment variable injection

- **Error Handling:**
  - Status-code-specific error messages (401: auth failed, 403: missing role, 404: deployment not found, 5xx: service unavailable)
  - Network errors surfaced with endpoint URL for debugging
  - All errors wrapped in `VoiceUnavailableError` with detailed context

- **Configuration:**
  - `azure_openai_api_key` now optional in `config.py` (description updated)
  - `dependencies.py` passes `api_key=None` when unset, triggering managed identity path
  - Mock mode unaffected (no Azure credentials required)

**Affected Files:**
- `backend/app/services/azure/realtime.py` — Token-based auth with credential refresh
- `backend/app/core/config.py` — Made API key optional
- `backend/app/core/dependencies.py` — Pass None for API key when unset
- `infra/main.bicep` — System-assigned identity + RBAC role assignment

**Rationale:** Deployed frontend was hitting 503 errors because Azure OpenAI had `disableLocalAuth: true` (API key auth rejected with 403). Managed identity is Azure best practice for container apps — no secrets in config, auto-rotated tokens, and RBAC-controlled access. API key fallback preserves local dev workflow without Azure credentials.

### Realtime API Authentication Fix
**Timestamp:** 2026-03-14  
**Authority:** Tank (Backend Dev)  
**Status:** Requires user decision  
**Decision:** Diagnosed and fixed 503 error on `/api/realtime/session`; awaiting auth configuration choice

**Problem:**
- Frontend getting 503 when calling `POST /api/realtime/session`
- Root cause: Wrong Azure OpenAI Realtime API endpoint URL → 404 (fixed)
- Secondary issue: Azure OpenAI resource has `disableLocalAuth: true` → 403 (pending)

**Code Fixes Applied:**
1. Changed endpoint URL from `/openai/deployments/{deployment}/realtime/sessions` to `/openai/v1/realtime/client_secrets`
2. Updated request body to nested session configuration structure per Microsoft docs
3. Updated response parsing to extract token from `data.get("value")`
4. Attempted to add `disableLocalAuth: false` to bicep (didn't take effect)

**Resolution Options:**
1. **Quick fix:** Run `az resource update --set properties.disableLocalAuth=false` to enable API key auth
2. **Secure fix:** Modify `AzureRealtimeService` to use `DefaultAzureCredential` for Entra ID authentication

**Recommendation:** Option 1 for immediate unblock; Option 2 for production security best practices.

**Affected Files:**
- `backend/app/services/azure/realtime.py` — Fixed session creation endpoint
- `infra/main.bicep` — Added disableLocalAuth property (didn't work)

## Governance

- All meaningful changes require team consensus
- Document architectural decisions here
- Keep history focused on work, decisions focused on direction
