import { useCallback } from 'react';
import { ChatContainer } from './components/ChatContainer';
import { Header } from './components/Header';
import { useChat } from './hooks/useChat';
import { useHighContrast } from './hooks/useHighContrast';

function App() {
  const [highContrast, toggleHighContrast] = useHighContrast();
  const {
    messages,
    isLoading,
    sessionId,
    sendMessage,
    clearChat,
  } = useChat();

  const handleTalkToHuman = useCallback(() => {
    sendMessage("I need to speak with a human support agent.");
  }, [sendMessage]);

  return (
    <div className={`min-h-screen flex flex-col ${highContrast ? 'high-contrast' : ''}`}>
      {/* Skip link for accessibility */}
      <a
        href="#main-content"
        className="skip-link"
      >
        Skip to main content
      </a>

      <Header
        highContrast={highContrast}
        onToggleHighContrast={toggleHighContrast}
        onClearChat={clearChat}
        onTalkToHuman={handleTalkToHuman}
      />

      <main
        id="main-content"
        className="flex-1 flex flex-col max-w-4xl w-full mx-auto"
        role="main"
        aria-label="Chat with support agent"
      >
        <ChatContainer
          messages={messages}
          isLoading={isLoading}
          sessionId={sessionId}
          onSendMessage={sendMessage}
        />
      </main>
    </div>
  );
}

export default App;
