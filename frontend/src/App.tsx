import { useCallback, useEffect, useState } from "react";
import { loadSelectedAgent, saveSelectedAgent } from "./agents/storage";
import {
  askQuestion,
  checkHealth,
  fetchAgents,
  fetchConversation,
  fetchConversations,
} from "./api/client";
import { consumeWelcomePending } from "./auth/flags";
import { ChatInput } from "./components/ChatInput";
import { ChatSidebar } from "./components/ChatSidebar";
import { ChatWindow } from "./components/ChatWindow";
import { Header } from "./components/Header";
import { WelcomeBanner } from "./components/WelcomeBanner";
import { useAuth } from "./context/AuthContext";
import { LoginPage } from "./pages/LoginPage";
import { ResetPasswordPage } from "./pages/ResetPasswordPage";
import { AuthCallbackPage } from "./pages/AuthCallbackPage";
import { AgentId, AgentInfo, ApiError, ChatMessage, ConversationSummary } from "./types";

function createId(): string {
  return crypto.randomUUID();
}

function ChatApp() {
  const { user, logout } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [conversationsLoading, setConversationsLoading] = useState(true);
  const [loadingConversationId, setLoadingConversationId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isOnline, setIsOnline] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<AgentId>("gemini");
  const [agentsReady, setAgentsReady] = useState(false);
  const [welcomeState, setWelcomeState] = useState<{ show: boolean; returning: boolean }>({
    show: false,
    returning: false,
  });

  const displayName = user?.full_name?.trim() || user?.email?.split("@")[0] || "there";

  const refreshConversations = useCallback(async () => {
    try {
      const items = await fetchConversations();
      setConversations(items);
    } catch {
      setConversations([]);
    } finally {
      setConversationsLoading(false);
    }
  }, []);

  useEffect(() => {
    const pending = consumeWelcomePending();
    if (pending.show) {
      setWelcomeState({ show: true, returning: pending.returning });
    }
  }, []);

  useEffect(() => {
    void refreshConversations();
  }, [refreshConversations]);

  useEffect(() => {
    const runHealthCheck = async () => {
      setIsOnline(await checkHealth());
    };

    runHealthCheck();
    const interval = window.setInterval(runHealthCheck, 30000);
    return () => window.clearInterval(interval);
  }, []);

  useEffect(() => {
    const loadAgents = async () => {
      setAgentsReady(false);
      try {
        const data = await fetchAgents();
        setAgents(data.agents);

        const stored = loadSelectedAgent();
        const pickIfUsable = (id: AgentId | null | undefined) =>
          id ? data.agents.find((agent) => agent.id === id && agent.available && agent.healthy) : undefined;

        const defaultAgent = data.agents.find((agent) => agent.is_default && agent.available);

        const resolved =
          pickIfUsable(stored)?.id ??
          pickIfUsable(data.default_agent)?.id ??
          defaultAgent?.id ??
          data.agents.find((agent) => agent.available && agent.healthy)?.id ??
          data.default_agent;

        setSelectedAgent(resolved);
        saveSelectedAgent(resolved);
      } catch {
        setAgents([
          {
            id: "gemini",
            name: "Google Gemini",
            model: "gemini-2.5-flash",
            available: true,
            is_default: true,
            healthy: true,
          },
          {
            id: "openai",
            name: "OpenAI",
            model: "gpt-4o-mini",
            available: true,
            is_default: false,
            healthy: false,
          },
        ]);
        setSelectedAgent("gemini");
      } finally {
        setAgentsReady(true);
      }
    };

    void loadAgents();
  }, []);

  const handleAgentChange = (agent: AgentId) => {
    setSelectedAgent(agent);
    saveSelectedAgent(agent);
  };

  const handleSelectConversation = useCallback(async (id: string) => {
    if (loadingConversationId === id || isLoading) {
      return;
    }

    setError(null);
    setLoadingConversationId(id);

    try {
      const detail = await fetchConversation(id);
      setConversationId(detail.conversation_id);
      setMessages(
        detail.messages.map((message) => ({
          id: createId(),
          role: message.role,
          content: message.content,
        })),
      );
      setWelcomeState((current) => ({ ...current, show: false }));
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : "Could not load this conversation. Please try again.";
      setError(message);
    } finally {
      setLoadingConversationId(null);
    }
  }, [isLoading, loadingConversationId]);

  const sendMessage = useCallback(
    async (question: string) => {
      const trimmed = question.trim();
      if (!trimmed || isLoading || !agentsReady) {
        return;
      }

      setError(null);
      setInput("");
      setWelcomeState((current) => ({ ...current, show: false }));

      const userMessage: ChatMessage = {
        id: createId(),
        role: "user",
        content: trimmed,
      };

      setMessages((current) => [...current, userMessage]);
      setIsLoading(true);

      const agentForRequest = selectedAgent;

      try {
        const response = await askQuestion(trimmed, conversationId, agentForRequest);
        setConversationId(response.conversation_id);

        const assistantMessage: ChatMessage = {
          id: createId(),
          role: "assistant",
          content: response.response,
          action: response.action,
          ticketId: response.ticket_id,
          status: response.status,
          agent: response.agent ?? agentForRequest,
          data: response.data ?? null,
        };

        if (response.action === "error" && response.response.toLowerCase().includes("openai quota")) {
          setSelectedAgent("gemini");
          saveSelectedAgent("gemini");
        }

        setMessages((current) => [...current, assistantMessage]);
        setIsOnline(true);
        void refreshConversations();
      } catch (err) {
        const message =
          err instanceof ApiError
            ? err.message
            : "Unable to reach the assistant. Please try again.";

        setError(message);
        setMessages((current) => [
          ...current,
          {
            id: createId(),
            role: "assistant",
            content: message,
            action: "error",
          },
        ]);
      } finally {
        setIsLoading(false);
      }
    },
    [conversationId, isLoading, selectedAgent, agentsReady, refreshConversations],
  );

  const handleNewChat = () => {
    setMessages([]);
    setConversationId(null);
    setInput("");
    setError(null);
    setWelcomeState((current) => ({ ...current, show: false }));
  };

  return (
    <div className="app-shell with-sidebar">
      <Header
        isOnline={isOnline}
        userName={user?.full_name ?? user?.email ?? "User"}
        userRole={user?.job_title ?? user?.access_role_label ?? "Workspace member"}
        userProvider={user?.provider ?? "local"}
        agents={agents}
        selectedAgent={selectedAgent}
        agentsReady={agentsReady}
        onAgentChange={handleAgentChange}
        onLogout={() => void logout()}
      />
      <div className="app-body">
        <ChatSidebar
          conversations={conversations}
          activeConversationId={conversationId}
          isLoading={conversationsLoading || Boolean(loadingConversationId)}
          onSelectConversation={(id) => void handleSelectConversation(id)}
          onNewChat={handleNewChat}
        />
        <main className="chat-layout">
          {!agentsReady && (
            <div className="system-banner">Checking available AI agents...</div>
          )}
          {welcomeState.show && (
            <WelcomeBanner
              userName={displayName}
              isReturning={welcomeState.returning}
              onDismiss={() => setWelcomeState((current) => ({ ...current, show: false }))}
            />
          )}
          <ChatWindow
            messages={messages}
            isLoading={isLoading}
            onSuggestionClick={(text) => {
              void sendMessage(text);
            }}
          />
          {error && <div className="error-banner">{error}</div>}
          <ChatInput
            value={input}
            disabled={isLoading || !agentsReady || Boolean(loadingConversationId)}
            onChange={setInput}
            onSubmit={() => void sendMessage(input)}
          />
        </main>
      </div>
    </div>
  );
}

export default function App() {
  const { isAuthenticated, isLoading } = useAuth();

  if (window.location.pathname === "/oauth/callback") {
    return <AuthCallbackPage />;
  }

  if (window.location.pathname === "/reset-password") {
    return <ResetPasswordPage />;
  }

  if (isLoading) {
    return (
      <div className="auth-page">
        <div className="auth-card callback-card">
          <p>Loading session...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  return <ChatApp />;
}
