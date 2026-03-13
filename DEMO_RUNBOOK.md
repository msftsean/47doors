# 🎤 47 Doors Voice Feature — Demo Runbook

> **Branch**: `002-voice-interaction` | **Audience**: EDU customers, stakeholders, internal demos
> **Last updated**: 2026-03-13 | **Estimated demo time**: 12–15 minutes

---

## 🎯 Demo Overview

The **47 Doors Universal Front Door Support Agent** now speaks. Students can click a single microphone button and have a natural spoken conversation with the same AI pipeline that powers text chat — getting ticket confirmations, knowledge article summaries, and escalation notices, all by voice. This demo shows how a university can replace dozens of disconnected support portals with **one trusted digital colleague** that works whether you type or talk.

---

## ✅ Pre-Demo Checklist

Run through this list **5 minutes before** you start the demo.

| # | Check | Status |
|---|-------|--------|
| 1 | **Browser**: Chrome 90+, Firefox 85+, or Edge 90+ open | ☐ |
| 2 | **Microphone**: Tested via browser audio settings (Settings → Privacy → Microphone) | ☐ |
| 3 | **Backend**: `uvicorn` running on **port 8000** — confirm at `http://localhost:8000/api/health` | ☐ |
| 4 | **Frontend**: Vite dev server running on **port 5173** — confirm at `http://localhost:5173` | ☐ |
| 5 | **Environment**: `MODE=mock` (default) set in `backend/.env` — no Azure credentials needed | ☐ |
| 6 | **Audio output**: System volume up, headset or speakers working | ☐ |
| 7 | **Fallback plan**: If voice fails mid-demo, text chat always works — just keep typing | ☐ |

> 💡 **Codespaces?** Leave `VITE_API_BASE_URL` blank — Vite proxies `/api` to `127.0.0.1:8000` automatically. Both port 5173 and port 8000 must be forwarded.

---

## 🚀 Start Commands

### Option A — Local Development (Recommended for Demos)

```bash
# Terminal 1 — Backend
cd backend
cp .env.example .env          # MODE=mock is already set
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

```bash
# Terminal 2 — Frontend
cd frontend
npm install
npm run dev                   # Opens http://localhost:5173
```

### Option B — Docker (One Command)

```bash
docker-compose up
# Frontend: http://localhost:5173
# Backend:  http://localhost:8000
```

### Option C — GitHub Codespaces

```bash
# Same as Option A — Vite proxy handles /api routing
# DO NOT set VITE_API_BASE_URL to a localhost URL inside Codespaces
# Leave it as empty string in frontend/.env.local:
echo "VITE_API_BASE_URL=" > frontend/.env.local
```

### Health Check (Verify before demoing)

```bash
curl http://localhost:8000/api/health
# Expected: { "status": "healthy", "services": { "realtime_api": "available" } }

