# 47 Doors Hackathon Facilitation Guide

This guide provides facilitators with a structured approach to leading the 47 Doors AI Agent hackathon curriculum. The 8-hour format balances hands-on learning with sufficient pacing to accommodate diverse skill levels.

---

## Room Setup Checklist

Complete these items **before participants arrive**:

### Physical Environment
- [ ] Projector/screen tested and working
- [ ] Whiteboard markers available (at least 3 colors)
- [ ] Power strips at each table cluster
- [ ] Seating arranged in pairs or small groups (3-4 per table)
- [ ] Facilitator station near power and screen access
- [ ] Water/refreshments station identified

### Technical Environment
- [ ] Wi-Fi credentials posted visibly
- [ ] Test internet connectivity from multiple locations in room
- [ ] Azure subscription access verified for all participants
- [ ] GitHub Codespaces quota confirmed (if using cloud dev)
- [ ] Backup hotspot available for connectivity issues
- [ ] Shared screen/demo machine ready with all labs pre-loaded

### Materials
- [ ] Printed quick-reference cards (optional but helpful)
- [ ] Sticky notes for "parking lot" questions
- [ ] Name tags or table tents
- [ ] Feedback forms ready (digital or paper)

### Pre-Flight Verification
- [ ] Run through Lab 00 setup on a fresh account
- [ ] Verify Azure OpenAI endpoints are responding
- [ ] Confirm Azure AI Search index is accessible
- [ ] Test `azd` deployment flow end-to-end

---

## 8-Hour Timeline

### 8:00 - 8:30 | Welcome & Lab 00: Environment Setup (30 min)

**Objectives:**
- Establish psychological safety and excitement
- Verify all participants have working development environments
- Set expectations for the day

**Facilitator Actions:**
| Time | Activity |
|------|----------|
| 8:00-8:10 | Welcome, introductions, day overview |
| 8:10-8:15 | Distribute credentials, explain support channels |
| 8:15-8:28 | Participants complete Lab 00 setup |
| 8:28-8:30 | Quick poll: thumbs up/down on environment status |

**Pacing Markers:**
- By 8:20 (midpoint): 70% should have VS Code/Codespace open
- By 8:25: 90% should have Python environment activated
- By 8:30: 100% should show successful test run or be paired with someone who has

**If Behind:**
- Pair struggling participants with those who finished early
- Have facilitator circulate to troubleshoot top 3 issues
- Extend by 5 min max; cut intro content, not setup time

**Key Checkpoints:**
- [ ] Can run `python --version` (3.11+)
- [ ] Can run `pytest` with no errors
- [ ] Azure credentials loaded (environment variables set)

---

### 8:30 - 10:00 | Lab 01: Understanding Agents (90 min)

**Objectives:**
- Build mental model of AI agents vs. simple LLM calls
- Understand tool-use patterns
- Execute first working agent interaction

**Facilitator Actions:**
| Time | Activity |
|------|----------|
| 8:30-8:40 | Present agent concepts (slides/whiteboard) |
| 8:40-9:00 | Participants read through lab introduction |
| 9:00-9:45 | Hands-on: Build first agent with tool |
| 9:45-9:55 | Group discussion: What did your agent do? |
| 9:55-10:00 | Transition + stretch break |

**Pacing Markers:**
- By 9:15 (midpoint of hands-on): 50% should have basic agent responding
- By 9:30: 75% should have tool-use working
- By 9:45: 90% should have completed core exercises

**If Behind:**
- At 9:15, if <40% have agents responding: do live coding demo
- At 9:30, if <60% have tool-use: provide solution snippet for struggling pairs
- Skip extension exercises; focus on core loop

**Key Checkpoints:**
- [ ] Agent can respond to user prompt
- [ ] Agent calls at least one tool successfully
- [ ] Participant can explain agent loop in their own words

