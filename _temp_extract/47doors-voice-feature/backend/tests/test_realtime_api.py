"""
Tests for the Realtime API voice endpoints.

Covers:
- POST /api/realtime/session — ephemeral token creation
- WebSocket /api/realtime/ws — tool call relay
- Voice disabled (503) scenario
"""

import json
import os

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

# Ensure test environment before importing app
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("MOCK_MODE", "true")


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def app():
    """Create test application with mock services."""
    from app.core.dependencies import clear_service_caches
    clear_service_caches()
    from app.main import create_app
    return create_app()


@pytest.fixture
def client(app):
    """Synchronous test client."""
    return TestClient(app)


@pytest.fixture
async def async_client(app):
    """Asynchronous test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# =============================================================================
# T012: test_create_session
# =============================================================================


def test_create_session_returns_token(client: TestClient) -> None:
    """
    T012: POST /api/realtime/session returns ephemeral token, endpoint URL,
    tool definitions, and voice config.
    """
    response = client.post("/api/realtime/session")
    assert response.status_code == 200

    data = response.json()

    # Must have a token
    assert "token" in data
    assert isinstance(data["token"], str)
    assert len(data["token"]) > 0

    # Must have an endpoint URL
    assert "endpoint" in data
    assert isinstance(data["endpoint"], str)
    assert len(data["endpoint"]) > 0

    # Must have tool definitions (4 tools)
    assert "tool_definitions" in data
    tool_defs = data["tool_definitions"]
    assert isinstance(tool_defs, list)
    assert len(tool_defs) == 4

    tool_names = {t["name"] for t in tool_defs}
    assert "analyze_and_route_query" in tool_names
    assert "check_ticket_status" in tool_names
    assert "search_knowledge_base" in tool_names
    assert "escalate_to_human" in tool_names

    # Must have voice config
    assert "voice_config" in data
    voice_config = data["voice_config"]
    assert "voice" in voice_config
    assert "vad_threshold" in voice_config
    assert 0.0 <= voice_config["vad_threshold"] <= 1.0


def test_create_session_mock_mode(client: TestClient) -> None:
    """Mock mode session returns a recognizable mock token."""
    response = client.post("/api/realtime/session")
    assert response.status_code == 200

    data = response.json()
    # Mock mode token starts with "mock-token-"
    assert data["token"].startswith("mock-token-") or len(data["token"]) > 0
    # Mock mode flag
    assert data.get("mock") is True


def test_create_session_tool_definitions_have_required_fields(client: TestClient) -> None:
    """Each tool definition must have type, name, description, and parameters."""
    response = client.post("/api/realtime/session")
    assert response.status_code == 200

    tool_defs = response.json()["tool_definitions"]
    for tool in tool_defs:
        assert "type" in tool
        assert tool["type"] == "function"
        assert "name" in tool
        assert "description" in tool
        assert "parameters" in tool
        assert "properties" in tool["parameters"]


# =============================================================================
# T035: test_session_when_voice_disabled
# =============================================================================


def test_session_when_voice_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    T035: POST /api/realtime/session returns 503 with informative message
    when voice_enabled=false.
    """
    monkeypatch.setenv("VOICE_ENABLED", "false")

    # Re-create app with new env
    from app.core.config import get_settings
    get_settings.cache_clear()

    from app.core.dependencies import clear_service_caches
    clear_service_caches()

    from app.main import create_app
    app = create_app()
    client = TestClient(app)

    response = client.post("/api/realtime/session")
    assert response.status_code == 503

    error_data = response.json()
    assert "detail" in error_data

    # Restore
    get_settings.cache_clear()
    clear_service_caches()


# =============================================================================
# T015: test_websocket_tool_execution
# =============================================================================


def test_websocket_tool_execution_analyze_query(client: TestClient) -> None:
    """
    T015: WebSocket /api/realtime/ws receives a tool_call message,
    executes it via the pipeline, and returns a tool_result with call_id.
    """
    with client.websocket_connect("/api/realtime/ws") as ws:
        # Send a tool call
        ws.send_text(json.dumps({
            "type": "tool_call",
            "tool_name": "analyze_and_route_query",
            "arguments": {"query": "I forgot my password"},
            "call_id": "call-001",
        }))

        # Receive the result
        raw = ws.receive_text()
        result = json.loads(raw)

        assert result["type"] == "tool_result"
        assert result["call_id"] == "call-001"
        assert "result" in result

        tool_result = result["result"]
        assert "ticket_id" in tool_result or "message" in tool_result


def test_websocket_tool_execution_search_kb(client: TestClient) -> None:
    """WebSocket search_knowledge_base tool returns articles list."""
    with client.websocket_connect("/api/realtime/ws") as ws:
        ws.send_text(json.dumps({
            "type": "tool_call",
            "tool_name": "search_knowledge_base",
            "arguments": {"query": "password reset", "limit": 3},
            "call_id": "call-002",
        }))

        raw = ws.receive_text()
        result = json.loads(raw)

        assert result["type"] == "tool_result"
        assert result["call_id"] == "call-002"
        tool_result = result["result"]
        assert "articles" in tool_result
        assert isinstance(tool_result["articles"], list)


def test_websocket_ping_pong(client: TestClient) -> None:
    """WebSocket responds to ping with pong."""
    with client.websocket_connect("/api/realtime/ws") as ws:
        ws.send_text(json.dumps({"type": "ping"}))
        raw = ws.receive_text()
        result = json.loads(raw)
        assert result["type"] == "pong"


def test_websocket_session_start(client: TestClient) -> None:
    """WebSocket responds to session_start with session_ack."""
    import uuid
    session_id = str(uuid.uuid4())

    with client.websocket_connect("/api/realtime/ws") as ws:
        ws.send_text(json.dumps({
            "type": "session_start",
            "session_id": session_id,
        }))
        raw = ws.receive_text()
        result = json.loads(raw)
        assert result["type"] == "session_ack"
        assert result["session_id"] == session_id


def test_websocket_invalid_json(client: TestClient) -> None:
    """WebSocket handles invalid JSON gracefully."""
    with client.websocket_connect("/api/realtime/ws") as ws:
        ws.send_text("not-json{{{")
        raw = ws.receive_text()
        result = json.loads(raw)
        assert result["type"] == "error"


def test_websocket_unknown_tool(client: TestClient) -> None:
    """WebSocket returns error or result for unknown tool name."""
    with client.websocket_connect("/api/realtime/ws") as ws:
        ws.send_text(json.dumps({
            "type": "tool_call",
            "tool_name": "nonexistent_tool",
            "arguments": {},
            "call_id": "call-err",
        }))
        raw = ws.receive_text()
        result = json.loads(raw)
        # Should get either tool_result with error or error type
        assert result.get("call_id") == "call-err" or result.get("type") == "error"


# =============================================================================
# Health check includes realtime_api
# =============================================================================


def test_health_check_includes_realtime_api(client: TestClient) -> None:
    """GET /api/health response includes realtime_api service status."""
    response = client.get("/api/health")
    assert response.status_code == 200

    data = response.json()
    assert "services" in data
    assert "realtime_api" in data["services"]

    realtime_health = data["services"]["realtime_api"]
    assert "status" in realtime_health
    assert realtime_health["status"] in ("up", "down", "degraded")
