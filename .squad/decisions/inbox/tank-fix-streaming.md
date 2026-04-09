# Decision: Fix Phone Bridge Transcript Streaming + Real Tool Execution

**Author:** Tank  
**Date:** 2026-04-09  
**Status:** Implemented & Deployed

## Context

Sean reported two bugs during phone call testing:
1. Chat responses (agent speech) not showing up in the live transcript viewer
2. Phone calls can't create tickets or route to humans — tools returned mock data

## Decisions Made

### 1. GA Event Name Migration (media_ws.py)

The ACS↔OpenAI media bridge was listening for `response.audio_transcript.done` (preview Realtime API event). The deployed GA api-version (`2025-04-01-preview`) sends `response.output_audio_transcript.done`. Updated to GA name.

**Impact on Switch:** None — the SSE contract (event types `call_started`, `user_speech`, `agent_speech`, `tool_call`, `call_ended`) is unchanged. The frontend `useTranscriptStream` hook doesn't need changes.

### 2. Real Service Wiring for Phone Tools (azure/realtime.py)

Replaced hardcoded mock responses in `AzureRealtimeService.execute_tool()` with real backend service calls:

| Tool | Service Called | What It Does |
|------|--------------|-------------|
| `analyze_and_route_query` | `llm_service.classify_intent()` + `ticket_service.create_ticket()` | Classifies intent via LLM, creates real ticket |
| `check_ticket_status` | `ticket_service.get_ticket_status()` | Looks up real ticket by ID |
| `search_knowledge_base` | `knowledge_service.search()` | Searches real KB (Azure AI Search or mock) |
| `escalate_to_human` | `ticket_service.create_ticket()` with URGENT priority | Creates escalation ticket |

Services are obtained via lazy import from `dependencies.py` (avoids circular imports, uses cached singletons).

**MockRealtimeService unchanged** — tests continue using mock responses. Only the Azure production service now calls real services.

### 3. Error Handling Strategy

All tool execution is wrapped in try/except. On failure, the error message is returned to the Realtime API model as a `ToolCallResponse(error=...)`, allowing the AI to gracefully tell the caller something went wrong rather than hanging silently.

## Risks

- `analyze_and_route_query` adds ~2-4s latency (LLM classify + ticket create). Acceptable for voice UX since the AI was already waiting for the tool result.
- No ServiceNow integration yet — `get_ticket_service()` returns `MockTicketService` even in production. Tickets are in-memory. This is a known gap (TODO in dependencies.py).

## Validation

- 455 tests pass (0 failures)
- Deployed via `azd deploy backend`
- Health check: all services UP
- SSE endpoint confirmed streaming keepalives
