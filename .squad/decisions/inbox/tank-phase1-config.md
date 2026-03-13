# Decision Record: Phase 1 Setup — Voice Config, Env, Bicep

**Author:** Tank (Backend Dev)  
**Date:** 2026-03-14  
**Requested by:** msftsean  
**Scope:** T001, T002, T003 from `specs/002-voice-interaction/tasks.md`

---

## T001 — Voice Config Fields (`backend/app/core/config.py`)

**Decision:** Used `model_validator(mode="after")` (Pydantic v2 API) rather than a `@validator` (v1 API) because the existing codebase uses Pydantic v2.5+ throughout.

**Fields added:**
| Field | Default | Notes |
|---|---|---|
| `voice_enabled` | `True` | Kill switch |
| `azure_openai_realtime_deployment` | `""` | Empty → auto-disable |
| `azure_openai_realtime_api_version` | `"2025-04-01-preview"` | Realtime endpoint version |
| `realtime_voice` | `"alloy"` | Azure voice |
| `realtime_vad_threshold_ms` | `500` | ms |
| `max_voice_session_duration` | `600` | seconds (10 min) |

**Validator logic:** `voice_enabled` is set to `False` when `azure_openai_realtime_deployment == ""` AND `mock_mode == False`. Mock mode keeps voice alive for local dev without real credentials.

**Placement:** New `# Voice / Realtime API Settings` section after `# SLA Configuration`, before `@property` methods — consistent with the existing section comment style.

---

## T002 — `.env.example` Update (`backend/.env.example`)

**Decision:** Used `gpt-4o-realtime-preview` as the stub value (matches `tasks.md` line T002). The user task brief showed `gpt-4o-realtime`; `tasks.md` is the canonical source so `gpt-4o-realtime-preview` was used.

---

## T003 — Bicep Realtime Deployment (`infra/main.bicep`)

**Decision:** Added `dependsOn: [openAiDeployment]` to the new `openAiRealtimeDeployment` resource. Azure OpenAI rate-limits concurrent deployment operations; serializing them avoids quota-throttle failures during `azd provision`.

**Output added:** `AZURE_OPENAI_REALTIME_DEPLOYMENT` — allows `azd` to automatically wire the deployment name into Container App environment variables without manual configuration.

**Capacity set to 1 TPM-unit** as specified (realtime is expensive; start minimal, scale up manually).

---

## Verification

```
python -c "from app.core.config import Settings; s = Settings(); print(f'voice_enabled={s.voice_enabled}')"
# → voice_enabled=True  (mock_mode=True by default; deployment value from local .env)

python -c "from app.core.config import Settings; s = Settings(azure_openai_realtime_deployment='', mock_mode=False); print(f'voice_enabled={s.voice_enabled}')"
# → voice_enabled=False  (validator fired correctly)
```

Both checks passed. Phase 1 unblocked.
