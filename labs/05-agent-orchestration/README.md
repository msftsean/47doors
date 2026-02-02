# Lab 05 - Agent Orchestration

**Duration:** 120 minutes (2 hours)
**Prerequisites:** Lab 04 completed

---

## Learning Objectives

By the end of this lab, you will be able to:

1. **Wire up a three-agent pipeline** - Connect QueryAgent, RouterAgent, and ActionAgent into a cohesive orchestration system
2. **Implement handoff protocols** - Define clear contracts for passing data between agents with proper error handling
3. **Add session context for multi-turn conversations** - Maintain conversation state across multiple user interactions

---

## Recap: The Three-Agent Pattern

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

### Pipeline Flow

```
UserQuery --> QueryAgent --> RouterAgent --> ActionAgent --> Response
    ^                                                            |
    |                                                            |
    +------------------- Session Context ------------------------+
```

### Agent Responsibilities Recap

| Agent | Input | Output | Responsibility |
|-------|-------|--------|----------------|
| **QueryAgent** | Raw user message + session context | Structured query with intent, entities | Parse, extract, normalize, enrich |
| **RouterAgent** | Structured query | Routing decision with selected agent | Classify intent, select action path |
| **ActionAgent** | Routing decision + parameters | Final user response | Execute task, generate response |

---

## Architecture Overview

In this lab, you will build the following components:

```
labs/05-agent-orchestration/
  start/
    query_agent.py         # QueryAgent implementation (skeleton)
    router_agent.py        # RouterAgent implementation (skeleton)
    action_agents.py       # ActionAgent implementations (skeleton)
    pipeline.py            # Orchestration pipeline (skeleton)
    session.py             # Session context management (skeleton)
    models.py              # Pydantic models for data contracts
    config.py              # Configuration settings
  solution/
    query_agent.py         # Complete QueryAgent
    router_agent.py        # Complete RouterAgent
    action_agents.py       # Complete ActionAgents
    pipeline.py            # Complete orchestration pipeline
    session.py             # Complete session management
    models.py              # Complete data models
    config.py              # Complete configuration
  tests/
    test_pipeline.py       # Pipeline integration tests
    test_session.py        # Session management tests
```

---

## Step-by-Step Instructions

### Step 1: Define Data Contracts

Before implementing agents, establish clear contracts for data flowing between them. Open `start/models.py`:

#### 1a: Query Model

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

#### 1b: Routing Decision Model

```python
class RoutingDecision(BaseModel):
    """Output from RouterAgent - which action to take."""
    target_agent: str = Field(..., description="Name of ActionAgent to invoke")
    parameters: dict = Field(default_factory=dict, description="Parameters for the agent")
    fallback_agent: Optional[str] = Field(None, description="Backup if primary fails")
    reasoning: str = Field(..., description="Why this routing was chosen")
```

#### 1c: Response Model

```python
class AgentResponse(BaseModel):
    """Output from ActionAgent - final response to user."""
    content: str = Field(..., description="Response text")
    sources: list[dict] = Field(default_factory=list, description="Citations if applicable")
    confidence: float = Field(..., ge=0.0, le=1.0)
    requires_followup: bool = Field(default=False)
    suggested_actions: list[str] = Field(default_factory=list)
```

**Task:** Complete the data models in `start/models.py`.

### Step 2: Implement Session Context

Session context maintains state across conversation turns. Open `start/session.py`:

#### 2a: Session Store

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
        """Record a conversation turn."""
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
        """Get recent conversation history for context."""
        recent = self.turns[-max_turns:] if len(self.turns) > max_turns else self.turns
        return [
            {"role": "user", "content": t.user_message}
            for t in recent
        ] + [
            {"role": "assistant", "content": t.agent_response}
            for t in recent
        ]

    def get_context_summary(self) -> str:
        """Generate a summary of conversation context."""
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

#### 2b: Session Manager

```python
class SessionManager:
    """Manages multiple concurrent sessions."""

    def __init__(self):
        self._sessions: dict[str, Session] = {}

    def get_or_create(self, session_id: Optional[str] = None) -> Session:
        """Get existing session or create new one."""
        if session_id and session_id in self._sessions:
            return self._sessions[session_id]

        session = Session(session_id=session_id) if session_id else Session()
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> Optional[Session]:
        """Get session by ID."""
        return self._sessions.get(session_id)

    def delete(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False
```

