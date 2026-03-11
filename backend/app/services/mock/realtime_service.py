"""
Mock Realtime Service for voice interaction testing without Azure credentials.
Returns simulated ephemeral tokens and delegates tool calls to the existing agent pipeline.
"""

import hashlib
import uuid
from typing import Optional

from app.agents import ActionAgent, QueryAgent, RouterAgent
from app.core.config import get_settings
from app.services.interfaces import (
    KnowledgeServiceInterface,
    LLMServiceInterface,
    RealtimeServiceInterface,
    SessionStoreInterface,
    TicketServiceInterface,
)


VOICE_SYSTEM_PROMPT = """You are a helpful university support assistant communicating via voice.

Speak concisely and naturally. Do not use markdown formatting — speak in plain sentences.
Spell out ticket IDs character by character (e.g., "T-K-T dash I-T dash two zero two six...").
Do NOT repeat PII back to the student.

If the student mentions appeals, waivers, refunds, Title IX, mental health,
or asks to speak to a human, use the escalate_to_human tool immediately.

Always be empathetic and student-friendly. Keep responses brief for voice delivery."""


def get_voice_tool_definitions() -> list[dict]:
    """Return Realtime API tool schemas for the 4 voice tools."""
    return [
        {
            "type": "function",
            "name": "analyze_and_route_query",
            "description": (
                "Analyze a student's support request, route it to the correct department, "
                "create a support ticket, and find relevant knowledge base articles. "
                "Use this as the primary tool for handling student requests."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The student's support request in their own words",
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Optional session ID for conversation context",
                    },
                },
                "required": ["query"],
            },
        },
        {
            "type": "function",
            "name": "check_ticket_status",
            "description": "Check the status of a previously created support ticket.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "string",
                        "description": "The ticket ID to look up (e.g., TKT-IT-20260201-0001)",
                    },
                },
                "required": ["ticket_id"],
            },
        },
        {
            "type": "function",
            "name": "search_knowledge_base",
            "description": (
                "Search the knowledge base for articles relevant to a student's question. "
                "Use this to find self-service instructions before creating a ticket."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query to find relevant help articles",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of articles to return (default 3)",
                        "default": 3,
                    },
                },
                "required": ["query"],
            },
        },
        {
            "type": "function",
            "name": "escalate_to_human",
            "description": (
                "Transfer the student to a human support agent. "
                "Use this when the student explicitly asks for a human, "
                "mentions policy-related topics (appeals, waivers, refunds), "
                "or discusses sensitive topics (Title IX, mental health, discrimination, threats)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The student's request that requires human review",
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for escalation (e.g., 'policy_keyword', 'user_request', 'sensitive_topic')",
                    },
                },
                "required": ["query", "reason"],
            },
        },
    ]