**Intervention Points:**
- Common confusion: Agent vs. prompt engineering. Clarify the loop.
- Watch for: Participants stuck on API key errors (revisit Lab 00)
- Red flag: Anyone frustrated for >5 min without progress

---

### 10:00 - 10:30 | Lab 02: Azure MCP Setup (30 min)

**Objectives:**
- Configure Model Context Protocol connection to Azure
- Verify Azure OpenAI and Azure AI Search connectivity
- Understand enterprise security context

**Facilitator Actions:**
| Time | Activity |
|------|----------|
| 10:00-10:05 | Brief intro to MCP and Azure integration |
| 10:05-10:25 | Participants configure connections |
| 10:25-10:30 | Verify all connections; troubleshoot stragglers |

**Pacing Markers:**
- By 10:15 (midpoint): 60% should have Azure OpenAI connection verified
- By 10:25: 85% should have both OpenAI and Search connected
- By 10:30: 100% should be ready (or have noted issue for later)

**If Behind:**
- This lab is configuration-heavy; expect variance
- Have backup credentials ready for authentication issues
- If >30% struggling at 10:20, do group walkthrough on projector

**Key Checkpoints:**
- [ ] Azure OpenAI endpoint responds
- [ ] Azure AI Search returns sample query
- [ ] MCP configuration file is valid JSON

**Intervention Points:**
- Most common issue: Azure subscription permissions
- Watch for: Expired tokens or wrong region endpoints
- Escalate: Any persistent 403/401 errors to Azure admin immediately

---

### 10:30 - 11:15 | Lab 03: Spec-Driven Development (45 min)

**Objectives:**
- Learn to write specifications before code
- Practice prompt engineering for code generation
- Experience AI-assisted development workflow

**Facilitator Actions:**
| Time | Activity |
|------|----------|
| 10:30-10:40 | Introduce spec-driven methodology |
| 10:40-11:00 | Participants write spec for RAG component |
| 11:00-11:10 | Generate code from spec using AI tools |
| 11:10-11:15 | Share examples; discuss spec quality |

**Pacing Markers:**
- By 10:50 (midpoint): 50% should have draft spec written
- By 11:00: 80% should have spec ready for code generation
- By 11:10: 70% should have generated initial code

**If Behind:**
- Provide spec template at 10:50 for those struggling
- Focus on one strong spec rather than multiple weak ones
- Code generation can be demoed if time is tight

**Key Checkpoints:**
- [ ] Spec includes clear inputs, outputs, and behavior description
- [ ] Generated code matches spec intent (even if imperfect)
- [ ] Participant can iterate on spec to improve output

**Intervention Points:**
- Common mistake: Specs too vague ("make it good")
- Watch for: Over-engineering specs (analysis paralysis)
- Guide toward: Specific, testable requirements

---

### 11:15 - 11:30 | Break (15 min)

**Facilitator Actions:**
- Encourage participants to step away from screens
- Be available for 1:1 questions
- Assess energy level; adjust afternoon pacing if needed
- Update parking lot with any deferred questions

---

### 11:30 - 13:30 | Lab 04: Build RAG Pipeline (120 min)

**Objectives:**
- Implement complete Retrieval-Augmented Generation pipeline
- Connect vector search to language model
- Handle document chunking and embedding

**This is the longest and most complex lab.** Plan for multiple check-ins.

**Facilitator Actions:**
| Time | Activity |
|------|----------|
| 11:30-11:40 | RAG architecture overview (visual diagram) |
| 11:40-12:00 | Part A: Document ingestion and chunking |
| 12:00-12:20 | Part B: Embedding generation |
| 12:20-12:45 | Part C: Vector search integration |
| 12:45-13:00 | Part D: Response generation with context |
| 13:00-13:20 | End-to-end testing and debugging |
| 13:20-13:30 | Demo working pipelines; celebrate wins |

**Pacing Markers:**

