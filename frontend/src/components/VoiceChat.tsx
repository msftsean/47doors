/**
 * Voice chat UI component — shown when a voice session is active.
 * Displays audio level indicator, voice state text, and live transcript.
 */

import {} from 'react';
import type { VoiceState, VoiceMessage } from '../types';

interface VoiceChatProps {
  voiceState: VoiceState;
  transcript: VoiceMessage[];
  error: string | null;
}

function stateToStatusText(state: VoiceState): string {
  switch (state) {
    case 'connecting':
      return 'Connecting to voice service...';
    case 'listening':
      return 'Listening...';
    case 'processing':
      return 'Processing your request...';
    case 'speaking':
      return 'Agent is speaking...';
    case 'error':
      return 'Voice connection error';
    default:
      return '';
  }
}

/**
 * Simple animated waveform bars for listening/speaking states.
 */
function VoiceWaveform({ active }: { active: boolean }) {
  return (
    <div
      className="flex items-center gap-0.5 h-6"
      aria-hidden="true"
    >
      {[1, 2, 3, 4, 5].map((i) => (
        <div
          key={i}
          className={`w-1 bg-green-500 rounded-full transition-all ${
            active ? 'animate-bounce' : 'h-1'
          }`}
          style={
            active
              ? {
                  animationDelay: `${(i - 1) * 0.1}s`,
                  height: `${8 + ((i * 7) % 14)}px`,
                }
              : { height: '4px' }
          }
        />
      ))}
    </div>
  );
}

export function VoiceChat({ voiceState, transcript, error }: VoiceChatProps) {
  const isActive =
    voiceState === 'connecting' ||
    voiceState === 'listening' ||
    voiceState === 'processing' ||
    voiceState === 'speaking';

  const statusText = stateToStatusText(voiceState);

  if (!isActive && voiceState !== 'error') return null;

  return (
    <div
      className="border-t border-gray-200 bg-gray-50 px-4 py-3"
      role="region"
      aria-label="Voice conversation"
    >
      {/* ARIA live region for screen reader announcements */}
      <div
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
      >
        {statusText}
      </div>

      <div className="flex items-center gap-3">
        {/* Waveform */}
        <VoiceWaveform
          active={voiceState === 'listening' || voiceState === 'speaking'}
        />

        {/* State text */}
        <span className="text-sm text-gray-600 font-medium">
          {error ? (
            <span className="text-red-600">{error}</span>
          ) : (
            statusText
          )}
        </span>
      </div>

      {/* Live transcript (last few messages) */}
      {transcript.length > 0 && (
        <div className="mt-2 space-y-1 max-h-24 overflow-y-auto">
          {transcript.slice(-4).map((msg) => (
            <p
              key={msg.id}
              className={`text-xs ${
                msg.role === 'user' ? 'text-gray-500' : 'text-gray-700'
              }`}
            >
              <span className="font-medium">
                {msg.role === 'user' ? 'You: ' : 'Agent: '}
              </span>
              {msg.content}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}