**Task:** Complete the session management in `start/session.py`.

### Step 3: Implement QueryAgent

The QueryAgent transforms raw user input into structured data. Open `start/query_agent.py`:

```python
from openai import AzureOpenAI
from models import StructuredQuery, Intent
from session import Session
import json

class QueryAgent:
    """
    Transforms raw user input into structured, actionable data.

    Responsibilities:
    - Parse natural language queries
    - Extract entities (names, dates, IDs, etc.)
    - Classify intent
    - Enrich with conversation context
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
1. Classify the user's intent into one of these categories:
   - knowledge_query: Questions about policies, procedures, how-to
   - password_reset: Requests to reset password or account access
   - ticket_status: Checking status of existing support tickets
   - general_chat: Casual conversation, greetings
   - escalation: User is frustrated, asking for human, or issue is complex
   - unknown: Cannot determine intent

2. Extract relevant entities:
   - ticket_id: If mentioned (e.g., "TKT-12345")
   - user_name: If the user identifies themselves
   - topic: Main subject of the query
   - urgency: low, medium, high based on language

3. Determine if clarification is needed

Respond with JSON only:
{
    "intent": "<intent>",
    "confidence": <0.0-1.0>,
    "entities": { ... },
    "requires_clarification": <bool>,
    "clarification_question": "<question if needed>"
}"""

        # Include conversation context
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

**Task:** Complete the QueryAgent in `start/query_agent.py`.

### Step 4: Implement RouterAgent

The RouterAgent decides which ActionAgent should handle the query. Open `start/router_agent.py`:

```python
from openai import AzureOpenAI
from models import StructuredQuery, RoutingDecision, Intent

class RouterAgent:
    """
    Determines the best action path for a given query.

    Responsibilities:
    - Map intents to ActionAgents
    - Apply business rules
    - Handle edge cases and fallbacks
    """

    # Routing table: intent -> (primary_agent, fallback_agent)
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
        # Handle clarification requests immediately
        if query.requires_clarification:
            return RoutingDecision(
                target_agent="clarification_agent",
                parameters={
                    "question": query.clarification_question,
                    "original_query": query.original_text
                },
                reasoning="Query requires clarification before proceeding"
            )

        # Low confidence? Ask for clarification
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

        # Look up routing
        primary, fallback = self.ROUTING_TABLE.get(
            query.intent,
            ("general_agent", None)
        )

        # Build parameters based on intent
        parameters = self._build_parameters(query)

        return RoutingDecision(
            target_agent=primary,
            parameters=parameters,
            fallback_agent=fallback,
            reasoning=f"Intent '{query.intent.value}' with confidence {query.confidence:.2f}"
        )

    def _build_parameters(self, query: StructuredQuery) -> dict:
        """Build agent-specific parameters from query."""
        params = {
            "query": query.original_text,
            "entities": query.entities
        }

        # Add intent-specific parameters
        if query.intent == Intent.TICKET_STATUS:
            params["ticket_id"] = query.entities.get("ticket_id")

        elif query.intent == Intent.KNOWLEDGE_QUERY:
            params["topic"] = query.entities.get("topic")
            params["search_query"] = query.original_text

        return params
```

**Task:** Complete the RouterAgent in `start/router_agent.py`.

### Step 5: Implement ActionAgents

ActionAgents execute specific tasks. Open `start/action_agents.py`:

```python
from abc import ABC, abstractmethod
from openai import AzureOpenAI
from models import RoutingDecision, AgentResponse
from session import Session

class BaseActionAgent(ABC):
    """Base class for all ActionAgents."""

    def __init__(self, openai_client: AzureOpenAI, model_deployment: str):
        self.client = openai_client
        self.model = model_deployment

    @abstractmethod
    async def execute(
        self,
        decision: RoutingDecision,
        session: Session
    ) -> AgentResponse:
        """Execute the agent's task."""
        pass


