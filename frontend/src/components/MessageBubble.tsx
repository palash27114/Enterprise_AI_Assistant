import { ChatMessage } from "../types";
import { ActionDataPanel } from "./ActionDataPanel";

interface MessageBubbleProps {
  message: ChatMessage;
}

function formatAgent(agent: string): string {
  if (agent === "gemini") {
    return "Google Gemini";
  }
  if (agent === "openai") {
    return "OpenAI";
  }
  return agent;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const isError = message.action === "error";
  const isAiResponse = message.action === "ai_response";

  return (
    <div className={`message-row ${isUser ? "user" : "assistant"}`}>
      <div className={`avatar ${isUser ? "user-avatar-bubble" : "assistant-avatar"}`}>
        {isUser ? "You" : "AI"}
      </div>
      <div className="message-content">
        <div
          className={`bubble ${isUser ? "user-bubble" : "assistant-bubble"} ${
            isError ? "error-bubble" : ""
          }`}
        >
          <p>{message.content}</p>
        </div>
        {!isUser && isAiResponse && message.agent && (
          <div className="message-meta">
            <span className="badge agent">{formatAgent(message.agent)}</span>
          </div>
        )}
        {!isUser && isError && (
          <div className="message-meta">
            <span className="badge error">Could not respond</span>
            {message.agent && <span className="badge agent">{formatAgent(message.agent)}</span>}
          </div>
        )}
        {!isUser && <ActionDataPanel message={message} />}
      </div>
    </div>
  );
}
