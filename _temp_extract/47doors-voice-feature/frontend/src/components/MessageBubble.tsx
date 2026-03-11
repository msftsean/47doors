/**
 * Chat message bubble component.
 */

import { TicketCard } from './TicketCard';
import { KnowledgeArticleList } from './KnowledgeArticleList';
import { SpeakerWaveIcon } from '@heroicons/react/24/solid';
import type { Message, VoiceMessage } from '../types';

interface MessageBubbleProps {
  message: Message | VoiceMessage;
}

function isVoiceMessage(msg: Message | VoiceMessage): msg is VoiceMessage {
  return 'modality' in msg && (msg as VoiceMessage).modality === 'voice';
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const isError = message.status === 'error';
  const isVoice = isVoiceMessage(message);

  return (
    <div
      className={`message-bubble flex ${isUser ? 'justify-end' : 'justify-start'}`}
      role="article"
      aria-label={`${isUser ? 'You' : 'Support agent'} said${isVoice ? ' via voice' : ''}`}
    >
      <div
        className={`max-w-[85%] md:max-w-[75%] ${
          isUser
            ? 'bg-primary-600 text-white rounded-2xl rounded-br-md'
            : isError
            ? 'bg-error-50 text-error-900 border border-error-200 rounded-2xl rounded-bl-md'
            : 'bg-white border border-gray-200 rounded-2xl rounded-bl-md shadow-sm'
        } px-4 py-3`}
      >
        {/* Message content */}
        <p className="text-sm whitespace-pre-wrap">{message.content}</p>

        {/* Ticket card (if ticket was created) */}
        {message.ticketId && (
          <div className="mt-3">
            <TicketCard
              ticketId={message.ticketId}
              department={message.department}
              status={message.status}
              estimatedResponseTime={message.estimatedResponseTime}
              escalated={message.escalated}
            />
          </div>
        )}

        {/* Knowledge articles (if any) */}
        {message.knowledgeArticles && message.knowledgeArticles.length > 0 && (
          <div className="mt-3">
            <KnowledgeArticleList articles={message.knowledgeArticles} />
          </div>
        )}

        {/* Timestamp + voice indicator */}
        <div className="mt-2 flex items-center gap-1">
          {isVoice && (
            <SpeakerWaveIcon
              className={`w-3 h-3 ${isUser ? 'text-primary-200' : 'text-gray-400'}`}
              aria-label="Voice message"
              title="Voice message"
            />
          )}
          <p
            className={`text-xs ${
              isUser ? 'text-primary-200' : 'text-gray-400'
            }`}
          >
            {formatTime(message.timestamp)}
          </p>
        </div>
      </div>
    </div>
  );
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  });
}