class RetrieveAgent(BaseActionAgent):
    """
    RAG agent that searches knowledge base and generates cited responses.
    Uses the hybrid_search from Lab 04.
    """

    def __init__(
        self,
        openai_client: AzureOpenAI,
        model_deployment: str,
        search_client,  # From Lab 04
    ):
        super().__init__(openai_client, model_deployment)
        self.search_client = search_client

    async def execute(
        self,
        decision: RoutingDecision,
        session: Session
    ) -> AgentResponse:
        """Search KB and generate response with citations."""
        query = decision.parameters.get("search_query", decision.parameters["query"])

        # Use hybrid search from Lab 04
        from search_tool import hybrid_search
        documents = await hybrid_search(
            query=query,
            search_client=self.search_client,
            openai_client=self.client,
            top_k=5
        )

        # Build context with citations
        context = self._build_context(documents)

        # Generate response
        response = await self._generate_response(query, context, session)

        return AgentResponse(
            content=response,
            sources=[{"id": d["id"], "title": d["title"]} for d in documents],
            confidence=0.85 if documents else 0.3,
            requires_followup=len(documents) == 0
        )

    def _build_context(self, documents: list[dict]) -> str:
        """Build context string with numbered citations."""
        if not documents:
            return "No relevant documents found."

        parts = []
        for i, doc in enumerate(documents, 1):
            parts.append(f"[{i}] {doc['title']}\n{doc['content']}")
        return "\n---\n".join(parts)

    async def _generate_response(
        self,
        query: str,
        context: str,
        session: Session
    ) -> str:
        """Generate cited response."""
        system_prompt = """You are a helpful assistant answering questions from a knowledge base.
Rules:
1. Only answer based on the provided context
2. Always cite sources using [1], [2], etc.
3. If context doesn't help, say you don't have that information
4. Be concise but complete"""

        history = session.get_history(max_turns=3)

        messages = [
            {"role": "system", "content": system_prompt},
            *history,
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
        ]

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3
        )

        return response.choices[0].message.content


class GeneralAgent(BaseActionAgent):
    """Handles general conversation and chitchat."""

    async def execute(
        self,
        decision: RoutingDecision,
        session: Session
    ) -> AgentResponse:
        """Generate conversational response."""
        system_prompt = """You are a friendly support assistant.
For general questions or chat:
- Be helpful and personable
- If they seem to need specific help, offer to assist
- Keep responses concise"""

        history = session.get_history(max_turns=3)
        query = decision.parameters.get("query", "")

        messages = [
            {"role": "system", "content": system_prompt},
            *history,
            {"role": "user", "content": query}
        ]

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7
        )

        return AgentResponse(
            content=response.choices[0].message.content,
            confidence=0.8,
            suggested_actions=["Ask a specific question", "Check ticket status"]
        )


class ClarificationAgent(BaseActionAgent):
    """Asks clarifying questions when intent is unclear."""

    async def execute(
        self,
        decision: RoutingDecision,
        session: Session
    ) -> AgentResponse:
        """Generate clarification request."""
        params = decision.parameters

        if "question" in params:
            # Specific clarification needed
            content = params["question"]
        else:
            # Generate clarification based on low confidence
            intent_guess = params.get("intent_guess", "unknown")
            content = f"I want to make sure I understand. Are you asking about {intent_guess.replace('_', ' ')}? Could you provide more details?"

        return AgentResponse(
            content=content,
            confidence=0.5,
            requires_followup=True
        )


class EscalationAgent(BaseActionAgent):
    """Handles escalation to human support."""

    async def execute(
        self,
        decision: RoutingDecision,
        session: Session
    ) -> AgentResponse:
        """Initiate escalation process."""
        # In production, this would create a ticket and notify humans
        content = """I understand you'd like to speak with a human agent.
I'm creating a support ticket for you now. A member of our team will reach out within 2 business hours.

In the meantime, is there anything else I can help with?"""

        return AgentResponse(
            content=content,
            confidence=1.0,
            suggested_actions=["Provide contact info", "Describe issue in detail"]
        )
```

**Task:** Complete the ActionAgents in `start/action_agents.py`. Add any additional agents needed for your use case.

### Step 6: Wire Up the Pipeline

Now connect all agents in the orchestration pipeline. Open `start/pipeline.py`:

```python
from openai import AzureOpenAI
from query_agent import QueryAgent
from router_agent import RouterAgent
from action_agents import (
    BaseActionAgent,
    RetrieveAgent,
    GeneralAgent,
    ClarificationAgent,
    EscalationAgent
)
from session import Session, SessionManager
from models import AgentResponse
import logging

