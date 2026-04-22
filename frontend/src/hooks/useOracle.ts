/**
 * useOracle — subscribes to the phone transcript SSE stream, detects
 * agent_speech events, requests a cinematic image for each one, and
 * exposes the current "scene" the projector should display.
 *
 * Design: we only ever keep the CURRENT scene and the most recent user
 * utterance. Old scenes cross-fade out and are discarded. This keeps
 * memory flat during a long talk.
 */

import { useEffect, useReducer, useRef } from 'react';
import type { TranscriptEvent } from '../types/demo';
import type { OracleImageResponse, OracleScene, OracleStatus } from '../types/oracle';

interface OracleState {
  status: OracleStatus;
  callActive: boolean;
  /** Most recent user utterance — shown as pre-response typography. */
  userUtterance: string | null;
  /** Current scene (agent reply + image). */
  scene: OracleScene | null;
  /** Previous scene kept for one crossfade tick, then cleared. */
  previousScene: OracleScene | null;
  /** Most recent tool call summary (shown as a subtle pill). */
  toolHint: string | null;
  /** Count of total agent responses this session (for the stat strip). */
  responseCount: number;
  /** Count of blocked responses (for the stat strip). */
  blockedCount: number;
}

type Action =
  | { type: 'event'; event: TranscriptEvent }
  | { type: 'scene_image'; sceneId: string; response: OracleImageResponse }
  | { type: 'clear_previous' };

const initial: OracleState = {
  status: 'idle',
  callActive: false,
  userUtterance: null,
  scene: null,
  previousScene: null,
  toolHint: null,
  responseCount: 0,
  blockedCount: 0,
};

function reducer(state: OracleState, action: Action): OracleState {
  switch (action.type) {
    case 'event': {
      const evt = action.event;
      if (evt.type === 'call_started') {
        return {
          ...initial,
          callActive: true,
          status: 'listening',
        };
      }
      if (evt.type === 'call_ended') {
        return { ...state, callActive: false, status: 'idle' };
      }
      if (evt.type === 'user_speech') {
        return {
          ...state,
          userUtterance: evt.text,
          status: 'listening',
          toolHint: null,
        };
      }
      if (evt.type === 'tool_call') {
        return { ...state, toolHint: evt.summary };
      }
      if (evt.type === 'agent_speech') {
        const newScene: OracleScene = {
          id: `${evt.call_id}-${evt.timestamp}`,
          agentText: evt.text,
          imageUrl: null,
          blocked: false,
          loading: true,
          enteredAt: Date.now(),
        };
        return {
          ...state,
          status: 'speaking',
          previousScene: state.scene,
          scene: newScene,
          responseCount: state.responseCount + 1,
          toolHint: null,
        };
      }
      return state;
    }
    case 'scene_image': {
      if (!state.scene || state.scene.id !== action.sceneId) return state;
      const r = action.response;
      const blocked = r.status === 'blocked';
      return {
        ...state,
        status: blocked ? 'blocked' : state.status,
        blockedCount: blocked ? state.blockedCount + 1 : state.blockedCount,
        scene: {
          ...state.scene,
          imageUrl: r.image ?? null,
          blocked,
          blockReason: r.reason,
          loading: false,
        },
      };
    }
    case 'clear_previous':
      return { ...state, previousScene: null };
    default:
      return state;
  }
}

const SSE_URL = '/api/phone/transcripts/stream';
const IMAGE_URL = '/api/oracle/image';
/**
 * Minimum time between image request starts.
 * gpt-image-1 is rate-limited to 3 req / 60s on Azure, so 22s between
 * starts gives us headroom for retries and avoids 429 cascades during
 * rapid back-and-forth conversation turns. Rate-limited scenes still
 * show typography and user utterance — only the image is skipped.
 */
const MIN_IMAGE_INTERVAL_MS = 22_000;

export function useOracle() {
  const [state, dispatch] = useReducer(reducer, initial);
  const esRef = useRef<EventSource | null>(null);
  const currentSceneIdRef = useRef<string | null>(null);
  const lastImageRequestAtRef = useRef<number>(0);

  // 1. Subscribe to SSE stream
  useEffect(() => {
    const es = new EventSource(SSE_URL);
    esRef.current = es;

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as TranscriptEvent;
        dispatch({ type: 'event', event: data });
      } catch {
        // ignore malformed events
      }
    };

    es.onerror = () => {
      // EventSource auto-reconnects; nothing to do.
    };

    return () => {
      es.close();
      esRef.current = null;
    };
  }, []);

  // 2. Whenever a new scene enters "loading", fire off an image request.
  useEffect(() => {
    const scene = state.scene;
    if (!scene || !scene.loading) return;
    if (currentSceneIdRef.current === scene.id) return;
    currentSceneIdRef.current = scene.id;

    // Rate-limit guard: if we fired an image request less than
    // MIN_IMAGE_INTERVAL_MS ago, skip this one. Agent text still shows;
    // we just don't request an image. Prevents 429 storms on stage.
    const now = Date.now();
    const elapsed = now - lastImageRequestAtRef.current;
    if (lastImageRequestAtRef.current > 0 && elapsed < MIN_IMAGE_INTERVAL_MS) {
      dispatch({
        type: 'scene_image',
        sceneId: scene.id,
        response: {
          status: 'error',
          error: `rate-limit-guard: ${Math.round((MIN_IMAGE_INTERVAL_MS - elapsed) / 1000)}s until next image`,
        },
      });
      return;
    }
    lastImageRequestAtRef.current = now;

    const controller = new AbortController();

    fetch(IMAGE_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: scene.agentText }),
      signal: controller.signal,
    })
      .then((r) => r.json() as Promise<OracleImageResponse>)
      .then((resp) => {
        dispatch({ type: 'scene_image', sceneId: scene.id, response: resp });
      })
      .catch((err) => {
        if (err?.name === 'AbortError') return;
        dispatch({
          type: 'scene_image',
          sceneId: scene.id,
          response: { status: 'error', error: String(err) },
        });
      });

    return () => controller.abort();
  }, [state.scene?.id]);

  // 3. Clear previousScene after one second so it crossfades out.
  useEffect(() => {
    if (!state.previousScene) return;
    const t = setTimeout(() => dispatch({ type: 'clear_previous' }), 1200);
    return () => clearTimeout(t);
  }, [state.previousScene]);

  return state;
}
