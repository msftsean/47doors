"""
Azure OpenAI Realtime Service for voice interaction.
Creates ephemeral tokens for WebRTC auth and executes tool calls via the agent pipeline.
"""

import hashlib
import uuid
from typing import Optional

import httpx

from app.agents import ActionAgent, QueryAgent, RouterAgent
from app.core.config import get_settings
from app.services.interfaces import (
    KnowledgeServiceInterface,
    LLMServiceInterface,
    RealtimeServiceInterface,
    SessionStoreInterface,
    TicketServiceInterface,
)
from app.services.mock.realtime_service import get_voice_tool_definitions, VOICE_SYSTEM_PROMPT


class AzureRealtimeService(RealtimeServiceInterface):
    """
    Production implementation of Realtime Service using Azure OpenAI Realtime API.
    Creates ephemeral session tokens for WebRTC connections and executes tool calls.
    """

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        deployment: str,
        api_version: str,
        llm_service: LLMServiceInterface,
        ticket_service: TicketServiceInterface,
        knowledge_service: KnowledgeServiceInterface,
        session_store: Optional[SessionStoreInterface] = None,
        voice: str = "alloy",
        vad_threshold: float = 0.5,
    ) -> None:
        self._endpoint = endpoint.rstrip("/")
        self._api_key = api_key
        self._deployment = deployment
        self._api_version = api_version
        self._llm = llm_service
        self._tickets = ticket_service
        self._knowledge = knowledge_service
        self._session_store = session_store
        self._voice = voice
        self._vad_threshold = vad_threshold
        self._settings = get_settings()

    async def create_session(self) -> dict:
        """
        Call Azure OpenAI REST API to create an ephemeral session token for WebRTC auth.
        Returns token, endpoint URL, tool definitions, and voice config.
        """
        # Azure OpenAI Realtime session endpoint
        session_url = (
            f"{self._endpoint}/openai/realtimeapi/sessions"
            f"?api-version={self._api_version}"
        )

        # Session configuration for the Realtime API
        session_config = {
            "model": self._deployment,
            "instructions": VOICE_SYSTEM_PROMPT,
            "voice": self._voice,
            "input_audio_format": "pcm16",
            "output_audio_format": "pcm16",
            "turn_detection": {
                "type": "server_vad",
                "threshold": self._vad_threshold,
                "prefix_padding_ms": 300,
                "silence_duration_ms": 500,
            },
            "tools": self.get_tool_definitions(),
            "tool_choice": "auto",
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                session_url,
                json=session_config,
                headers={
                    "api-key": self._api_key,
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            session_data = response.json()

        # Extract ephemeral token and endpoint from Azure response
        token = session_data.get("client_secret", {}).get("value", "")
        realtime_endpoint = session_data.get("url", f"{self._endpoint}/openai/realtime")

        return {
            "token": token,
            "endpoint": realtime_endpoint,
            "tool_definitions": self.get_tool_definitions(),
            "voice_config": {
                "voice": self._voice,
                "vad_threshold": self._vad_threshold,
            },
            "session_id": session_data.get("id", str(uuid.uuid4())),
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
        # Delegate to mock service logic (same pipeline, different token source)
        from app.services.mock.realtime_service import MockRealtimeService

        mock = MockRealtimeService(
            llm_service=self._llm,
            ticket_service=self._tickets,
            knowledge_service=self._knowledge,
            session_store=self._session_store,
        )
        return await mock.execute_tool(tool_name, arguments, session_id)
