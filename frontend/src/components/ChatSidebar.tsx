import { ConversationSummary } from "../types";

interface ChatSidebarProps {
  conversations: ConversationSummary[];
  activeConversationId: string | null;
  isLoading: boolean;
  onSelectConversation: (conversationId: string) => void;
  onNewChat: () => void;
}

function formatWhen(iso: string): string {
  const date = new Date(iso);
  const now = new Date();
  const sameDay =
    date.getFullYear() === now.getFullYear() &&
    date.getMonth() === now.getMonth() &&
    date.getDate() === now.getDate();

  if (sameDay) {
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }
  return date.toLocaleDateString([], { month: "short", day: "numeric" });
}

export function ChatSidebar({
  conversations,
  activeConversationId,
  isLoading,
  onSelectConversation,
  onNewChat,
}: ChatSidebarProps) {
  return (
    <aside className="chat-sidebar">
      <div className="sidebar-header">
        <h2>Your chats</h2>
        <button type="button" className="sidebar-new-button" onClick={onNewChat}>
          + New chat
        </button>
      </div>

      <div className="sidebar-list">
        {isLoading && <p className="sidebar-empty">Loading conversations...</p>}

        {!isLoading && conversations.length === 0 && (
          <p className="sidebar-empty">No chats yet. Start a new conversation.</p>
        )}

        {!isLoading &&
          conversations.map((conversation) => (
            <button
              key={conversation.conversation_id}
              type="button"
              className={`sidebar-item ${
                activeConversationId === conversation.conversation_id ? "active" : ""
              }`}
              onClick={() => onSelectConversation(conversation.conversation_id)}
            >
              <span className="sidebar-item-title">{conversation.title}</span>
              <span className="sidebar-item-preview">{conversation.preview}</span>
              <span className="sidebar-item-meta">
                {formatWhen(conversation.updated_at)} · {conversation.message_count} messages
              </span>
            </button>
          ))}
      </div>
    </aside>
  );
}
