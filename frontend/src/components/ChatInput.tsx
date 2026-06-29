import type { KeyboardEvent } from "react";

interface ChatInputProps {
  value: string;
  disabled: boolean;
  onChange: (value: string) => void;
  onSubmit: () => void;
}

export function ChatInput({ value, disabled, onChange, onSubmit }: ChatInputProps) {
  const remaining = 1000 - value.length;

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (!disabled && value.trim()) {
        onSubmit();
      }
    }
  };

  return (
    <div className="chat-input-panel">
      <div className="chat-input-wrapper">
        <textarea
          value={value}
          onChange={(event) => onChange(event.target.value.slice(0, 1000))}
          onKeyDown={handleKeyDown}
          placeholder="Ask me anything about HR, IT, policies, your account, or report an issue..."
          rows={3}
          disabled={disabled}
          aria-label="Message input"
        />
        <div className="input-footer">
          <span className={`char-count ${remaining < 100 ? "warning" : ""}`}>
            {remaining} characters left
          </span>
          <button type="button" onClick={onSubmit} disabled={disabled || !value.trim()}>
            {disabled ? "Sending..." : "Send"}
          </button>
        </div>
      </div>
      <p className="input-hint">Press Enter to send · Shift+Enter for a new line</p>
    </div>
  );
}
