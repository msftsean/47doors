# Next Feature Recommendation: Conversation Persistence & History

**Timestamp:** 2026-04-21T23:00:00Z  
**Authority:** Morpheus (Lead)  
**Requested by:** msftsean (Sean)  
**Status:** Awaiting decision

---

## Recommendation

**Build next: Conversation Persistence & History**

Add persistent session storage (Cosmos DB or Azure Table Storage) so students can resume conversations across browser sessions, view their past conversation history (text + voice transcripts), and retrieve ticket IDs from previous sessions. Include admin dashboard showing active sessions, session duration metrics, and conversation counts per department.

---

## Rationale

The phone demo landed perfectly — callers speak, transcripts render live, the 3-agent pipeline handles real queries. But the demo narrative is "single-call magic": student calls once, gets answer, hangs up. Real student support is a *journey* across days or weeks. Without persistence, every session is ephemeral — students can't return, coaches can't audit, and the "universal front door" metaphor breaks down.

**Why this feature, why now:**

1. **Closes the demo → production gap with minimal risk**: Persistence is pure additive infrastructure (Cosmos DB + backend CRUD). No changes to voice/phone logic. The hardest parts already work; this makes them *useful* beyond the demo.

2. **Unlocks ServiceNow integration as a natural follow-on**: Real ticketing systems expect sessions to persist. You can't sync ticket status updates if the session disappears when the browser closes. Persistence first, then ticketing — sequential value delivery.

3. **Supports "Reuse Across Campus" narrative from workshop runbook**: A department can't reuse a system that forgets conversations. Persistence is the prerequisite for cross-department trust.

---

## Suggested speckit.plan Kickoff Prompt

```
Plan a feature to add conversation persistence and history to the 47 Doors support agent. Students should be able to resume conversations across browser sessions, view their past conversation history (text + voice transcripts), and retrieve ticket IDs from previous sessions. Admins should have a dashboard showing active sessions, session duration metrics, and conversation counts per department. Use Azure Cosmos DB for storage (align with existing Azure-first stack). The existing in-memory session store should remain as a fallback for local development. Build on the session model established in 002-voice-interaction (session_id UUID is already the join key for text, browser voice, and phone transcripts). Target: enable multi-visit support journeys and unlock future ServiceNow ticket status sync.
```

---

## Full Analysis

See: `specs/roadmap/next-feature-recommendation-2026-04-21.md`

Includes:
- Current state snapshot (app capabilities, infrastructure, boundaries)
- Existing specs inventory
- 5 candidate features with complexity + dependency analysis
- Detailed rationale for recommendation
- Out-of-scope / deferred items with reasons
- Suggested implementation phases
