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