curl http://localhost:8000/api/realtime/health
# Expected: { "realtime_available": true, "mock_mode": true }
```

---

## 🎬 Demo Sequence (12–15 Minutes)

---

### 🎭 Scene 1 — The 47 Doors Problem *(~3 min)*

**What to show:** The chat UI with text conversation working normally.

**Talk track:**

> *"Imagine being a first-year student at a large university. You have a password problem — but is that IT? Or is it your course portal? Maybe it's your library login? At most universities, there are literally **47 different front doors** for support. Students don't know which door to knock on, so they knock on all of them and wait."*

> *"47 Doors is the answer to that. One trusted digital colleague that knows every department, every process, and every knowledge article — and routes your request to exactly the right team."*

1. **Type** in the chat: `"I forgot my password and can't log into Canvas"`
2. **Show** the ticket ID returned, the KB articles, and the SLA estimate
3. **Point out**: One input → intent detected → ticket created → KB surfaced → SLA communicated

> *"This is what we built for text. Today, I'm going to show you the same experience — but spoken out loud."*

---

### 🎤 Scene 2 — Voice Interaction *(~4 min)*

**What to show:** The full voice round-trip — click mic, speak, hear a response, see the transcript.

**Talk track:**

> *"Let me show you what it looks like when a student just wants to talk."*

1. **Point to** the 🎤 microphone button in the chat input area
   > *"One button. That's the entire voice interface."*

2. **Click the mic button** — the button pulses green
   > *"The browser asks for mic permission — we request it, the student grants it, and we're live. Notice the status banner at the top: it says 'Listening...'"*

3. **Speak clearly**: *"I forgot my password and can't log into Canvas"*
   > *"Speak naturally. No commands, no keywords — just say what you need."*

4. **While processing** — point to the spinner state
   > *"The agent heard me finish speaking. Now it's running the same 3-agent pipeline we just saw in text — intent detection, routing, action. That's the WebSocket tool relay working in the background."*

5. **When the agent responds** — point to the transcript bubble with 🔊 icon
   > *"The agent speaks the answer back AND adds it to the chat thread with a speaker icon so there's always a written record. No audio is stored — only this PII-filtered transcript."*

6. **Ask a follow-up question verbally**: *"Can you check the status of that ticket?"*
   > *"Now I'm asking a follow-up without re-explaining anything. The session context is shared — voice and text are the same session."*

7. **Click mic button again** to stop — status returns to idle
   > *"Done. I stopped talking, the mic is off. I can pick up the conversation in text right now without losing a single message."*

---

### 🔍 Scene 3 — Observability & Trust *(~3 min)*

**What to show:** Health endpoint, audit trail, session sharing.

**Talk track:**

> *"University IT teams ask: 'How do we know what the AI is doing? How do we audit it?' Great question."*

1. **Open a new browser tab**, navigate to `http://localhost:8000/api/realtime/health`
   ```json
   { "realtime_available": true, "mock_mode": true }
   ```
   > *"This endpoint tells the frontend whether voice is available. If it returns false, the mic button never even appears — there's no broken state to deal with."*

2. **Navigate to** `http://localhost:8000/api/health`
   > *"Full health check — every service, including the Realtime API, has a status entry."*

3. **Back in the chat**, scroll through the conversation history
   > *"Every voice interaction is logged with `input_modality: voice`. Admins can filter logs to see exactly which queries came through voice, when, and what the agent did. No audio, no PII — just a clean audit trail."*

4. **Highlight** that voice and text messages share the same session
   > *"The session ID is identical whether a student types or speaks. That means support staff see a coherent conversation history, not two separate logs."*

---

### 🛡️ Scene 4 — Graceful Degradation *(~2 min)*

**What to show:** Voice unavailable → text chat continues seamlessly.

**Talk track:**

> *"The most important thing about a feature like this is what happens when it doesn't work."*

1. **Temporarily disable voice**: In `backend/.env`, set `VOICE_ENABLED=false`, restart uvicorn
2. **Refresh the frontend** — mic button is **gone entirely**
   > *"When voice isn't available, we don't show a broken button — we remove it. The student sees a normal, fully functional text chat."*

3. **Type** a message and get a response
   > *"Text chat is completely unaffected. Voice uses separate WebRTC and WebSocket connections — there's zero coupling to the text pipeline."*

4. **Re-enable**: Set `VOICE_ENABLED=true`, restart — mic button reappears

> *"Graceful degradation isn't just a buzzword here. It's a constitutional requirement baked into the architecture from day one."*

---

### 🔭 Scene 5 — What's Next *(~2 min)*

**Talk track:**

> *"What you just saw is the MVP — running in mock mode, which means no Azure credentials required. Here's what the path to production looks like."*

1. **Production deployment**: Swap `MODE=production` and provide an Azure OpenAI Realtime API deployment (`gpt-4o-realtime-preview`) — the same Bicep templates in `infra/` already include it
2. **Accessibility hardening**: WCAG 2.1 AA audit, screen reader testing with JAWS/NVDA
3. **Real Azure Realtime API**: Sub-2-second voice response latency with the live WebRTC transport
4. **Analytics**: Voice vs. text resolution rate comparison, VAD tuning per environment

