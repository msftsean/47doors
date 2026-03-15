# Project Context

- **Owner:** msftsean
- **Project:** 47 Doors — Universal Front Door Support Agent for university student support
- **Stack:** Python 3.11+ / FastAPI 0.109+, TypeScript 5 / React 18, Azure OpenAI, Azure AI Search, Pydantic v2.5+
- **Architecture:** Three-agent pipeline (QueryAgent → RouterAgent → ActionAgent) with voice interaction via Azure OpenAI GPT-4o Realtime API / WebRTC
- **Created:** 2026-03-13

## Learnings

<!-- Append new learnings below. Each entry is something lasting about the project. -->

## Work Log

### 2026-03-13T18:46:00Z — Azure-First Spec Update (Morpheus)
Updated `specs/002-voice-interaction/spec.md` to prioritize Azure Container Apps as primary deployment target.

**Changes:**
- MVP scope: Added "Azure Container Apps deployment"
- VFR-026–029: Deployment requirements (Azure primary, local dev secondary, parity)
- Updated assumptions and dependencies to reflect Azure-first strategy
- Mock mode clarified as dev/test tool, not demo default

**Commit:** `71a91d6`

**Cross-agent impact:** Tank's Phase 1 deployment config must align with these requirements.
