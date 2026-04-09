# Decision: WebSocket Bridge for ACS→Azure OpenAI Audio Relay

**Timestamp:** 2026-04-09T01:57Z  
**Author:** Tank (Backend Dev)  
**Status:** Implemented & Deployed  
**Commit:** b2d7abc

## Context

Phone calls to +19132171946 connected (call answered) but produced dead air — no audio in either direction. ACS media streaming was configured to connect directly to Azure OpenAI Realtime API's WebSocket, but:

1. Azure OpenAI has `disableLocalAuth: true` — only Entra ID/token auth accepted
2. ACS resource has NO managed identity and NO RBAC role on the OpenAI resource
3. `MediaStreamingOptions.transport_url` provides no mechanism for auth headers
4. ACS Call Automation callback events (CloudEvents format) were all rejected with 400, hiding the `MediaStreamingFailed` diagnostic event

## Decision

Route ACS media streaming through a backend WebSocket bridge (`/ws/acs-media`) instead of connecting ACS directly to Azure OpenAI.

```
PSTN → ACS → WS [backend /ws/acs-media] → WS [Azure OpenAI Realtime API]
```

The backend authenticates to Azure OpenAI using its existing managed identity (which already has the Cognitive Services OpenAI User RBAC role).

## Alternatives Considered

1. **Enable ACS system-assigned managed identity + RBAC role on OpenAI**: Would require infra changes (Bicep), and it's unclear whether `cognitive_services_endpoint` in `answer_call()` actually authenticates media streaming WebSocket connections (docs only mention it for speech/transcription features).

2. **Embed ephemeral token in WebSocket URL query param**: Azure OpenAI Realtime API doesn't support auth via URL query parameters for WebSocket connections.

3. **Disable `disableLocalAuth` on OpenAI**: Security regression — was set to `true` intentionally.

## Rationale

- Backend bridge is the documented pattern in all official Azure samples (e.g., `Azure-Samples/communication-services-openai-sample`)
- Backend already has the RBAC role — no infra changes needed
- Gives full control over session configuration, tool calls, barge-in
- No audio format conversion needed: ACS PCM24K_MONO = OpenAI pcm16 (24kHz 16-bit mono)
- Also fixed CloudEvents callback parsing as part of this change

## Impact

- New file: `backend/app/api/media_ws.py`
- Modified: `phone.py` service (transport_url), `phone.py` API (callbacks), `main.py` (route)
- All 447 tests pass
- No infra changes required
