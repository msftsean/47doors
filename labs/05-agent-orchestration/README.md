# 🔄 Lab 05 - Agent Orchestration

| 📋 Attribute | Value |
|-------------|-------|
| ⏱️ **Duration** | 120 minutes (2 hours) |
| 📊 **Difficulty** | ⭐⭐⭐ Advanced |
| 🎯 **Prerequisites** | Lab 04 completed |

---

## 📈 Progress Tracker

```
Lab Progress: [░░░░░░░░░░] 0% - Not Started

Checkpoints:
□ Step 1: Define Data Contracts
□ Step 2: Implement Session Context
□ Step 3: Implement QueryAgent
□ Step 4: Implement RouterAgent
□ Step 5: Implement ActionAgents
□ Step 6: Wire Up the Pipeline
□ Step 7: Test Multi-Turn Conversations
```

---

## 🎯 Learning Objectives

By the end of this lab, you will be able to:

1. 🔗 **Wire up a three-agent pipeline** - Connect QueryAgent, RouterAgent, and ActionAgent into a cohesive orchestration system
2. 🤝 **Implement handoff protocols** - Define clear contracts for passing data between agents with proper error handling
3. 💬 **Add session context for multi-turn conversations** - Maintain conversation state across multiple user interactions

---

## 🔁 Recap: The Three-Agent Pattern

In Lab 01, you learned about the three-agent architecture. Now you will implement it:

```
+------------------+     +------------------+     +------------------+
|   User Query     |     |   QueryAgent     |     |   RouterAgent    |
|   "How do I      | --> |  (Understand &   | --> |   (Classify &    |
|    reset pwd?"   |     |   Structure)     |     |    Dispatch)     |
+------------------+     +------------------+     +------------------+
                                                          |
                         +--------------------------------+
                         |
                         v
              +--------------------+
              |    ActionAgent     |
              |  (Execute & Reply) |
              +--------------------+
                         |
                         v
              +--------------------+
              |     Response       |
              |  "To reset your    |
              |   password..." [1] |
              +--------------------+
```

### 🔄 Pipeline Flow

```
UserQuery --> QueryAgent --> RouterAgent --> ActionAgent --> Response
    ^                                                            |
    |                                                            |
    +------------------- Session Context ------------------------+
```

### 👥 Agent Responsibilities Recap

| 🤖 Agent | 📥 Input | 📤 Output | 🎯 Responsibility |
|-------|-------|--------|----------------|
| 🔍 **QueryAgent** | Raw user message + session context | Structured query with intent, entities | Parse, extract, normalize, enrich |
| 🚦 **RouterAgent** | Structured query | Routing decision with selected agent | Classify intent, select action path |
| ⚡ **ActionAgent** | Routing decision + parameters | Final user response | Execute task, generate response |

---

## 🏗️ Architecture Overview

In this lab, you will build the following components:

```
labs/05-agent-orchestration/
  📁 start/
    📄 query_agent.py         # QueryAgent implementation (skeleton)
    📄 router_agent.py        # RouterAgent implementation (skeleton)
    📄 action_agents.py       # ActionAgent implementations (skeleton)
    📄 pipeline.py            # Orchestration pipeline (skeleton)
    📄 session.py             # Session context management (skeleton)
    📄 models.py              # Pydantic models for data contracts
    📄 config.py              # Configuration settings
  📁 solution/
    📄 query_agent.py         # Complete QueryAgent
    📄 router_agent.py        # Complete RouterAgent
    📄 action_agents.py       # Complete ActionAgents
    📄 pipeline.py            # Complete orchestration pipeline
    📄 session.py             # Complete session management
    📄 models.py              # Complete data models
    📄 config.py              # Complete configuration
  📁 tests/
    📄 test_pipeline.py       # Pipeline integration tests
    📄 test_session.py        # Session management tests
```

---

## 📝 Step-by-Step Instructions

### 🔹 Step 1: Define Data Contracts

Before implementing agents, establish clear contracts for data flowing between them. Open `start/models.py`:

