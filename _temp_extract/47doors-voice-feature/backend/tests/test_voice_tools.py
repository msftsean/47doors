"""
Tests for voice tool handlers in MockRealtimeService.

Covers:
- T013: analyze_and_route_query invokes 3-agent pipeline
- T014: search_knowledge_base returns top 3 articles
- T023: escalate_to_human creates escalation ticket
- T024: policy keyword escalation via voice
- T029: session context preservation across modality switches
"""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("MOCK_MODE", "true")


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_realtime_service():
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


# =============================================================================
# T013: test_analyze_and_route_query_tool
# =============================================================================


@pytest.mark.asyncio
async def test_analyze_and_route_query_tool(mock_realtime_service) -> None:
    """
    T013: analyze_and_route_query tool invokes QueryAgent → RouterAgent →
    ActionAgent pipeline and returns ticket_id + KB articles.
    """
    result = await mock_realtime_service.execute_tool(
        tool_name="analyze_and_route_query",
        arguments={"query": "I forgot my password and cannot log in"},
    )

    # Must return a dict
    assert isinstance(result, dict)

    # Must have a ticket_id (or message if not created)
    assert "ticket_id" in result or "message" in result

    # Must have status
    assert "status" in result

    # Must have knowledge_articles list
    assert "knowledge_articles" in result
    assert isinstance(result["knowledge_articles"], list)

    # Must have escalated flag
    assert "escalated" in result


@pytest.mark.asyncio
async def test_analyze_and_route_query_creates_ticket(mock_realtime_service) -> None:
    """analyze_and_route_query creates a valid ticket ID."""
    result = await mock_realtime_service.execute_tool(
        tool_name="analyze_and_route_query",
        arguments={"query": "The printer in the library is broken"},
    )

    assert isinstance(result, dict)
    # Ticket ID should match pattern or be None for kb_only
    if result.get("ticket_id"):
        import re
        pattern = r"^TKT-[A-Z]{2,3}-\d{8}-\d{4}$"
        assert re.match(pattern, result["ticket_id"]), (
            f"Ticket ID format invalid: {result['ticket_id']}"
        )


@pytest.mark.asyncio
async def test_analyze_and_route_query_with_session_id(mock_realtime_service) -> None:
    """analyze_and_route_query accepts session_id parameter."""
    import uuid
    session_id = str(uuid.uuid4())

    result = await mock_realtime_service.execute_tool(
        tool_name="analyze_and_route_query",
        arguments={"query": "I need help with my registration", "session_id": session_id},
        session_id=session_id,
    )

    assert isinstance(result, dict)
    assert "status" in result


# =============================================================================
# T014: test_search_knowledge_base_tool
# =============================================================================


@pytest.mark.asyncio
async def test_search_knowledge_base_tool(mock_realtime_service) -> None:
    """
    T014: search_knowledge_base tool returns top 3 articles with correct fields.
    """
    result = await mock_realtime_service.execute_tool(
        tool_name="search_knowledge_base",
        arguments={"query": "password reset", "limit": 3},
    )

    assert isinstance(result, dict)
    assert "articles" in result
    articles = result["articles"]
    assert isinstance(articles, list)

    # Should return up to 3 articles
    assert len(articles) <= 3

    # Each article should have required fields
    for article in articles:
        assert "article_id" in article
        assert "title" in article
        assert "url" in article
        assert "relevance_score" in article
        assert 0.0 <= article["relevance_score"] <= 1.0


@pytest.mark.asyncio
async def test_search_knowledge_base_respects_limit(mock_realtime_service) -> None:
    """search_knowledge_base enforces limit of 3."""
    result = await mock_realtime_service.execute_tool(
        tool_name="search_knowledge_base",
        arguments={"query": "tuition fees financial aid", "limit": 10},
    )

    assert isinstance(result, dict)
    # Limit is capped at 3 in the service
    assert len(result["articles"]) <= 3
    assert "total" in result


# =============================================================================
# T023: test_escalate_to_human_tool
# =============================================================================


@pytest.mark.asyncio
async def test_escalate_to_human_tool(mock_realtime_service) -> None:
    """
    T023: escalate_to_human tool creates an escalation ticket and returns confirmation.
    """
    result = await mock_realtime_service.execute_tool(
        tool_name="escalate_to_human",
        arguments={
            "query": "I want to appeal my grade",
            "reason": "policy_keyword",
        },
    )

    assert isinstance(result, dict)

    # Must confirm escalation
    assert result.get("escalated") is True

    # Must have a ticket ID
    assert "ticket_id" in result
    assert result["ticket_id"] is not None

    # Must have a user-friendly message
    assert "message" in result
    assert len(result["message"]) > 0

    # Must preserve the reason
    assert "reason" in result


@pytest.mark.asyncio
async def test_escalate_to_human_sensitive_topic(mock_realtime_service) -> None:
    """escalate_to_human handles sensitive topic reason."""
    result = await mock_realtime_service.execute_tool(
        tool_name="escalate_to_human",
        arguments={
            "query": "I am having mental health issues",
            "reason": "sensitive_topic",
        },
    )

    assert result.get("escalated") is True
    assert result.get("ticket_id") is not None


