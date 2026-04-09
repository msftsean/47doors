"""WebSocket bridge: ACS media streaming ↔ Azure OpenAI Realtime API.

Routes:
  WS /ws/acs-media  — bidirectional audio relay between ACS Call Automation
                       media streaming and the Azure OpenAI Realtime API.

ACS cannot authenticate directly to Azure OpenAI (disableLocalAuth=true,
no ACS managed identity configured). This bridge uses the backend's own
managed identity to open an authenticated WebSocket to the Realtime API,
then relays audio frames in both directions.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Optional

import websockets
from azure.core.credentials import AccessToken
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.dependencies import get_realtime_service, get_settings
from app.services.azure.phone import PHONE_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

router = APIRouter()


class _TokenManager:
    """Thread-safe managed-identity token cache for the OpenAI WebSocket."""

    def __init__(self) -> None:
        self._credential = None
        self._token: Optional[AccessToken] = None
        self._lock = asyncio.Lock()

    async def get_token(self) -> str:
        refresh_buffer = 300
        needs_refresh = (
            not self._token
            or datetime.now(timezone.utc) >= datetime.fromtimestamp(
                self._token.expires_on - refresh_buffer, tz=timezone.utc
            )
        )
        if needs_refresh:
            async with self._lock:
                if not self._credential:
                    from azure.identity.aio import ManagedIdentityCredential
                    self._credential = ManagedIdentityCredential()
                self._token = await self._credential.get_token(
                    "https://cognitiveservices.azure.com/.default"
                )
                logger.info("Media bridge: MI token acquired")
        return self._token.token


_token_mgr = _TokenManager()


@router.websocket("/acs-media")
async def acs_media_bridge(ws: WebSocket) -> None:
    """Bridge ACS media streaming to Azure OpenAI Realtime API.

    Audio flow:
      Caller → ACS → [this WS] → Azure OpenAI Realtime → [this WS] → ACS → Caller
    """
    await ws.accept()
    settings = get_settings()
    logger.info("Media bridge: ACS WebSocket connected")

    openai_ws = None
    session_ready = asyncio.Event()

    try:
        token = await _token_mgr.get_token()

        openai_url = (
            f"{settings.azure_openai_endpoint.replace('https://', 'wss://')}"
            f"/openai/realtime"
            f"?api-version={settings.azure_openai_realtime_api_version}"
            f"&deployment={settings.azure_openai_realtime_deployment}"
        )
        logger.info(
            f"Media bridge: connecting to OpenAI Realtime "
            f"deployment={settings.azure_openai_realtime_deployment}"
        )

        openai_ws = await websockets.connect(
            openai_url,
            additional_headers={"Authorization": f"Bearer {token}"},
        )
        logger.info("Media bridge: OpenAI Realtime WebSocket connected")

        # ------------------------------------------------------------------
        # Coroutine: read OpenAI messages, forward audio & handle events
        # ------------------------------------------------------------------
        async def _openai_receiver() -> None:
            nonlocal openai_ws
            realtime_svc = get_realtime_service()
            tools = await realtime_svc.get_tool_definitions()
            tool_defs = [
                {
                    "type": "function",
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                }
                for t in tools
            ]

            async for raw in openai_ws:
                msg = json.loads(raw)
                t = msg.get("type", "")

                # -- Session lifecycle ------------------------------------
                if t == "session.created":
                    logger.info("Media bridge: session.created — sending config")
                    await openai_ws.send(json.dumps({
                        "type": "session.update",
                        "session": {
                            "instructions": PHONE_SYSTEM_PROMPT,
                            "audio": {
                                "input": {
                                    "format": "pcm16",
                                    "transcription": {"model": "whisper-1"},
                                },
                                "output": {
                                    "format": "pcm16",
                                    "voice": settings.realtime_voice,
                                },
                            },
                            "turn_detection": {
                                "type": "server_vad",
                                "threshold": 0.5,
                                "prefix_padding_ms": 300,
                                "silence_duration_ms": settings.realtime_vad_threshold_ms,
                            },
                            "tools": tool_defs,
                        },
                    }))
                    logger.info("Media bridge: session.update sent")
                    session_ready.set()
                    continue

                if t == "session.updated":
                    logger.info("Media bridge: session.updated confirmed")
                    continue

                # -- Audio to caller (via ACS) ----------------------------
                if t == "response.audio.delta":
                    delta = msg.get("delta", "")
                    if delta:
                        await ws.send_text(json.dumps({
                            "kind": "AudioData",
                            "audioData": {"data": delta},
                        }))
                    continue

                # -- Barge-in: stop AI playback when user speaks ----------
                if t == "input_audio_buffer.speech_started":
                    try:
                        await ws.send_text(json.dumps({
                            "kind": "StopAudio",
                            "stopAudio": {},
                        }))
                    except Exception:
                        pass
                    continue

                # -- Transcript logging -----------------------------------
                if t == "response.audio_transcript.done":
                    logger.info(
                        f"Media bridge: AI said: "
                        f"{msg.get('transcript', '')[:120]}"
                    )
                    continue

                if t == "conversation.item.input_audio_transcription.completed":
                    logger.info(
                        f"Media bridge: Caller said: "
                        f"{msg.get('transcript', '')[:120]}"
                    )
                    continue

                # -- Tool calls -------------------------------------------
                if t == "response.function_call_arguments.done":
                    call_id = msg.get("call_id", "")
                    name = msg.get("name", "")
                    logger.info(f"Media bridge: tool call '{name}'")
                    try:
                        args = json.loads(msg.get("arguments", "{}"))
                    except json.JSONDecodeError:
                        args = {}
                    result = await realtime_svc.execute_tool(
                        call_id, name, args, "phone-call"
                    )
                    await openai_ws.send(json.dumps({
                        "type": "conversation.item.create",
                        "item": {
                            "type": "function_call_output",
                            "call_id": call_id,
                            "output": result.result or result.error or "",
                        },
                    }))
                    await openai_ws.send(json.dumps({"type": "response.create"}))
                    logger.info(f"Media bridge: tool '{name}' result sent")
                    continue

                # -- Errors -----------------------------------------------
                if t == "error":
                    logger.error(
                        f"Media bridge: OpenAI error: {msg.get('error', {})}"
                    )
                    continue

                # Known noise events — ignore silently
                if t in (
                    "response.created", "response.done",
                    "response.output_item.added", "response.output_item.done",
                    "response.content_part.added", "response.content_part.done",
                    "response.audio.done", "response.audio_transcript.delta",
                    "conversation.item.created",
                    "input_audio_buffer.speech_stopped",
                    "input_audio_buffer.committed",
                    "conversation.item.input_audio_transcription.delta",
                    "response.function_call_arguments.delta",
                ):
                    continue

                logger.debug(f"Media bridge: unhandled OpenAI event: {t}")

        # ------------------------------------------------------------------
        # Coroutine: read ACS media messages, forward audio to OpenAI
        # ------------------------------------------------------------------
        async def _acs_sender() -> None:
            try:
                while True:
                    raw = await ws.receive_text()
                    msg = json.loads(raw)
                    kind = msg.get("kind", "")

                    if kind == "AudioMetadata":
                        meta = msg.get("audioMetadata", {})
                        logger.info(
                            f"Media bridge: ACS audio — "
                            f"rate={meta.get('sampleRate')} "
                            f"enc={meta.get('encoding')} "
                            f"ch={meta.get('channels')}"
                        )
                        continue

                    if kind == "AudioData":
                        b64 = msg.get("audioData", {}).get("data", "")
                        silent = msg.get("audioData", {}).get("silent", False)
                        if b64 and not silent:
                            await session_ready.wait()
                            await openai_ws.send(json.dumps({
                                "type": "input_audio_buffer.append",
                                "audio": b64,
                            }))
                        continue

                    logger.debug(f"Media bridge: ACS msg kind={kind}")
            except WebSocketDisconnect:
                logger.info("Media bridge: ACS disconnected")
            except Exception as exc:
                logger.error(f"Media bridge: ACS read error: {exc}")

        # Run both; when one ends (hangup), cancel the other.
        done, pending = await asyncio.wait(
            [
                asyncio.create_task(_openai_receiver()),
                asyncio.create_task(_acs_sender()),
            ],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()

    except websockets.exceptions.InvalidStatus as exc:
        logger.error(
            f"Media bridge: OpenAI WS handshake rejected — "
            f"HTTP {exc.response.status_code}"
        )
    except Exception as exc:
        logger.error(f"Media bridge: fatal error: {exc}", exc_info=True)
    finally:
        if openai_ws and not openai_ws.closed:
            await openai_ws.close()
        try:
            await ws.close()
        except Exception:
            pass
        logger.info("Media bridge: session ended")