logger = logging.getLogger(__name__)


class AgentPipeline:
    """
    Orchestrates the three-agent pipeline.

    Flow: UserQuery --> QueryAgent --> RouterAgent --> ActionAgent --> Response
    """

    def __init__(
        self,
        openai_client: AzureOpenAI,
        model_deployment: str,
        search_client=None,  # For RAG
    ):
        self.session_manager = SessionManager()

        # Initialize agents
        self.query_agent = QueryAgent(openai_client, model_deployment)
        self.router_agent = RouterAgent(openai_client, model_deployment)

        # Initialize action agents
        self.action_agents: dict[str, BaseActionAgent] = {
            "retrieve_agent": RetrieveAgent(
                openai_client, model_deployment, search_client
            ),
            "general_agent": GeneralAgent(openai_client, model_deployment),
            "clarification_agent": ClarificationAgent(openai_client, model_deployment),
            "escalation_agent": EscalationAgent(openai_client, model_deployment),
        }

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
        # Get or create session
        session = self.session_manager.get_or_create(session_id)
        logger.info(f"Processing message in session {session.session_id}")

        try:
            # Stage 1: QueryAgent - Understand the query
            logger.debug("Stage 1: QueryAgent")
            structured_query = await self.query_agent.process(user_message, session)
            logger.info(f"Intent: {structured_query.intent}, Confidence: {structured_query.confidence}")

            # Stage 2: RouterAgent - Decide where to route
            logger.debug("Stage 2: RouterAgent")
            routing_decision = await self.router_agent.route(structured_query)
            logger.info(f"Routing to: {routing_decision.target_agent}")

            # Stage 3: ActionAgent - Execute and respond
            logger.debug(f"Stage 3: ActionAgent ({routing_decision.target_agent})")
            response = await self._execute_action(routing_decision, session)

            # Record turn in session
            session.add_turn(
                user_message=user_message,
                agent_response=response.content,
                intent=structured_query.intent.value,
                entities=structured_query.entities
            )

            return response, session.session_id

        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            # Return graceful error response
            return AgentResponse(
                content="I apologize, but I encountered an issue processing your request. Please try again.",
                confidence=0.0,
                requires_followup=True
            ), session.session_id

    async def _execute_action(
        self,
        decision,
        session: Session
    ) -> AgentResponse:
        """Execute the selected ActionAgent with fallback."""
        agent = self.action_agents.get(decision.target_agent)

        if not agent:
            logger.warning(f"Unknown agent: {decision.target_agent}")
            agent = self.action_agents["general_agent"]

        try:
            return await agent.execute(decision, session)
        except Exception as e:
            logger.error(f"Agent {decision.target_agent} failed: {e}")

            # Try fallback if available
            if decision.fallback_agent:
                fallback = self.action_agents.get(decision.fallback_agent)
                if fallback:
                    logger.info(f"Falling back to {decision.fallback_agent}")
                    return await fallback.execute(decision, session)

            raise
```

**Task:** Complete the pipeline orchestration in `start/pipeline.py`.

### Step 7: Test Multi-Turn Conversations

Create a test script to verify the complete pipeline:

```python
# test_pipeline.py
import asyncio
from pipeline import AgentPipeline
from openai import AzureOpenAI

async def test_multi_turn():
    """Test multi-turn conversation flow."""
    # Initialize pipeline
    client = AzureOpenAI(...)  # Your configuration
    pipeline = AgentPipeline(client, "gpt-4o")

    # Conversation turns
    conversations = [
        # Turn 1: Greeting
        "Hi there!",
        # Turn 2: Knowledge query
        "How do I reset my password?",
        # Turn 3: Follow-up (should use context)
        "What if that doesn't work?",
        # Turn 4: Different topic
        "Can you check the status of my ticket TKT-12345?",
        # Turn 5: Escalation
        "I need to speak to a human please"
    ]

    session_id = None

    for turn_num, message in enumerate(conversations, 1):
        print(f"\n{'='*60}")
        print(f"Turn {turn_num}")
        print(f"User: {message}")
        print("-" * 60)

        response, session_id = await pipeline.process(message, session_id)

        print(f"Agent: {response.content}")
        print(f"Confidence: {response.confidence}")
        if response.sources:
            print(f"Sources: {[s['title'] for s in response.sources]}")

    print(f"\nSession ID: {session_id}")


