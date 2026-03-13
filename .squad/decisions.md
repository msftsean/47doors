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

## Governance

- All meaningful changes require team consensus
- Document architectural decisions here
- Keep history focused on work, decisions focused on direction
