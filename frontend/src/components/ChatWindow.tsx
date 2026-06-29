import { useEffect, useRef } from "react";
import { ChatMessage } from "../types";
import { MessageBubble } from "./MessageBubble";

interface ChatWindowProps {
  messages: ChatMessage[];
  isLoading: boolean;
  onSuggestionClick: (text: string) => void;
}

const STARTERS = [
  "What is the leave policy?",
  "What is my name?",
  "How do I reset my VPN password?",
  "My laptop won't start — can you help?",
];

export function ChatWindow({ messages, isLoading, onSuggestionClick }: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  if (messages.length === 0) {
    return (
      <div className="chat-window empty">
        <div className="welcome-panel">
          <div className="welcome-copy">
            <span className="welcome-badge">Enterprise Assistant</span>
            <h2>How can I help you today?</h2>
            <p>
              Ask me anything — HR, IT, policies, or your account. I&apos;ll answer directly
              when I can, and fetch live data from company systems only when you need it.
            </p>
          </div>

          <div className="starter-row">
            {STARTERS.map((starter) => (
              <button
                key={starter}
                type="button"
                className="starter-chip"
                onClick={() => onSuggestionClick(starter)}
              >
                {starter}
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="chat-window">
      <div className="messages-list">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        {isLoading && (
          <div className="message-row assistant">
            <div className="avatar assistant-avatar">AI</div>
            <div className="message-content">
              <div className="bubble assistant-bubble typing">
                <span />
                <span />
                <span />
              </div>
              <p className="typing-label">Assistant is thinking...</p>
            </div>
          </div>
        )}
      </div>
      <div ref={bottomRef} />
    </div>
  );
}
