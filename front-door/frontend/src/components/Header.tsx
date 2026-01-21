/**
 * Header component with accessibility controls.
 */

import { SunIcon, MoonIcon, TrashIcon } from '@heroicons/react/24/outline';

interface HeaderProps {
  highContrast: boolean;
  onToggleHighContrast: () => void;
  onClearChat: () => void;
  onTalkToHuman: () => void;
}

export function Header({
  highContrast,
  onToggleHighContrast,
  onClearChat,
  onTalkToHuman,
}: HeaderProps) {
  return (
    <header
      className="bg-white border-b border-gray-200 px-4 py-3 shadow-sm"
      role="banner"
    >
      <div className="max-w-4xl mx-auto flex items-center justify-between">
        {/* Logo and title */}
        <div className="flex items-center gap-3">
          <div
            className="w-10 h-10 bg-primary-600 rounded-lg flex items-center justify-center"
            aria-hidden="true"
          >
            <svg
              className="w-6 h-6 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
              />
            </svg>
          </div>
          <div>
            <h1 className="text-lg font-semibold text-gray-900">
              University Support
            </h1>
            <p className="text-xs text-gray-500">
              Get help with IT, registration, financial aid, and more
            </p>
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-2">
          {/* High contrast toggle */}
          <button
            onClick={onToggleHighContrast}
            className="p-2 rounded-lg hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
            aria-label={`${highContrast ? 'Disable' : 'Enable'} high contrast mode`}
            aria-pressed={highContrast}
          >
            {highContrast ? (
              <SunIcon className="w-5 h-5 text-gray-600" />
            ) : (
              <MoonIcon className="w-5 h-5 text-gray-600" />
            )}
          </button>

          {/* Clear chat button */}
          <button
            onClick={onClearChat}
            className="p-2 rounded-lg hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
            aria-label="Clear chat history"
          >
            <TrashIcon className="w-5 h-5 text-gray-600" />
          </button>

          {/* Talk to human button */}
          <button
            onClick={onTalkToHuman}
            className="ml-2 px-4 py-2 text-sm font-medium text-primary-600 border border-primary-600 rounded-lg hover:bg-primary-50 focus:outline-none focus:ring-2 focus:ring-primary-500"
            aria-label="Request to speak with a human agent"
          >
            Talk to a Human
          </button>
        </div>
      </div>
    </header>
  );
}
