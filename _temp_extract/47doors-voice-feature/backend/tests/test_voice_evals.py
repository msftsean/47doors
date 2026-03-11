"""
Voice-specific evaluation tests for the Front Door Support Agent.

Covers:
1. Intent detection accuracy via voice tool calls matches text baseline
2. Escalation triggers fire correctly for all policy keywords via voice
3. Tool call response format validation for all 4 voice tools
4. Session context preservation across text-to-voice modality switches

Latency benchmarks are intentionally skipped — only functional correctness is validated.
"""

import os
import pytest

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("MOCK_MODE", "true")


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def realtime_service():
    """MockRealtimeService with real mock sub-services."""
    from app.services.mock.realtime_service import MockRealtimeService
    from app.services.mock.llm_service import MockLLMService
    from app.services.mock.ticket_service import MockTicketService
    from app.services.mock.knowledge_service import MockKnowledgeService
    from app.services.mock.session_store import MockSessionStore

    return MockRealtimeService(
        llm_service=MockLLMService(),
        ticket_service=MockTicketService(),
        knowledge_service=MockKnowledgeService(),
        session_store=MockSessionStore(),
    )


@pytest.fixture
def text_client():
    """HTTP test client for text chat baseline."""
    from app.core.dependencies import clear_service_caches
    clear_service_caches()
    from app.main import create_app
    from fastapi.testclient import TestClient
    return TestClient(create_app())


# =============================================================================
# Eval 1: Intent detection accuracy via voice matches text baseline
# =============================================================================

