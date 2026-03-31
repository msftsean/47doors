# Project Context

- **Owner:** msftsean
- **Project:** 47 Doors — Universal Front Door Support Agent for university student support
- **Stack:** Python 3.11+ / FastAPI 0.109+, TypeScript 5 / React 18, Azure OpenAI, Azure AI Search, Pydantic v2.5+
- **Architecture:** Three-agent pipeline (QueryAgent → RouterAgent → ActionAgent) with voice interaction via Azure OpenAI GPT-4o Realtime API / WebRTC
- **Created:** 2026-03-13

## Learnings

<!-- Append new learnings below. Each entry is something lasting about the project. -->

### 2026-03-19 — Workshop Companion Site Build

**Architecture decisions:**
- Built standalone React + TypeScript + Tailwind CSS site at `workshop-site/` as executive briefing tool for "Trustworthy Agentic AI in Higher Education" workshop
- Microsoft Fluent 2 visual language: generous whitespace, calm typography, restrained color palette
- Primary colors: Microsoft blue (#0078D4), neutral gray (#F3F2F1), dark text (#323130)
- IU crimson (#990000) used SPARINGLY for callout borders — accent color, not primary
- 10 tab-based sections covering full 47 Doors narrative: Problem → Architecture → Trust → Voice → Demo → Governance

**Component architecture:**
- Tab navigation with keyboard accessibility (arrow keys, Tab/Shift+Tab, Enter/Space)
- Reusable components: TabNavigation, CollapsibleNotes, CalloutCard, DiagramSVG
- Each tab is standalone React component in `src/tabs/` — deep-linkable design
- SVG diagrams with semantic markup (figure/figcaption, aria-labels, title/desc elements)
- No external component libraries — lightweight, Heroicons only

**Key file paths:**
- Site root: `workshop-site/`
- Main app: `workshop-site/src/App.tsx` (tab state management)
- Tab components: `workshop-site/src/tabs/*.tsx` (10 total: Overview, TheProblem, ChatbotsToAgents, TrustBoundaries, Architecture, VoiceAccessibility, DemoWalkthrough, ResponsibleAI, ReuseAcrossCampus, YourFirstAgent)
- Reusable UI: `workshop-site/src/components/*.tsx`
- README: `workshop-site/README.md` (install/run instructions)

**User preferences observed:**
- Calm, academic tone — NO flashy marketing energy
- Text-light, visually rich — icons, diagrams, callout cards over dense paragraphs
- Speaker notes as collapsible sections (preserve presentation context without cluttering UI)
- Interactive "Your First Agent" exercise (client-side only, no backend) with live-updating agent card
- High contrast text (WCAG AA 4.5:1 minimum), semantic HTML, keyboard navigation
- Design principle: "This should feel like a confident executive briefing, not a product pitch"

**Content patterns:**
- Each tab has: headline, visual elements (diagrams/cards), callout cards for key insights, collapsible presenter notes
- Diagrams use inline SVG with DiagramSVG wrapper for accessibility
- "What to Notice" callouts highlight architectural insights
- Demo walkthrough uses numbered step cards with visual labels and notes
- "Your First Agent" tab uses controlled inputs with example chips for quick selection

**Build verification:**
- TypeScript typechecks clean (`npm run typecheck` passes)
- Production build succeeds: 222.94 kB JS (63.50 kB gzipped), 16.28 kB CSS (3.58 kB gzipped)
- 371 modules transformed, built in 2.15s
- Local dev: `npm run dev` (Vite dev server on port 5173)

### 2026-03-14 — Azure Static Web Apps Auth Migration (docs runbook)

**Architecture decisions:**
- Runbook site migrated from GitHub Pages → Azure Static Web Apps for built-in authentication.
- Auth provider: Azure AD (Microsoft Entra ID) only — GitHub/Twitter providers explicitly blocked with 404.
- `staticwebapp.config.json` route rules: `/.auth/login/aad` + `/.auth/logout` are `anonymous`; all other routes require `authenticated` role; 401 redirects to AAD login.
- Auth bar integrated into existing sticky nav (right-aligned `.nav-auth` div) — uses `/.auth/me` fetch to show username; hidden on local dev when endpoint unavailable (silent catch).

**Key file paths:**
- SWA config: `docs/staticwebapp.config.json`
- Setup guide: `docs/AZURE_SWA_SETUP.md`
- GitHub Actions workflow: `.github/workflows/deploy-docs-swa.yml`
- Deployment secret expected: `AZURE_STATIC_WEB_APPS_API_TOKEN` (user adds after SWA resource creation)

**User preferences observed:**
- Auth UI must be minimal — user said "don't distract from runbook content"
- Dark theme, purple accent, Inter font — all auth elements use existing CSS variables
- Setup docs use bash (not PowerShell) with emojis for readability
- Local dev graceful degradation is a hard requirement (auth bar hides if `/.auth/me` unavailable)

**Architecture decisions:**
- Audio never transits the backend — WebRTC connects browser → Azure OpenAI directly. Backend only relays tool call results via `/api/realtime/ws`.
- Ephemeral token TTL ≤ 60 s is a hard constitutional constraint (Voice Channel Security); tokens are single-use and non-renewable.
- `session_id` is shared between text chat and voice sessions — voice attaches to the existing `Session` entity so modality switching preserves context.

**Key file paths:**
- OpenAPI contract: `specs/002-voice-interaction/contracts/voice-api.yaml`
- Quickstart guide: `specs/002-voice-interaction/quickstart.md`
- Planned backend router: `backend/app/api/realtime.py` (not yet created)
- Planned frontend hook: `frontend/src/hooks/useVoice.ts` (not yet created)
- Existing router pattern: `backend/app/api/routes.py` (FastAPI `APIRouter`, mounted at `settings.api_prefix` = `/api`)
- Vite proxy config: `frontend/vite.config.ts` — `/api` → `http://127.0.0.1:8000`; WebSocket proxy is handled automatically.
- Env example: `backend/.env.example` — `MODE=mock` is the default; voice adds `AZURE_OPENAI_REALTIME_DEPLOYMENT`.

**Patterns to follow:**
- Router uses `APIRouter()` with full `responses={}` dicts for all non-200 status codes.
- All response models use Pydantic v2 schemas defined in `backend/app/models/`.
- Health check pattern: always returns HTTP 200; use field values (`realtime_available`) for capability detection, not HTTP status.
- WebSocket close code conventions: 4001 = invalid token, 4002 = session expired (custom range above 4000 for app-level errors).

### 2026-03-14 — session.update via Data Channel for Transcription

**What:** Added `dc.onopen` handler in `useVoice.ts` that sends a `session.update` event through the WebRTC data channel to enable `input_audio_transcription` (whisper-1 model). Without this, the Azure OpenAI Realtime API never emits `conversation.item.input_audio_transcription.completed` events — meaning user speech is never transcribed.

**Why belt-and-suspenders:** The backend (Tank) is also being updated to include `input_audio_transcription` in the initial session config. The frontend `session.update` is a safety net — if the backend config is ever missing or the API ignores the initial config, the data-channel message ensures transcription is active before we start listening.

**Side benefit:** Moved the `LISTENING` dispatch into `dc.onopen` instead of relying on `pc.onconnectionstatechange`. The data channel being open is the actual prerequisite for sending/receiving events — more semantically correct than peer connection state alone.

**Key files:**
- `frontend/src/hooks/useVoice.ts` — added `dc.onopen` handler (lines 106–116)

**Team Coordination:** Coordinated with Tank's parallel backend session config changes (spawn 2026-03-15T01:53). Both changes are idempotent and reinforce each other. Frontend ensures transcription is active; backend ensures system prompt is sent.

**Verification:** TypeScript compiles clean. Code review passed (Morpheus).

**Orchestration Log:** `.squad/orchestration-log/2026-03-15T01-53-switch.md`
