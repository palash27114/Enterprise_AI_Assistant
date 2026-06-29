import { AgentId, AgentInfo } from "../types";

const SWAGGER_URL = `${import.meta.env.VITE_API_URL ?? ""}/docs`;

interface HeaderProps {
  isOnline: boolean;
  userName: string;
  agents: AgentInfo[];
  selectedAgent: AgentId;
  agentsReady: boolean;
  onAgentChange: (agent: AgentId) => void;
  onLogout: () => void;
}

export function Header({
  isOnline,
  userName,
  agents,
  selectedAgent,
  agentsReady,
  onAgentChange,
  onLogout,
}: HeaderProps) {
  const selectedInfo = agents.find((agent) => agent.id === selectedAgent);
  const initials = userName
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <header className="app-header">
      <div className="header-main">
        <div className="brand">
          <div className="brand-icon" aria-hidden="true">
            EA
          </div>
          <div>
            <p className="brand-eyebrow">Enterprise Platform</p>
            <h1>AI Assistant</h1>
          </div>
        </div>

        <div className="header-toolbar">
          <div className="toolbar-group agent-group">
            <span className="toolbar-label">AI Agent</span>
            <div className="agent-switch" role="group" aria-label="Select AI agent">
              {agents.map((agent) => {
                const disabled = !agent.available || !agentsReady;
                const isActive = selectedAgent === agent.id;

                return (
                  <button
                    key={agent.id}
                    type="button"
                    className={`agent-option ${isActive ? "active" : ""}`}
                    disabled={disabled}
                    onClick={() => onAgentChange(agent.id)}
                    title={
                      !agent.available
                        ? "Not configured"
                        : agent.healthy
                          ? `${agent.name} · ${agent.model}`
                          : `${agent.name} unavailable — check API quota or billing`
                    }
                  >
                    <span className="agent-option-name">{agent.name}</span>
                    {agent.available && (
                      <span className={`agent-status-dot ${agent.healthy ? "healthy" : "unhealthy"}`} />
                    )}
                  </button>
                );
              })}
            </div>
            {selectedInfo && (
              <span className="model-tag">{selectedInfo.model}</span>
            )}
          </div>

          <div className="toolbar-group">
            <span className={`status-pill ${isOnline ? "online" : "offline"}`}>
              <span className="status-dot" />
              {isOnline ? "Connected" : "Offline"}
            </span>
            <a href={SWAGGER_URL} target="_blank" rel="noreferrer" className="ghost-button link-button">
              Swagger
            </a>
          </div>
        </div>
      </div>

      <div className="header-user">
        <div className="user-chip">
          <span className="user-avatar">{initials}</span>
          <div>
            <p className="user-name">{userName}</p>
            <p className="user-role">Workspace member</p>
          </div>
        </div>
        <button type="button" className="logout-button" onClick={onLogout}>
          Sign out
        </button>
      </div>
    </header>
  );
}