class MockRealtimeService(RealtimeServiceInterface):
    """
    Mock implementation of Realtime Service for development and testing.
    Returns fake ephemeral tokens and executes tool calls via the real agent pipeline.
    """

    def __init__(
        self,
        llm_service: LLMServiceInterface,
        ticket_service: TicketServiceInterface,
        knowledge_service: KnowledgeServiceInterface,
        session_store: Optional[SessionStoreInterface] = None,
    ) -> None:
        self._llm = llm_service
        self._tickets = ticket_service
        self._knowledge = knowledge_service
        self._session_store = session_store
        self._settings = get_settings()

    async def create_session(self) -> dict:
        """Return a mock ephemeral token for WebRTC simulation."""
        mock_token = f"mock-token-{uuid.uuid4().hex[:16]}"
        return {
            "token": mock_token,
            "endpoint": "mock://realtime.openai.azure.com/v1/realtime",
            "tool_definitions": self.get_tool_definitions(),
            "voice_config": {
                "voice": self._settings.realtime_voice,
                "vad_threshold": self._settings.realtime_vad_threshold,
            },
            "mock": True,
        }

    def get_tool_definitions(self) -> list[dict]:
        """Return Realtime API tool schemas for the 4 voice tools."""
        return get_voice_tool_definitions()

    async def execute_tool(
        self,
        tool_name: str,
        arguments: dict,
        session_id: Optional[str] = None,
    ) -> dict:
        """Execute a tool call against the existing agent pipeline."""
        if tool_name == "analyze_and_route_query":
            return await self._handle_analyze_and_route(arguments, session_id)
        elif tool_name == "check_ticket_status":
            return await self._handle_check_ticket_status(arguments)
        elif tool_name == "search_knowledge_base":
            return await self._handle_search_knowledge_base(arguments)
        elif tool_name == "escalate_to_human":
            return await self._handle_escalate_to_human(arguments, session_id)
        else:
            return {"error": f"Unknown tool: {tool_name}"}

    async def _handle_analyze_and_route(
        self, arguments: dict, session_id: Optional[str]
    ) -> dict:
        """Route a query through the full 3-agent pipeline."""
        query = arguments.get("query", "")
        student_id_hash = hashlib.sha256(b"voice_demo_student").hexdigest()

        query_agent = QueryAgent(self._llm)
        router_agent = RouterAgent(self._settings)
        action_agent = ActionAgent(self._tickets, self._knowledge, self._llm)

        query_result = await query_agent.analyze(message=query)
        routing_decision = router_agent.route(query_result=query_result)
        action_result = await action_agent.execute(
            query_result=query_result,
            routing_decision=routing_decision,
            student_id_hash=student_id_hash,
            original_message=query,
        )

        return {
            "ticket_id": action_result.ticket_id,
            "department": action_result.department.value if action_result.department else None,
            "status": action_result.status.value,
            "escalated": action_result.escalated,
            "knowledge_articles": [
                {
                    "article_id": a.article_id,
                    "title": a.title,
                    "url": a.url,
                    "snippet": a.snippet,
                    "relevance_score": a.relevance_score,
                }
                for a in action_result.knowledge_articles
            ],
            "estimated_response_time": action_result.estimated_response_time,
            "message": action_result.user_message,
        }

    async def _handle_check_ticket_status(self, arguments: dict) -> dict:
        """Check the status of an existing ticket."""
        ticket_id = arguments.get("ticket_id", "")
        result = await self._tickets.get_ticket_status(ticket_id)
        if result is None:
            return {"error": f"Ticket {ticket_id} not found"}
        return {
            "ticket_id": result.ticket_id,
            "status": result.status.value,
            "department": result.department.value,
            "summary": result.summary,
            "priority": result.priority.value if result.priority else None,
            "assigned_to": result.assigned_to,
        }

    async def _handle_search_knowledge_base(self, arguments: dict) -> dict:
        """Search knowledge base articles."""
        query = arguments.get("query", "")
        limit = min(int(arguments.get("limit", 3)), 3)
        articles = await self._knowledge.search(query=query, limit=limit)
        return {
            "articles": [
                {
                    "article_id": a.article_id,
                    "title": a.title,
                    "url": a.url,
                    "snippet": a.snippet,
                    "relevance_score": a.relevance_score,
                }
                for a in articles
            ],
            "total": len(articles),
        }

    async def _handle_escalate_to_human(
        self, arguments: dict, session_id: Optional[str]
    ) -> dict:
        """Create an escalation ticket."""
        from datetime import datetime, timezone
        from app.models.enums import Department, Priority

        query = arguments.get("query", "")
        reason = arguments.get("reason", "user_request")
        student_id_hash = hashlib.sha256(b"voice_demo_student").hexdigest()

        ticket_id, ticket_url = await self._tickets.create_ticket(
            department=Department.ESCALATE_TO_HUMAN,
            priority=Priority.HIGH,
            summary="Voice escalation request",
            description=f"Voice escalation reason: {reason}\nQuery: {query}",
            student_id_hash=student_id_hash,
            entities={"reason": reason, "modality": "voice"},
        )

        return {
            "ticket_id": ticket_id,
            "message": (
                f"I've escalated your request to a human support specialist. "
                f"Your ticket ID is {ticket_id}. "
                f"A team member will follow up with you shortly."
            ),
            "escalated": True,
            "reason": reason,
        }