async def test_context_retention():
    """Verify context is maintained across turns."""
    client = AzureOpenAI(...)
    pipeline = AgentPipeline(client, "gpt-4o")

    # First turn: Introduce context
    response1, session_id = await pipeline.process(
        "My name is Alice and I'm having trouble with my VPN"
    )

    # Second turn: Should remember name
    response2, _ = await pipeline.process(
        "Can you help me?",
        session_id
    )

    # Third turn: Should remember the VPN issue
    response3, _ = await pipeline.process(
        "Actually, never mind that - how do I submit expenses?",
        session_id
    )

    # Check session state
    session = pipeline.session_manager.get(session_id)
    assert len(session.turns) == 3, "Should have 3 turns recorded"
    assert "alice" in str(session.context).lower() or \
           any("alice" in str(t.entities).lower() for t in session.turns), \
           "Should have captured user name"


if __name__ == "__main__":
    asyncio.run(test_multi_turn())
```

Run your tests:

```bash
python test_pipeline.py
```

---

## Deliverables

By the end of this lab, you should have:

| Deliverable | Success Criteria |
|-------------|------------------|
| QueryAgent | Parses messages into structured queries with intent and entities |
| RouterAgent | Routes queries to correct ActionAgent based on intent |
| ActionAgent(s) | At least 3 working ActionAgents (Retrieve, General, Escalation) |
| Pipeline | Full orchestration working end-to-end |
| Session Management | Multi-turn conversations maintain context |
| Test Results | All test conversations complete successfully |

---

## Troubleshooting Tips

### Common Issues

**Issue:** Intent classification is inconsistent
- **Solution:** Lower temperature in QueryAgent (use 0.1 or lower)
- **Solution:** Add more explicit examples in the system prompt
- **Solution:** Use structured output format (JSON mode)

**Issue:** Router selects wrong ActionAgent
- **Solution:** Verify QueryAgent is extracting correct intent
- **Solution:** Check routing table mappings
- **Solution:** Add logging to trace the decision path

**Issue:** Context lost between turns
- **Solution:** Verify session_id is being passed correctly
- **Solution:** Check that session.add_turn() is called after each response
- **Solution:** Ensure history is included in agent prompts

**Issue:** ActionAgent throws exception
- **Solution:** Verify fallback agent is configured
- **Solution:** Add try/catch in execute methods
- **Solution:** Check that all required parameters are passed

**Issue:** Responses don't reference previous conversation
- **Solution:** Increase max_turns in get_history()
- **Solution:** Include context_summary in prompts
- **Solution:** Verify conversation history format is correct

### Debugging Checklist

1. [ ] All data models (StructuredQuery, RoutingDecision, AgentResponse) are valid
2. [ ] QueryAgent returns valid Intent enum values
3. [ ] RouterAgent routing table covers all intents
4. [ ] All ActionAgents are registered in the pipeline
5. [ ] Session ID is consistent across turns
6. [ ] Logging is enabled to trace pipeline flow
7. [ ] Error handling returns graceful responses

### Enabling Debug Logging

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Getting Help

- Review the solution files for reference implementations
- Check Lab 01 for three-agent pattern concepts
- Review Lab 04 for RetrieveAgent implementation
- Reach out to your instructor or lab assistant

---

## Additional Resources

- [Azure OpenAI Structured Outputs](https://learn.microsoft.com/azure/ai-services/openai/how-to/structured-outputs)
- [Pydantic Model Validation](https://docs.pydantic.dev/latest/)
- [Python Async/Await Patterns](https://docs.python.org/3/library/asyncio.html)
- [Agent Orchestration Patterns](https://learn.microsoft.com/azure/architecture/ai-ml/architecture/baseline-openai-e2e-chat)

---

## Next Steps

Once your pipeline handles multi-turn conversations correctly, proceed to:

**[Lab 06 - Deploy with azd](../06-deploy-with-azd/README.md)**

In the next lab, you will containerize your agent system and deploy it to Azure using the Azure Developer CLI.