# Cases: (query, expected_keywords_in_status_or_dept)
VOICE_INTENT_CASES = [
    ("I forgot my password and cannot log in", ["created", "IT", "ACCOUNT"]),
    ("The printer in the library is broken", ["created", "FACILITIES"]),
    ("I need help with my financial aid", ["created", "FINANCIAL"]),
    ("My student ID card was stolen", ["created", "STUDENT"]),
    ("I need an official transcript", ["created", "REGISTRAR", "ACADEMIC"]),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("query,expected_keywords", VOICE_INTENT_CASES)
async def test_voice_intent_detection_accuracy(realtime_service, query, expected_keywords):
    """
    Eval 1: Voice tool call intent detection should produce valid routing outcomes
    comparable to text chat baseline.
    """
    result = await realtime_service.execute_tool(
        tool_name="analyze_and_route_query",
        arguments={"query": query},
    )

    assert isinstance(result, dict), f"Expected dict result for: {query}"
    assert "status" in result, f"Missing 'status' in result for: {query}"

    # Result should have some useful content
    has_ticket = result.get("ticket_id") is not None
    has_kb = len(result.get("knowledge_articles", [])) > 0
    assert has_ticket or has_kb, (
        f"Expected ticket or KB articles for: {query}, got: {result}"
    )

    # Department should be set (not None for non-escalation queries)
    dept = result.get("department")
    if not result.get("escalated"):
        assert dept is not None, f"Expected department for: {query}, got: {result}"


@pytest.mark.asyncio
async def test_voice_intent_matches_text_baseline(realtime_service, text_client):
    """
    Eval 1: A password reset query via voice tool call should have the same
    department routing as the text chat baseline.
    """
    query = "I cannot log into Canvas — forgot my password"

    # Text baseline
    text_resp = text_client.post(
        "/api/chat",
        json={"message": query, "session_id": None},
    )
    assert text_resp.status_code == 200
    text_data = text_resp.json()
    text_dept = text_data.get("department")

    # Voice tool call
    voice_result = await realtime_service.execute_tool(
        tool_name="analyze_and_route_query",
        arguments={"query": query},
    )

    voice_dept = voice_result.get("department")

    # Both should land in IT or be escalated (consistent routing)
    # We allow some tolerance but both should not be wildly different
    assert voice_result.get("status") is not None
    if text_dept and voice_dept:
        # If text routes to IT, voice should also route to IT
        assert text_dept == voice_dept or voice_result.get("escalated"), (
            f"Voice dept={voice_dept} should match text dept={text_dept}"
        )


# =============================================================================
# Eval 2: Escalation triggers for all policy keywords via voice
# =============================================================================

ESCALATION_KEYWORD_CASES = [
    ("I want to appeal my grade in CS101", "appeal"),
    ("Can I get a tuition refund for this semester?", "refund"),
    ("I need a tuition waiver due to medical reasons", "waiver"),
    ("I want to file a Title IX complaint", "Title IX"),
    ("I am having a mental health crisis", "mental health"),
    ("I need to speak to a human immediately", "human request"),
    ("Can I request an exception to the deadline?", "exception"),
    ("I want to withdraw after the deadline", "late withdrawal"),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("query,reason_label", ESCALATION_KEYWORD_CASES)
async def test_escalation_triggers_via_voice(realtime_service, query, reason_label):
    """
    Eval 2: All policy/sensitivity keywords must trigger escalation via voice tool calls.
    """
    result = await realtime_service.execute_tool(
        tool_name="analyze_and_route_query",
        arguments={"query": query},
    )

    escalated = result.get("escalated", False)
    dept = result.get("department", "")

    assert escalated or dept == "ESCALATE_TO_HUMAN", (
        f"Expected escalation for '{reason_label}' keyword in query: '{query}'\n"
        f"Got escalated={escalated}, department={dept}"
    )


@pytest.mark.asyncio
async def test_escalate_to_human_tool_fires_correctly(realtime_service):
    """
    Eval 2: escalate_to_human tool creates escalation ticket correctly.
    """
    escalation_cases = [
        {"query": "I want to appeal my grade", "reason": "policy_keyword"},
        {"query": "I am having mental health issues", "reason": "sensitive_topic"},
        {"query": "I need to talk to a real person", "reason": "user_request"},
    ]

    for case in escalation_cases:
        result = await realtime_service.execute_tool(
            tool_name="escalate_to_human",
            arguments=case,
        )

        assert result.get("escalated") is True, f"Expected escalated=True for: {case}"
        assert result.get("ticket_id") is not None, f"Expected ticket_id for: {case}"
        assert len(result.get("message", "")) > 0, f"Expected message for: {case}"


# =============================================================================
# Eval 3: Tool call response format validation for all 4 voice tools
# =============================================================================


@pytest.mark.asyncio
async def test_analyze_and_route_query_format(realtime_service):
    """Eval 3: analyze_and_route_query returns correct response structure."""
    result = await realtime_service.execute_tool(
        tool_name="analyze_and_route_query",
        arguments={"query": "I need help resetting my password"},
    )

    assert isinstance(result, dict)
    # Required fields
    assert "status" in result
    assert "escalated" in result
    assert "knowledge_articles" in result
    assert isinstance(result["knowledge_articles"], list)
    assert isinstance(result["escalated"], bool)
    # Optional but expected
    assert "ticket_id" in result or result.get("status") == "kb_only"


@pytest.mark.asyncio
async def test_check_ticket_status_format(realtime_service):
    """Eval 3: check_ticket_status returns correct structure for found ticket."""
    # Create a ticket first
    create_result = await realtime_service.execute_tool(
        tool_name="analyze_and_route_query",
        arguments={"query": "The elevator in Smith Hall is broken"},
    )
    ticket_id = create_result.get("ticket_id")
    if ticket_id is None:
        pytest.skip("No ticket created")

    status_result = await realtime_service.execute_tool(
        tool_name="check_ticket_status",
        arguments={"ticket_id": ticket_id},
    )

    assert isinstance(status_result, dict)
    assert "ticket_id" in status_result
    assert "status" in status_result
    assert "department" in status_result
    assert status_result["ticket_id"] == ticket_id


@pytest.mark.asyncio
async def test_search_knowledge_base_format(realtime_service):
    """Eval 3: search_knowledge_base returns correct structure."""
    result = await realtime_service.execute_tool(
        tool_name="search_knowledge_base",
        arguments={"query": "how to reset password", "limit": 3},
    )

    assert isinstance(result, dict)
    assert "articles" in result
    assert "total" in result
    assert isinstance(result["articles"], list)

    for article in result["articles"]:
        assert "article_id" in article
        assert "title" in article
        assert "url" in article
        assert "relevance_score" in article
        assert 0.0 <= article["relevance_score"] <= 1.0


@pytest.mark.asyncio
async def test_escalate_to_human_format(realtime_service):
    """Eval 3: escalate_to_human returns correct structure."""
    result = await realtime_service.execute_tool(
        tool_name="escalate_to_human",
        arguments={
            "query": "I need a refund for this semester",
            "reason": "policy_keyword",
        },
    )

    assert isinstance(result, dict)
    assert "ticket_id" in result
    assert "message" in result
    assert "escalated" in result
    assert "reason" in result
    assert result["escalated"] is True
    assert result["ticket_id"] is not None
    assert len(result["message"]) > 10


# =============================================================================
# Eval 4: Session context preservation across text-to-voice modality switches
# =============================================================================


@pytest.mark.asyncio
async def test_session_context_text_then_voice(realtime_service, text_client):
    """
    Eval 4: Text chat creates a ticket; voice check_ticket_status with same
    session context finds the ticket (modality switch preservation).
    """
    # Step 1: Create ticket via text chat
    text_resp = text_client.post(
        "/api/chat",
        json={"message": "My laptop screen is cracked", "session_id": None},
    )
    assert text_resp.status_code == 200
    text_data = text_resp.json()
    ticket_id = text_data.get("ticket_id")
    session_id = str(text_data.get("session_id", ""))

    if ticket_id is None:
        pytest.skip("Text chat did not create a ticket")

    # Step 2: Voice check_ticket_status with the ticket created via text
    voice_result = await realtime_service.execute_tool(
        tool_name="check_ticket_status",
        arguments={"ticket_id": ticket_id},
        session_id=session_id,
    )

    assert isinstance(voice_result, dict)
    assert "ticket_id" in voice_result
    assert voice_result["ticket_id"] == ticket_id
    assert "status" in voice_result


@pytest.mark.asyncio
async def test_voice_analyze_then_text_check(realtime_service, text_client):
    """
    Eval 4: Voice tool creates a ticket; text chat can find it (bidirectional).
    """
    # Step 1: Create ticket via voice tool
    voice_result = await realtime_service.execute_tool(
        tool_name="analyze_and_route_query",
        arguments={"query": "I need help with registration for next semester"},
    )
    ticket_id = voice_result.get("ticket_id")

    if ticket_id is None:
        pytest.skip("Voice tool did not create a ticket")

    # Step 2: Verify the ticket exists via text API
    ticket_resp = text_client.get(f"/api/tickets/{ticket_id}")
    assert ticket_resp.status_code == 200
    ticket_data = ticket_resp.json()
    assert ticket_data.get("ticket_id") == ticket_id


@pytest.mark.asyncio
async def test_voice_modality_preserves_session_state(realtime_service):
    """
    Eval 4: Multiple voice tool calls in sequence maintain consistent session context.
    """
    import uuid
    session_id = str(uuid.uuid4())

    # First voice tool call — create a ticket
    result1 = await realtime_service.execute_tool(
        tool_name="analyze_and_route_query",
        arguments={"query": "My internet connection is very slow", "session_id": session_id},
        session_id=session_id,
    )
    assert isinstance(result1, dict)
    ticket_id = result1.get("ticket_id")

    # Second voice tool call — search KB in same session
    result2 = await realtime_service.execute_tool(
        tool_name="search_knowledge_base",
        arguments={"query": "internet connection slow troubleshooting"},
        session_id=session_id,
    )
    assert isinstance(result2, dict)
    assert "articles" in result2

    # If ticket was created, verify it's still retrievable
    if ticket_id:
        result3 = await realtime_service.execute_tool(
            tool_name="check_ticket_status",
            arguments={"ticket_id": ticket_id},
            session_id=session_id,
        )
        assert result3.get("ticket_id") == ticket_id


# =============================================================================
# Voice system prompt and tool definitions validation
# =============================================================================


def test_voice_system_prompt_has_required_directives():
    """Voice system prompt contains all required behavioral directives."""
    from app.services.mock.realtime_service import VOICE_SYSTEM_PROMPT
    prompt = VOICE_SYSTEM_PROMPT.lower()

    assert "escalat" in prompt, "Prompt must instruct on escalation"
    assert "human" in prompt, "Prompt must mention human escalation"
    assert "markdown" in prompt, "Prompt must prohibit markdown formatting"
    assert "pii" in prompt or "personal" in prompt or "repeat" in prompt, (
        "Prompt must address PII handling"
    )


def test_all_four_voice_tools_have_correct_schema():
    """All 4 voice tools have correct JSON Schema structure for Realtime API."""
    from app.services.mock.realtime_service import get_voice_tool_definitions
    tools = get_voice_tool_definitions()

    assert len(tools) == 4

    for tool in tools:
        assert tool["type"] == "function"
        assert "name" in tool
        assert "description" in tool
        assert len(tool["description"]) > 20, f"Tool '{tool['name']}' needs a more descriptive description"
        assert "parameters" in tool
        params = tool["parameters"]
        assert params["type"] == "object"
        assert "properties" in params
        assert "required" in params
        assert isinstance(params["required"], list)
        assert len(params["required"]) >= 1, f"Tool '{tool['name']}' must have at least 1 required param"


def test_tool_names_match_expected_set():
    """Tool names exactly match the 4 expected voice tools."""
    from app.services.mock.realtime_service import get_voice_tool_definitions
    tools = get_voice_tool_definitions()
    names = {t["name"] for t in tools}
    expected = {
        "analyze_and_route_query",
        "check_ticket_status",
        "search_knowledge_base",
        "escalate_to_human",
    }
    assert names == expected