> *"The architecture is already there. The tests are green — 76 backend tests pass. Turning this on in production is a configuration change, not a code change."*

---

## 🔧 Troubleshooting Table

| Issue | Cause | Fix |
|-------|-------|-----|
| 🚫 Mic permission denied | Browser blocked microphone access | Click the 🔒 lock icon in the address bar → Allow Microphone, then refresh |
| 🔌 WebSocket fails / 4001 | Ephemeral token expired (TTL ≤ 60 s) | Request a new token via `POST /api/realtime/session` — the hook retries automatically |
| 🔌 WebSocket closes 4002 | `session_id` not found | Verify UUID in query params matches a live session; reload the page |
| 🔇 No audio output | System volume muted / wrong output device | Check system audio settings; try a headset |
| 🌊 VAD not triggering / false triggers | Background noise | Use a headset in a quiet room; adjust `REALTIME_VAD_THRESHOLD_MS` in `.env` |
| 🎤 "Voice unavailable" banner | Backend not running or voice disabled | Confirm `uvicorn` is on port 8000; check `VOICE_ENABLED=true` in `.env` |
| 🚫 503 on POST /session | `VOICE_ENABLED=false` in config | Set `VOICE_ENABLED=true` in `backend/.env` and restart uvicorn |
| 🎤 Mic button not shown | `realtime_available: false` from health check | Check `GET /api/realtime/health`; confirm backend is running and `MODE=mock` |
| 📝 Transcript not appearing | Voice components not rendered | Confirm `ChatContainer.tsx` is importing `VoiceTranscript`; check browser console |
| 💬 Text chat broken after voice | Should not happen (separate connections) | Hard-reload the page; file a bug if it persists — check `ChatContainer.tsx` state isolation |
| 🔒 WebRTC ICE failure (live mode) | Azure endpoint/region misconfigured | Verify `AZURE_OPENAI_ENDPOINT` and `AZURE_OPENAI_REALTIME_DEPLOYMENT` in `.env` |
| 🌐 Codespaces: API calls fail | `VITE_API_BASE_URL` set to localhost | Clear `VITE_API_BASE_URL` — Vite proxy handles `/api` routing automatically |

---

## 🏫 EDU Reusable Framing

### The "47 Front Doors" Problem

Universities are not monolithic. A typical large institution has separate portals for:
IT support, financial aid, housing, dining, registrar, library, advising, health services, parking, athletics, career services... and more. Students waste hours figuring out **which door to knock on** — and often knock on the wrong one.

> **The pitch**: *"What if there was one door? One place where any student question — regardless of department — is heard, understood, and routed correctly?"*

### The "Trusted Digital Colleague" Narrative

47 Doors is not a chatbot. It is a **digital colleague** — one that:
- Knows the org chart (routes to the right team)
- Knows the knowledge base (surfaces relevant articles)
- Knows when to escalate (policy triggers, sensitivity detection)
- Remembers the conversation (session context across turns and modalities)
- Never stores what shouldn't be stored (no raw audio, PII-filtered transcripts)

Voice makes this colleague feel **present** — not like filling out a form, but like asking a knowledgeable colleague in the hallway.

### Applicable to Any University

This architecture is institution-agnostic. The 3-agent pipeline (QueryAgent → RouterAgent → ActionAgent) maps to any university's department taxonomy. The mock mode means any institution can demo it today, with zero Azure spend, and decide on production deployment after seeing it work for their specific use cases.

> **The close**: *"You're not buying a chatbot. You're giving every student a trusted digital colleague who is always available, always accurate, and always gets them to the right place — whether they type or talk."*

---

*Runbook maintained by the 47 Doors engineering team. For issues, open a GitHub issue on `002-voice-interaction`.*
