"""
Realtime API endpoints for voice interaction.
Provides WebRTC session token issuance and WebSocket tool call relay.
"""

import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status

from app.core.config import Settings, get_settings
from app.core.dependencies import get_realtime_service
from app.models.schemas import ErrorResponse, ServiceHealth
from app.services.interfaces import RealtimeServiceInterface

logger = logging.getLogger(__name__)

realtime_router = APIRouter(prefix="/realtime", tags=["Voice / Realtime"])


# =============================================================================
# POST /api/realtime/session — Create ephemeral WebRTC session token
# =============================================================================


@realtime_router.post(
    "/session",
    responses={
        200: {"description": "Session created with ephemeral token"},
        503: {"model": ErrorResponse, "description": "Voice feature disabled or unavailable"},
    },
    summary="Create realtime voice session",
    description=(
        "Create an ephemeral session token for WebRTC authentication with the "
        "Azure OpenAI Realtime API. Also returns tool definitions and voice config."
    ),
)
async def create_realtime_session(
    settings: Settings = Depends(get_settings),
    realtime_service: RealtimeServiceInterface = Depends(get_realtime_service),
) -> dict:
    """
    Create a new voice session and return an ephemeral WebRTC token.
    The frontend uses this token to connect directly to Azure OpenAI Realtime API.
    """
    if not settings.voice_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "voice_disabled",
                "message": "Voice mode is temporarily unavailable. Please use text chat.",
            },
        )

    try:
        session = await realtime_service.create_session()
        return session
    except Exception as e:
        logger.error(f"Failed to create realtime session: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "realtime_unavailable",
                "message": "Voice mode is temporarily unavailable. Please use text chat.",
            },
        )


# =============================================================================
# WebSocket /api/realtime/ws — Tool call relay
# =============================================================================


@realtime_router.websocket("/ws")
async def realtime_websocket(
    websocket: WebSocket,
    settings: Settings = Depends(get_settings),
    realtime_service: RealtimeServiceInterface = Depends(get_realtime_service),
) -> None:
    """
    WebSocket endpoint for relaying tool call execution.

    The frontend establishes a WebRTC connection to Azure OpenAI Realtime API
    and relays tool call invocations here via this WebSocket.

    Protocol:
    - Client sends: {"type": "tool_call", "tool_name": str, "arguments": dict, "call_id": str, "session_id": str?}
    - Server sends: {"type": "tool_result", "call_id": str, "result": dict}
    - Server sends: {"type": "error", "call_id": str, "message": str}
    """
    if not settings.voice_enabled:
        await websocket.close(code=1008, reason="Voice feature disabled")
        return

    await websocket.accept()
    logger.info("Realtime WebSocket connection established")

    session_id: Optional[str] = None

    try:
        while True:
            # Receive message from frontend
            raw = await websocket.receive_text()

            try:
                message = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_text(
                    json.dumps({"type": "error", "message": "Invalid JSON"})
                )
                continue

            msg_type = message.get("type")

            if msg_type == "tool_call":
                call_id = message.get("call_id", "")
                tool_name = message.get("tool_name", "")
                arguments = message.get("arguments", {})
                session_id = message.get("session_id") or session_id

                logger.info(f"Executing voice tool: {tool_name} (call_id={call_id})")

                try:
                    result = await realtime_service.execute_tool(
                        tool_name=tool_name,
                        arguments=arguments,
                        session_id=session_id,
                    )
                    await websocket.send_text(
                        json.dumps({
                            "type": "tool_result",
                            "call_id": call_id,
                            "result": result,
                        })
                    )
                except Exception as e:
                    logger.error(f"Tool execution failed: {tool_name} — {e}")
                    await websocket.send_text(
                        json.dumps({
                            "type": "error",
                            "call_id": call_id,
                            "message": f"Tool execution failed: {str(e)}",
                        })
                    )

            elif msg_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

            elif msg_type == "session_start":
                session_id = message.get("session_id")
                await websocket.send_text(
                    json.dumps({"type": "session_ack", "session_id": session_id})
                )

            else:
                logger.warning(f"Unknown WebSocket message type: {msg_type}")

    except WebSocketDisconnect:
        logger.info("Realtime WebSocket disconnected")
    except Exception as e:
        logger.error(f"Realtime WebSocket error: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except Exception:
            pass