#### 1a: 📋 Query Model

```python
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class Intent(str, Enum):
    """Supported intents for routing."""
    KNOWLEDGE_QUERY = "knowledge_query"
    PASSWORD_RESET = "password_reset"
    TICKET_STATUS = "ticket_status"
    GENERAL_CHAT = "general_chat"
    ESCALATION = "escalation"
    UNKNOWN = "unknown"

class StructuredQuery(BaseModel):
    """Output from QueryAgent - structured representation of user input."""
    original_text: str = Field(..., description="Original user message")
    intent: Intent = Field(..., description="Classified intent")
    entities: dict = Field(default_factory=dict, description="Extracted entities")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Classification confidence")
    requires_clarification: bool = Field(default=False)
    clarification_question: Optional[str] = None
```

#### 1b: 🚦 Routing Decision Model

```python
class RoutingDecision(BaseModel):
    """Output from RouterAgent - which action to take."""
    target_agent: str = Field(..., description="Name of ActionAgent to invoke")
    parameters: dict = Field(default_factory=dict, description="Parameters for the agent")
    fallback_agent: Optional[str] = Field(None, description="Backup if primary fails")
    reasoning: str = Field(..., description="Why this routing was chosen")
```

#### 1c: 💬 Response Model

```python
class AgentResponse(BaseModel):
    """Output from ActionAgent - final response to user."""
    content: str = Field(..., description="Response text")
    sources: list[dict] = Field(default_factory=list, description="Citations if applicable")
    confidence: float = Field(..., ge=0.0, le=1.0)
    requires_followup: bool = Field(default=False)
    suggested_actions: list[str] = Field(default_factory=list)
```

**Task:** Complete the data models in `start/models.py`. 📝

### 🔹 Step 2: Implement Session Context

Session context maintains state across conversation turns. Open `start/session.py`:

#### 2a: 💾 Session Store

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid

@dataclass
class ConversationTurn:
    """A single turn in the conversation."""
    turn_id: str
    timestamp: datetime
    user_message: str
    agent_response: str
    intent: str
    entities: dict

@dataclass
class Session:
    """Maintains conversation state across turns."""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)
    turns: list[ConversationTurn] = field(default_factory=list)
    context: dict = field(default_factory=dict)  # Arbitrary context storage

    def add_turn(
        self,
        user_message: str,
        agent_response: str,
        intent: str,
        entities: dict
    ) -> ConversationTurn:
        """📝 Record a conversation turn."""
        turn = ConversationTurn(
            turn_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            user_message=user_message,
            agent_response=agent_response,
            intent=intent,
            entities=entities
        )
        self.turns.append(turn)
        return turn

    def get_history(self, max_turns: int = 5) -> list[dict]:
        """📚 Get recent conversation history for context."""
        recent = self.turns[-max_turns:] if len(self.turns) > max_turns else self.turns
        return [
            {"role": "user", "content": t.user_message}
            for t in recent
        ] + [
            {"role": "assistant", "content": t.agent_response}
            for t in recent
        ]

    def get_context_summary(self) -> str:
        """📋 Generate a summary of conversation context."""
        if not self.turns:
            return "No previous conversation."

        recent_intents = [t.intent for t in self.turns[-3:]]
        all_entities = {}
        for t in self.turns:
            all_entities.update(t.entities)

        return f"""Previous topics: {', '.join(set(recent_intents))}
Known entities: {all_entities}
Turn count: {len(self.turns)}"""
```

#### 2b: 🗄️ Session Manager

```python
class SessionManager:
    """Manages multiple concurrent sessions."""

    def __init__(self):
        self._sessions: dict[str, Session] = {}

    def get_or_create(self, session_id: Optional[str] = None) -> Session:
        """🔍 Get existing session or create new one."""
        if session_id and session_id in self._sessions:
            return self._sessions[session_id]

        session = Session(session_id=session_id) if session_id else Session()
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> Optional[Session]:
        """🔍 Get session by ID."""
        return self._sessions.get(session_id)

    def delete(self, session_id: str) -> bool:
        """🗑️ Delete a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False
```

**Task:** Complete the session management in `start/session.py`. 📝

### 🔹 Step 3: Implement QueryAgent

The QueryAgent transforms raw user input into structured data. Open `start/query_agent.py`:

```python
from openai import AzureOpenAI
from models import StructuredQuery, Intent
from session import Session
import json

class QueryAgent:
    """
    🔍 Transforms raw user input into structured, actionable data.

    Responsibilities:
    - 📝 Parse natural language queries
    - 🏷️ Extract entities (names, dates, IDs, etc.)
    - 🎯 Classify intent
    - 📚 Enrich with conversation context
    """

    def __init__(self, openai_client: AzureOpenAI, model_deployment: str):
        self.client = openai_client
        self.model = model_deployment

    async def process(
        self,
        user_message: str,
        session: Session
    ) -> StructuredQuery:
        """
        Process user message into structured query.

        Args:
            user_message: Raw user input
            session: Current conversation session

        Returns:
            StructuredQuery with intent, entities, and metadata
        """
        system_prompt = """You are a query understanding agent. Your job is to:
