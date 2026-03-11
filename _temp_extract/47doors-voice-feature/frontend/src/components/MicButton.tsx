/**
 * Microphone toggle button with 6 visual states for voice interaction.
 * Keyboard accessible: Enter to activate, Escape to deactivate.
 */

import { useCallback, KeyboardEvent } from 'react';
import { MicrophoneIcon } from '@heroicons/react/24/solid';
import type { VoiceState } from '../types';

interface MicButtonProps {
  voiceState: VoiceState;
  onToggle: () => void;
  disabled?: boolean;
}

function stateToAriaLabel(state: VoiceState): string {
  switch (state) {
    case 'idle':
      return 'Start voice conversation';
    case 'connecting':
      return 'Connecting to voice service...';
    case 'listening':
      return 'End voice conversation — listening';
    case 'processing':
      return 'End voice conversation — processing your request';
    case 'speaking':
      return 'End voice conversation — agent is speaking';
    case 'error':
      return 'Voice error — click to retry';
    case 'disabled':
      return 'Voice mode unavailable';
    default:
      return 'Voice';
  }
}

function stateToClasses(state: VoiceState): string {
  const base =
    'relative flex items-center justify-center w-9 h-9 rounded-lg transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 ';

  switch (state) {
    case 'idle':
      return base + 'bg-gray-100 text-gray-500 hover:bg-gray-200 focus:ring-gray-400';
    case 'connecting':
      return (
        base +
        'bg-yellow-100 text-yellow-600 animate-pulse focus:ring-yellow-400'
      );
    case 'listening':
      return (
        base +
        'bg-green-100 text-green-600 animate-pulse focus:ring-green-500'
      );
    case 'processing':
      return base + 'bg-blue-100 text-blue-600 focus:ring-blue-500';
    case 'speaking':
      return base + 'bg-green-500 text-white focus:ring-green-600';
    case 'error':
      return base + 'bg-red-100 text-red-600 hover:bg-red-200 focus:ring-red-500';
    case 'disabled':
      return (
        base +
        'bg-gray-50 text-gray-300 cursor-not-allowed opacity-60 focus:ring-gray-300'
      );
    default:
      return base + 'bg-gray-100 text-gray-500';
  }
}

export function MicButton({
  voiceState,
  onToggle,
  disabled = false,
}: MicButtonProps) {
  const isDisabled = disabled || voiceState === 'disabled';
  const isActive =
    voiceState === 'listening' ||
    voiceState === 'processing' ||
    voiceState === 'speaking' ||
    voiceState === 'connecting';

  const handleClick = useCallback(() => {
    if (!isDisabled) {
      onToggle();
    }
  }, [isDisabled, onToggle]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLButtonElement>) => {
      if (e.key === 'Escape' && isActive) {
        e.preventDefault();
        onToggle();
      }
      // Enter is handled by default button click
    },
    [isActive, onToggle]
  );

  return (
    <button
      type="button"
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      disabled={isDisabled}
      aria-label={stateToAriaLabel(voiceState)}
      aria-pressed={isActive}
      title={stateToAriaLabel(voiceState)}
      className={stateToClasses(voiceState)}
    >
      {/* Spinner overlay for processing state */}
      {voiceState === 'processing' && (
        <span className="absolute inset-0 flex items-center justify-center">
          <svg
            className="animate-spin h-4 w-4 text-blue-600"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            />
          </svg>
        </span>
      )}
      <MicrophoneIcon className="w-5 h-5" aria-hidden="true" />
    </button>
  );
}
