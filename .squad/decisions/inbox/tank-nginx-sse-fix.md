# Decision: Dedicated Nginx Location Block for SSE Streaming

**Timestamp:** 2026-03-16  
**Authority:** Tank (Backend Dev)  
**Status:** Implemented  

## Context

The live transcript page (`/live`) connected successfully but displayed no transcript text. SSE events from `/api/transcripts/stream` were silently buffered by nginx because the single `/api/` location block was configured for WebSocket semantics (`Connection "upgrade"`, no `proxy_buffering off`).

## Decision

Added a dedicated `location /api/transcripts/stream` block in `frontend/nginx.conf` with SSE-specific proxy settings:

- `proxy_buffering off` + `proxy_cache off` — disables nginx response buffering
- `proxy_set_header Connection ""` — uses HTTP keep-alive instead of WebSocket upgrade
- `proxy_read_timeout 86400` — allows long-lived SSE connections (24h)

The existing `/api/` block remains unchanged for regular REST calls and WebSocket (`/api/realtime/ws/`).

## Rationale

SSE and WebSocket have fundamentally different proxy requirements:
- **WebSocket:** needs `Connection "upgrade"` + `Upgrade` header
- **SSE:** needs `Connection ""` (keep-alive) + `proxy_buffering off`

Nginx longest-prefix matching ensures `/api/transcripts/stream` matches the SSE block before falling through to the general `/api/` block.

## Files Changed

- `frontend/nginx.conf` — added SSE location block before existing `/api/` block

## Risks

- None. The change is additive. The existing `/api/` block is untouched, so WebSocket and REST traffic are unaffected.
- If additional SSE endpoints are added in the future, they should either be nested under `/api/transcripts/` (already covered by prefix match) or get their own location block.