1. 🎯 Classify the user's intent into one of these categories:
   - knowledge_query: Questions about policies, procedures, how-to
   - password_reset: Requests to reset password or account access
   - ticket_status: Checking status of existing support tickets
   - general_chat: Casual conversation, greetings
   - escalation: User is frustrated, asking for human, or issue is complex
   - unknown: Cannot determine intent

2. 🏷️ Extract relevant entities:
   - ticket_id: If mentioned (e.g., "TKT-12345")
   - user_name: If the user identifies themselves
   - topic: Main subject of the query
   - urgency: low, medium, high based on language

3. ❓ Determine if clarification is needed

Respond with JSON only:
{
    "intent": "<intent>",
    "confidence": <0.0-1.0>,
    "entities": { ... },
    "requires_clarification": <bool>,
    "clarification_question": "<question if needed>"
}"""

        # 📚 Include conversation context
        context_summary = session.get_context_summary()

        user_prompt = f"""Conversation context:
{context_summary}

Current message: {user_message}

Analyze this message and respond with JSON."""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)

        return StructuredQuery(
            original_text=user_message,
            intent=Intent(result["intent"]),
            entities=result.get("entities", {}),
            confidence=result["confidence"],
            requires_clarification=result.get("requires_clarification", False),
            clarification_question=result.get("clarification_question")
        )
```

**Task:** Complete the QueryAgent in `start/query_agent.py`. 📝

### 🔹 Step 4: Implement RouterAgent

The RouterAgent decides which ActionAgent should handle the query. Open `start/router_agent.py`:

```python
from openai import AzureOpenAI
from models import StructuredQuery, RoutingDecision, Intent

class RouterAgent:
    """
    🚦 Determines the best action path for a given query.

    Responsibilities:
    - 🗺️ Map intents to ActionAgents
    - 📋 Apply business rules
    - ⚠️ Handle edge cases and fallbacks
    """

    # 🗺️ Routing table: intent -> (primary_agent, fallback_agent)
    ROUTING_TABLE = {
        Intent.KNOWLEDGE_QUERY: ("retrieve_agent", "general_agent"),
        Intent.PASSWORD_RESET: ("password_agent", "escalation_agent"),
        Intent.TICKET_STATUS: ("ticket_agent", "general_agent"),
        Intent.GENERAL_CHAT: ("general_agent", None),
        Intent.ESCALATION: ("escalation_agent", None),
        Intent.UNKNOWN: ("clarification_agent", "general_agent"),
    }

    def __init__(self, openai_client: AzureOpenAI, model_deployment: str):
        self.client = openai_client
        self.model = model_deployment

    async def route(self, query: StructuredQuery) -> RoutingDecision:
        """
        Route the structured query to appropriate ActionAgent.

        Args:
            query: Structured query from QueryAgent

        Returns:
            RoutingDecision with target agent and parameters
        """
        # ❓ Handle clarification requests immediately
        if query.requires_clarification:
            return RoutingDecision(
                target_agent="clarification_agent",
                parameters={
                    "question": query.clarification_question,
                    "original_query": query.original_text
                },
                reasoning="Query requires clarification before proceeding"
            )

        # ⚠️ Low confidence? Ask for clarification
        if query.confidence < 0.6:
            return RoutingDecision(
                target_agent="clarification_agent",
                parameters={
                    "intent_guess": query.intent.value,
                    "confidence": query.confidence
                },
                fallback_agent="general_agent",
                reasoning=f"Low confidence ({query.confidence:.2f}) - requesting clarification"
            )

        # 🗺️ Look up routing
        primary, fallback = self.ROUTING_TABLE.get(
            query.intent,
            ("general_agent", None)
        )

        # 🔧 Build parameters based on intent
        parameters = self._build_parameters(query)

        return RoutingDecision(
            target_agent=primary,
            parameters=parameters,
            fallback_agent=fallback,
            reasoning=f"Intent '{query.intent.value}' with confidence {query.confidence:.2f}"
        )

    def _build_parameters(self, query: StructuredQuery) -> dict:
        """🔧 Build agent-specific parameters from query."""
        params = {
            "query": query.original_text,
            "entities": query.entities
        }

        # 🎯 Add intent-specific parameters
        if query.intent == Intent.TICKET_STATUS:
            params["ticket_id"] = query.entities.get("ticket_id")

        elif query.intent == Intent.KNOWLEDGE_QUERY:
            params["topic"] = query.entities.get("topic")
            params["search_query"] = query.original_text

        return params
```

**Task:** Complete the RouterAgent in `start/router_agent.py`. 📝

### 🔹 Step 5: Implement ActionAgents

ActionAgents execute specific tasks. Open `start/action_agents.py` and implement:

- 📚 **RetrieveAgent** - RAG-powered KB search
- 💬 **GeneralAgent** - Conversational responses
- ❓ **ClarificationAgent** - Ask clarifying questions
- 🚨 **EscalationAgent** - Escalate to humans

**Task:** Complete the ActionAgents in `start/action_agents.py`. 📝

### 🔹 Step 6: Wire Up the Pipeline

Connect all agents in the orchestration pipeline. Open `start/pipeline.py`:

```python
class AgentPipeline:
    """
    🔄 Orchestrates the three-agent pipeline.

    Flow: UserQuery --> QueryAgent --> RouterAgent --> ActionAgent --> Response
    """

    async def process(
        self,
        user_message: str,
        session_id: str = None
    ) -> tuple[AgentResponse, str]:
        """
        Process a user message through the full pipeline.

        Args:
            user_message: Raw user input
            session_id: Optional session ID for multi-turn

        Returns:
            Tuple of (AgentResponse, session_id)
        """
        # 💾 Get or create session
        session = self.session_manager.get_or_create(session_id)

        # 🔍 Stage 1: QueryAgent - Understand the query
        structured_query = await self.query_agent.process(user_message, session)

        # 🚦 Stage 2: RouterAgent - Decide where to route
        routing_decision = await self.router_agent.route(structured_query)

        # ⚡ Stage 3: ActionAgent - Execute and respond
        response = await self._execute_action(routing_decision, session)

        # 📝 Record turn in session
        session.add_turn(
            user_message=user_message,
            agent_response=response.content,
            intent=structured_query.intent.value,
            entities=structured_query.entities
        )

        return response, session.session_id
```

**Task:** Complete the pipeline orchestration in `start/pipeline.py`. 📝

### 🔹 Step 7: Test Multi-Turn Conversations

Create a test script to verify the complete pipeline handles multi-turn conversations:

```python
# test_pipeline.py
async def test_multi_turn():
    """🧪 Test multi-turn conversation flow."""
    pipeline = AgentPipeline(...)

    conversations = [
        "Hi there!",                                    # 👋 Greeting
        "How do I reset my password?",                  # 🔑 Knowledge query
        "What if that doesn't work?",                   # 🔄 Follow-up
        "Can you check the status of my ticket TKT-12345?",  # 🎫 Ticket status
        "I need to speak to a human please"             # 🚨 Escalation
    ]

    session_id = None
    for message in conversations:
        response, session_id = await pipeline.process(message, session_id)
        print(f"User: {message}")
        print(f"Agent: {response.content}\n")
```

Run your tests:

```bash
python test_pipeline.py
```

---

## ✅ Deliverables

By the end of this lab, you should have:

| 📋 Deliverable | ✅ Success Criteria |
|-------------|------------------|
| 🔍 QueryAgent | Parses messages into structured queries with intent and entities |
| 🚦 RouterAgent | Routes queries to correct ActionAgent based on intent |
| ⚡ ActionAgent(s) | At least 3 working ActionAgents (Retrieve, General, Escalation) |
| 🔄 Pipeline | Full orchestration working end-to-end |
| 💾 Session Management | Multi-turn conversations maintain context |
| 🧪 Test Results | All test conversations complete successfully |

---

## 🔧 Troubleshooting Tips

### ⚠️ Common Issues

**Issue:** Intent classification is inconsistent
- ✅ **Solution:** Lower temperature in QueryAgent (use 0.1 or lower)
- ✅ **Solution:** Add more explicit examples in the system prompt
- ✅ **Solution:** Use structured output format (JSON mode)

**Issue:** Router selects wrong ActionAgent
- ✅ **Solution:** Verify QueryAgent is extracting correct intent
- ✅ **Solution:** Check routing table mappings
- ✅ **Solution:** Add logging to trace the decision path

**Issue:** Context lost between turns
- ✅ **Solution:** Verify session_id is being passed correctly
- ✅ **Solution:** Check that session.add_turn() is called after each response
- ✅ **Solution:** Ensure history is included in agent prompts

### 📋 Debugging Checklist

1. [ ] 📄 All data models (StructuredQuery, RoutingDecision, AgentResponse) are valid
2. [ ] 🎯 QueryAgent returns valid Intent enum values
3. [ ] 🗺️ RouterAgent routing table covers all intents
4. [ ] 📦 All ActionAgents are registered in the pipeline
5. [ ] 🔑 Session ID is consistent across turns
6. [ ] 📝 Logging is enabled to trace pipeline flow
7. [ ] ⚠️ Error handling returns graceful responses

---

## 📚 Additional Resources

- 📖 [Azure OpenAI Structured Outputs](https://learn.microsoft.com/azure/ai-services/openai/how-to/structured-outputs)
- 🔧 [Pydantic Model Validation](https://docs.pydantic.dev/latest/)
- 🔄 [Python Async/Await Patterns](https://docs.python.org/3/library/asyncio.html)
- 🏗️ [Agent Orchestration Patterns](https://learn.microsoft.com/azure/architecture/ai-ml/architecture/baseline-openai-e2e-chat)

---

## ➡️ Next Steps

Once your pipeline handles multi-turn conversations correctly, proceed to:

**[Lab 06 - Deploy with azd](../06-deploy-with-azd/README.md)** 🚀

In the next lab, you will containerize your agent system and deploy it to Azure using the Azure Developer CLI.

---

## 📊 Version Matrix

| Component | Required Version | Tested Version |
|-----------|-----------------|----------------|
| 🐍 Python | 3.11+ | 3.11.9 |
| 🤖 Azure OpenAI | GPT-4o | 2024-02-15-preview |
| 🔧 Pydantic | 2.5+ | 2.6.1 |
| 🔄 asyncio | 3.11+ | Built-in |

---

<div align="center">

[← Lab 04](../04-build-rag-pipeline/README.md) | **Lab 05** | [Lab 06 →](../06-deploy-with-azd/README.md)

📅 Last Updated: 2026-02-04 | 📝 Version: 1.0.0

</div>