| Checkpoint | Time | Expected Completion |
|------------|------|---------------------|
| Part A complete | 12:00 | 70% |
| Part B complete | 12:20 | 60% |
| Part C complete | 12:45 | 50% |
| Part D complete | 13:00 | 45% |
| Working pipeline | 13:20 | 60% |

**Note:** This lab has natural variance. Focus on understanding over completion.

**If Behind:**
- At 12:00, if <50% have chunking working: provide chunking function
- At 12:30, if <40% have embeddings: do live coding of embedding call
- At 13:00, if <30% have search working: switch to guided group exercise
- Always preserve 10 min at end for demos regardless of completion

**Key Checkpoints:**
- [ ] Documents can be chunked into appropriate sizes
- [ ] Embeddings are generated and stored
- [ ] Search query returns relevant chunks
- [ ] LLM generates response using retrieved context

**Intervention Points:**
- Biggest challenge: Debugging embedding dimension mismatches
- Watch for: Participants skipping validation steps
- Red flag: Anyone stuck on same error for >10 min
- Success signal: "Aha!" moments when search returns relevant content

---

### 13:30 - 14:00 | Lunch (30 min)

**Facilitator Actions:**
- Take a real break yourself
- Have informal conversations about morning learnings
- Don't troubleshoot during lunch (unless critical blocker)
- Reset room for afternoon if needed

---

### 14:00 - 16:00 | Lab 05: Agent Orchestration (120 min)

**Objectives:**
- Coordinate multiple agents/tools
- Implement planning and execution patterns
- Handle agent communication and handoffs

**Facilitator Actions:**
| Time | Activity |
|------|----------|
| 14:00-14:15 | Orchestration patterns overview |
| 14:15-14:45 | Part A: Multi-tool agent setup |
| 14:45-15:15 | Part B: Planning agent implementation |
| 15:15-15:45 | Part C: Agent communication patterns |
| 15:45-16:00 | Integration testing and debugging |

**Pacing Markers:**

| Checkpoint | Time | Expected Completion |
|------------|------|---------------------|
| Multi-tool working | 14:45 | 65% |
| Planning agent | 15:15 | 55% |
| Communication working | 15:45 | 50% |
| Full integration | 16:00 | 45% |

**If Behind:**
- At 14:45, if <50% have multi-tool: simplify to 2 tools only
- At 15:15, if <40% have planning: provide planning prompt template
- At 15:30, if significantly behind: convert Part C to live demo
- Ensure everyone has at least multi-tool working before moving on

**Key Checkpoints:**
- [ ] Agent can select appropriate tool for task
- [ ] Planning agent decomposes complex request
- [ ] Agents can pass context to each other
- [ ] System handles tool failures gracefully

**Intervention Points:**
- Common issue: Agents in infinite loops
- Watch for: Over-complicated orchestration logic
- Guide toward: Simple, debuggable patterns first
- Post-lunch energy dip: Consider 5-min energizer at 15:00

---

### 16:00 - 17:30 | Lab 06: Deploy with azd (90 min)

**Objectives:**
- Package application for Azure deployment
- Use Azure Developer CLI for infrastructure provisioning
- Deploy working agent to cloud

**Facilitator Actions:**
| Time | Activity |
|------|----------|
| 16:00-16:10 | Deployment architecture and azd overview |
| 16:10-16:30 | Configure azd environment and templates |
| 16:30-17:00 | Run `azd up` and handle provisioning |
| 17:00-17:20 | Test deployed application |
| 17:20-17:30 | Troubleshoot failures; document deployed URLs |

**Pacing Markers:**

| Checkpoint | Time | Expected Completion |
|------------|------|---------------------|
| azd configured | 16:30 | 80% |
| Provisioning started | 17:00 | 70% |
| Deployment complete | 17:20 | 55% |
| Tested in cloud | 17:30 | 50% |

**Note:** Deployment has high variance due to Azure subscription limits and quotas.

