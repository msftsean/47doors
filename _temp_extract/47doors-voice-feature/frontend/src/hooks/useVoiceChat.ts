/**
 * Custom hook for managing voice chat state and WebRTC lifecycle.
 * Connects to Azure OpenAI Realtime API via WebRTC for voice interaction.
 * Falls back gracefully when WebRTC is unavailable or Azure credentials are missing.
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { createRealtimeSession, ApiClientError } from '../api/client';
import type { VoiceState, VoiceMessage } from '../types';

const WS_BASE_URL =
  (import.meta.env.VITE_API_BASE_URL || '').replace(/^http/, 'ws') || '';

interface UseVoiceChatOptions {
  sessionId: string | null;
  onTranscriptMessage?: (message: VoiceMessage) => void;
}

interface UseVoiceChatReturn {
  startVoiceSession: () => Promise<void>;
  stopVoiceSession: () => void;
  voiceState: VoiceState;
  transcript: VoiceMessage[];
  isVoiceSupported: boolean;
  error: string | null;
}

function isWebRTCSupported(): boolean {
  return (
    typeof window !== 'undefined' &&
    typeof window.RTCPeerConnection !== 'undefined'
  );
}

export function useVoiceChat({
  sessionId,
  onTranscriptMessage,
}: UseVoiceChatOptions): UseVoiceChatReturn {
  const [voiceState, setVoiceState] = useState<VoiceState>('idle');
  const [transcript, setTranscript] = useState<VoiceMessage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isVoiceSupported] = useState<boolean>(isWebRTCSupported);

  const peerConnectionRef = useRef<RTCPeerConnection | null>(null);
  const dataChannelRef = useRef<RTCDataChannel | null>(null);
  const audioStreamRef = useRef<MediaStream | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const isMockRef = useRef<boolean>(false);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cleanupResources();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function cleanupResources() {
    if (dataChannelRef.current) {
      dataChannelRef.current.close();
      dataChannelRef.current = null;
    }
    if (peerConnectionRef.current) {
      peerConnectionRef.current.close();
      peerConnectionRef.current = null;
    }
    if (audioStreamRef.current) {
      audioStreamRef.current.getTracks().forEach((track) => track.stop());
      audioStreamRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }

  /**
   * Connect backend WebSocket relay for tool call execution.
   */
  function connectToolRelay(): WebSocket {
    const wsUrl = `${WS_BASE_URL}/api/realtime/ws`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      if (sessionId) {
        ws.send(
          JSON.stringify({ type: 'session_start', session_id: sessionId })
        );
      }
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data as string);
        if (msg.type === 'tool_result' && dataChannelRef.current?.readyState === 'open') {
          // Send tool result back to Realtime API data channel
          dataChannelRef.current.send(
            JSON.stringify({
              type: 'conversation.item.create',
              item: {
                type: 'function_call_output',
                call_id: msg.call_id,
                output: JSON.stringify(msg.result),
              },
            })
          );
          // Trigger response generation
          dataChannelRef.current.send(
            JSON.stringify({ type: 'response.create' })
          );
        }
      } catch {
        // Ignore malformed messages
      }
    };

    ws.onerror = () => {
      setError('Tool relay connection failed');
    };

    return ws;
  }

  /**
   * Handle a tool call event from the Realtime API data channel.
   */
  function handleToolCallEvent(event: { call_id: string; name: string; arguments: string }) {
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) return;

    let parsedArgs: Record<string, unknown> = {};
    try {
      parsedArgs = JSON.parse(event.arguments);
    } catch {
      parsedArgs = {};
    }

    ws.send(
      JSON.stringify({
        type: 'tool_call',
        tool_name: event.name,
        arguments: parsedArgs,
        call_id: event.call_id,
        session_id: sessionId,
      })
    );
    setVoiceState('processing');
  }

  /**
   * Handle a transcript delta event from the Realtime API.
   */
  function handleTranscriptDelta(delta: string, role: 'user' | 'assistant') {
    const msg: VoiceMessage = {
      id: uuidv4(),
      role,
      content: delta,
      timestamp: new Date(),
      modality: 'voice',
    };
    setTranscript((prev) => [...prev, msg]);
    onTranscriptMessage?.(msg);
  }

  /**
   * Start a voice session: get ephemeral token, set up WebRTC, connect to Realtime API.
   */
  const startVoiceSession = useCallback(async () => {
    if (!isVoiceSupported) {
      setVoiceState('disabled');
      setError('Voice is not supported in this browser.');
      return;
    }
    if (voiceState !== 'idle' && voiceState !== 'error') return;

    setError(null);
    setVoiceState('connecting');

    let sessionData: Awaited<ReturnType<typeof createRealtimeSession>>;
    try {
      sessionData = await createRealtimeSession();
    } catch (err) {
      const msg =
        err instanceof ApiClientError
          ? err.message
          : 'Voice mode is temporarily unavailable. Please use text chat.';
      setError(msg);
      setVoiceState('error');
      return;
    }

    const { token, endpoint } = sessionData;
    isMockRef.current = endpoint.startsWith('mock://');

    // Connect the backend WebSocket relay for tool calls
    const ws = connectToolRelay();
    wsRef.current = ws;

    // In mock mode, skip actual WebRTC and simulate listening state
    if (isMockRef.current) {
      await new Promise<void>((resolve) => {
        const check = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            clearInterval(check);
            resolve();
          } else if (ws.readyState === WebSocket.CLOSED || ws.readyState === WebSocket.CLOSING) {
            clearInterval(check);
            resolve();
          }
        }, 50);
        // Resolve after 500ms max even if WS hasn't opened
        setTimeout(() => { clearInterval(check); resolve(); }, 500);
      });
      setVoiceState('listening');
      return;
    }

    // Request microphone access
    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioStreamRef.current = stream;
    } catch {
      setError('Microphone access is required for voice mode.');
      setVoiceState('error');
      ws.close();
      return;
    }

    // Create WebRTC peer connection
    const pc = new RTCPeerConnection();
    peerConnectionRef.current = pc;

    // Add local audio track (mic → Azure OpenAI)
    stream.getTracks().forEach((track) => pc.addTrack(track, stream));

    // Set up remote audio playback (Azure OpenAI → speaker)
    const remoteAudio = new Audio();
    remoteAudio.autoplay = true;
    pc.ontrack = (e) => {
      remoteAudio.srcObject = e.streams[0];
    };

    // Create data channel for Realtime API events
    const dc = pc.createDataChannel('oai-events');
    dataChannelRef.current = dc;

    dc.onopen = () => {
      setVoiceState('listening');
      // Configure the session with tools
      dc.send(
        JSON.stringify({
          type: 'session.update',
          session: {
            tools: sessionData.tool_definitions,
            tool_choice: 'auto',
            voice: sessionData.voice_config.voice,
          },
        })
      );
    };

    dc.onmessage = (e) => {
      try {
        const evt = JSON.parse(e.data as string);
        switch (evt.type) {
          case 'response.function_call_arguments.done':
            handleToolCallEvent({
              call_id: evt.call_id,
              name: evt.name,
              arguments: evt.arguments,
            });
            break;
          case 'response.audio_transcript.delta':
            setVoiceState('speaking');
            break;
          case 'response.audio_transcript.done':
            handleTranscriptDelta(evt.transcript, 'assistant');
            setVoiceState('listening');
            break;
          case 'conversation.item.input_audio_transcription.completed':
            handleTranscriptDelta(evt.transcript, 'user');
            break;
          case 'input_audio_buffer.speech_started':
            setVoiceState('listening');
            break;
          case 'input_audio_buffer.speech_stopped':
            setVoiceState('processing');
            break;
          case 'error':
            setError(evt.error?.message || 'Voice error occurred');
            setVoiceState('error');
            break;
        }
      } catch {
        // Ignore malformed events
      }
    };

    dc.onclose = () => {
      if (voiceState !== 'idle') {
        setVoiceState('idle');
      }
    };

    pc.onconnectionstatechange = () => {
      if (
        pc.connectionState === 'failed' ||
        pc.connectionState === 'disconnected'
      ) {
        setError('Voice connection lost. Switching to text chat. Your conversation has been preserved.');
        setVoiceState('error');
        cleanupResources();
      }
    };

    // Create SDP offer and connect to Azure OpenAI Realtime endpoint
    try {
      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);

      const sdpResponse = await fetch(endpoint, {
        method: 'POST',
        body: offer.sdp,
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/sdp',
        },
      });

      if (!sdpResponse.ok) {
        throw new Error(`SDP exchange failed: ${sdpResponse.status}`);
      }

      const answerSdp = await sdpResponse.text();
      await pc.setRemoteDescription({ type: 'answer', sdp: answerSdp });
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'WebRTC connection failed';
      setError(msg);
      setVoiceState('error');
      cleanupResources();
    }
  }, [voiceState, isVoiceSupported, sessionId]); // eslint-disable-line react-hooks/exhaustive-deps

  /**
   * Stop the voice session and clean up resources.
   */
  const stopVoiceSession = useCallback(() => {
    cleanupResources();
    setVoiceState('idle');
    setError(null);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return {
    startVoiceSession,
    stopVoiceSession,
    voiceState,
    transcript,
    isVoiceSupported,
    error,
  };
}