@pytest.mark.asyncio
async def test_check_ticket_status_tool(mock_realtime_service) -> None:
    """check_ticket_status returns ticket info for a valid ticket."""
    # First create a ticket via analyze_and_route_query
    create_result = await mock_realtime_service.execute_tool(
        tool_name="analyze_and_route_query",
        arguments={"query": "My laptop screen is broken"},
    )

    ticket_id = create_result.get("ticket_id")
    if ticket_id is None:
        pytest.skip("No ticket created — kb_only response")

    # Now look it up
    status_result = await mock_realtime_service.execute_tool(
        tool_name="check_ticket_status",
        arguments={"ticket_id": ticket_id},
    )

    assert isinstance(status_result, dict)
    assert "ticket_id" in status_result
    assert status_result["ticket_id"] == ticket_id
    assert "status" in status_result


@pytest.mark.asyncio
async def test_check_ticket_status_not_found(mock_realtime_service) -> None:
    """check_ticket_status returns error for unknown ticket."""
    result = await mock_realtime_service.execute_tool(
        tool_name="check_ticket_status",
        arguments={"ticket_id": "TKT-XX-99999999-0000"},
    )

    assert isinstance(result, dict)
    assert "error" in result


@pytest.mark.asyncio
async def test_unknown_tool_returns_error(mock_realtime_service) -> None:
    """Unknown tool name returns an error dict."""
    result = await mock_realtime_service.execute_tool(
        tool_name="fly_to_the_moon",
        arguments={},
    )

    assert isinstance(result, dict)
    assert "error" in result


# =============================================================================
# T024: test_policy_keyword_escalation_via_voice
# =============================================================================


@pytest.mark.asyncio
async def test_policy_keyword_escalation_via_voice(mock_realtime_service) -> None:
    """
    T024: When analyze_and_route_query detects policy keywords in a voice query,
    the result includes escalation=True.
    """
    # These queries contain known policy escalation keywords
    escalation_queries = [
        "I want to appeal my grade",
        "I need a tuition refund",
        "I want to file a Title IX complaint",
    ]

    for query in escalation_queries:
        result = await mock_realtime_service.execute_tool(
            tool_name="analyze_and_route_query",
            arguments={"query": query},
        )

        assert isinstance(result, dict), f"Expected dict for query: {query}"
        # The result should indicate escalation
        escalated = result.get("escalated", False)
        # Also accept if department is ESCALATE_TO_HUMAN
        dept = result.get("department", "")
        assert escalated or dept == "ESCALATE_TO_HUMAN", (
            f"Expected escalation for policy query '{query}', got: {result}"
        )


# =============================================================================
# T029: Session context preservation across modality switches
# =============================================================================


@pytest.mark.asyncio
async def test_session_context_preserved_across_modalities(mock_realtime_service) -> None:
    """
    T029: Text chat creates a ticket; voice check_ticket_status with same
    session_id finds the ticket.
    """
    from fastapi.testclient import TestClient
    from app.core.dependencies import clear_service_caches
    clear_service_caches()
    from app.main import create_app
    app = create_app()
    client = TestClient(app)

    # Step 1: Create ticket via text chat
    text_response = client.post(
        "/api/chat",
        json={"message": "I cannot access my student email", "session_id": None}
    )
    assert text_response.status_code == 200
    text_data = text_response.json()
    ticket_id = text_data.get("ticket_id")

    if ticket_id is None:
        pytest.skip("Text chat did not create a ticket (kb_only response)")

    session_id = str(text_data.get("session_id", ""))

    # Step 2: Voice check_ticket_status with same session context
    voice_result = await mock_realtime_service.execute_tool(
        tool_name="check_ticket_status",
        arguments={"ticket_id": ticket_id},
        session_id=session_id,
    )

    assert isinstance(voice_result, dict)
    assert "ticket_id" in voice_result
    assert voice_result["ticket_id"] == ticket_id


# =============================================================================
# Tool definitions structure validation
# =============================================================================


def test_get_tool_definitions_returns_4_tools(mock_realtime_service) -> None:
    """get_tool_definitions returns exactly 4 voice tools."""
    tools = mock_realtime_service.get_tool_definitions()
    assert len(tools) == 4

    names = {t["name"] for t in tools}
    assert names == {
        "analyze_and_route_query",
        "check_ticket_status",
        "search_knowledge_base",
        "escalate_to_human",
    }


def test_escalate_to_human_tool_description_covers_policy_keywords() -> None:
    """
    T026: escalate_to_human tool description must mention policy-related topics
    so the model knows when to use it.
    """
    from app.services.mock.realtime_service import get_voice_tool_definitions
    tools = get_voice_tool_definitions()

    escalate_tool = next(t for t in tools if t["name"] == "escalate_to_human")
    description = escalate_tool["description"].lower()

    # Check key policy keyword categories are mentioned
    assert "appeal" in description or "policy" in description
    assert "human" in description
    assert "sensitive" in description or "title ix" in description or "mental health" in description


def test_voice_system_prompt_includes_escalation_instructions() -> None:
    """
    T025: Voice system prompt instructs model to escalate on policy keywords.
    """
    from app.services.mock.realtime_service import VOICE_SYSTEM_PROMPT
    prompt_lower = VOICE_SYSTEM_PROMPT.lower()

    assert "escalat" in prompt_lower
    assert "human" in prompt_lower
    # Check policy keywords are listed
    assert "appeal" in prompt_lower or "refund" in prompt_lower