**If Behind:**
- At 16:30, if <60% configured: distribute pre-made azd config
- At 17:00, if many waiting on provisioning: show what successful deployment looks like
- If quota errors: have backup resource group or demo deployed instance
- Celebrate ANY successful deployment loudly

**Key Checkpoints:**
- [ ] `azd env` shows correct configuration
- [ ] `azd provision` completes without errors
- [ ] `azd deploy` pushes application code
- [ ] Deployed endpoint responds to requests

**Intervention Points:**
- Most common issue: Azure quota exceeded
- Watch for: Wrong region selection causing capacity errors
- Red flag: Subscription spending limits about to be hit
- Have Plan B: Demo from facilitator's pre-deployed instance

---

### 17:30 - 18:00 | Wrap-up & Lab 07 Intro (30 min)

**Objectives:**
- Celebrate accomplishments
- Preview stretch content for continued learning
- Gather feedback

**Facilitator Actions:**
| Time | Activity |
|------|----------|
| 17:30-17:40 | Group share-out: biggest learning, proudest moment |
| 17:40-17:50 | Lab 07 (stretch) introduction and resources |
| 17:50-17:55 | Distribute/complete feedback forms |
| 17:55-18:00 | Final Q&A, thank you, next steps |

**No pacing markers needed** - this is flexible closing time.

**Key Checkpoints:**
- [ ] Every participant can articulate one thing they learned
- [ ] Stretch content links shared
- [ ] Feedback collected from >80% of participants
- [ ] Participants know how to continue learning

---

## Intervention Decision Framework

Use this framework to decide when to intervene:

### Green Zone - Productive Struggle
- Participant is engaged and making attempts
- Error messages are being read and researched
- Questions are specific and show understanding
- **Action:** Observe, encourage, let them work through it

### Yellow Zone - Consider Intervening
- Same error for 5+ minutes without progress
- Visible frustration or disengagement
- Asking very broad questions ("Why doesn't it work?")
- **Action:** Check in with open question, offer hint, pair with peer

### Red Zone - Immediate Intervention
- Technical blocker affecting multiple participants
- Participant visibly upset or shutting down
- Error that cannot be resolved without facilitator help
- 10+ minutes stuck on same issue
- **Action:** Direct assistance, provide solution, or note for post-session

### Intervention Techniques

1. **The Drive-By Check:** "How's it going? What are you working on?"
2. **The Rubber Duck:** "Talk me through what you've tried"
3. **The Breadcrumb:** "Have you looked at line 42?" (don't give answer)
4. **The Pair-Up:** "Alex just solved something similar - Alex, can you share?"
5. **The Reset:** "Let's close everything and start fresh from checkpoint X"
6. **The Demo:** "Watch me do this one, then you'll try the next"

---

## Contingency Plans

### If 30+ minutes behind schedule:
- Skip extension exercises in current and remaining labs
- Convert hands-on to live coding with participation
- Compress breaks (minimum 5 min for each scheduled break)
- Lab 07 becomes take-home only

### If Azure services have outage:
- Switch to local development mode (mock endpoints)
- Use cached responses for demo purposes
- Focus on code structure and patterns over working API calls
- Document issue for post-hackathon support

### If significant portion (>30%) struggling:
- Pause for group teaching moment
- Create impromptu help tables (those ahead help those behind)
- Simplify remaining exercises
- Ensure everyone completes core path even if reduced scope

### If running ahead:
- Allow more exploration time
- Add extension exercises
- Deeper Q&A sessions
- Start Lab 07 in-session

---

## Facilitator Self-Care

- Take breaks when participants take breaks
- Stay hydrated
- Don't absorb participant frustration
- Celebrate small wins (yours and theirs)
- It's okay if not everyone finishes everything

---

## Post-Event Checklist

- [ ] Collect all feedback forms
- [ ] Note any Azure resources that need cleanup
- [ ] Document common issues for curriculum improvement
- [ ] Send follow-up email with resources and Lab 07 materials
- [ ] Thank yourself for facilitating!
