# Project Context

- **Owner:** msftsean
- **Project:** 47 Doors — Universal Front Door Support Agent for university student support
- **Stack:** Python 3.11+ / FastAPI 0.109+, TypeScript 5 / React 18, Azure OpenAI, Azure AI Search, Pydantic v2.5+
- **Architecture:** Three-agent pipeline (QueryAgent → RouterAgent → ActionAgent) with voice interaction via Azure OpenAI GPT-4o Realtime API / WebRTC
- **Created:** 2026-03-13

## Learnings

- **Doc Fleet Pattern**: Major features ship across four parallel doc surfaces: (1) technical specs in `specs/` (Tank's domain), (2) runbook/workshop site (Switch's domain), (3) participant & coach guides (narrative, Morpheus), (4) release notes + changelog (both coordinated). When a feature ships to production, all four surfaces must be updated for coherent narrative flow and participant understanding.

## Work Log

### 2026-04-21T22:30:00Z — Phone Bridge Live: Narrative Doc Sweep (Morpheus)
Updated participant-facing and coach docs to reflect production-verified phone integration.

**Changes:**
- `docs/RELEASE_NOTES.md` — Added Version 0.1.5 entry noting phone bridge live, bidirectional transcripts, production architecture
- `docs/bootcamp/PARTICIPANT_GUIDE.md` — Updated "What You're Building" to reflect phone calls fully working (not just "coach demo"); updated bonus assessment criteria
- `docs/bootcamp/QUICK_REFERENCE.md` — Clarified live phone number (+1-913-217-1946), corrected Phone env vars table (required vs. default), emphasized production verification
- `coach-guide/FACILITATION.md` — Inverted voice/phone demo section to assert "phone demo is live"
- `coach-guide/TALKING_POINTS.md` — Added production-verified backend stack to voice/phone transition talking point
- `coach-guide/TROUBLESHOOTING.md` — Replaced phone troubleshooting entries with verification steps and expected signals on `/live`

**Commit:** `599cc8e`

**Cross-team coordination:** Tank updated backend code & CHANGELOG; Switch updating runbook site. This update completes the narrative surface (participant guides, coach guides, release notes).

### 2026-03-13T18:46:00Z — Azure-First Spec Update (Morpheus)
Updated `specs/002-voice-interaction/spec.md` to prioritize Azure Container Apps as primary deployment target.

**Changes:**
- MVP scope: Added "Azure Container Apps deployment"
- VFR-026–029: Deployment requirements (Azure primary, local dev secondary, parity)
- Updated assumptions and dependencies to reflect Azure-first strategy
- Mock mode clarified as dev/test tool, not demo default

**Commit:** `71a91d6`

**Cross-agent impact:** Tank's Phase 1 deployment config must align with these requirements.
