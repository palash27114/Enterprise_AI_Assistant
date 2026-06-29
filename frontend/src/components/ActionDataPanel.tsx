import { ActionType, ChatMessage } from "../types";

const ACTION_LABELS: Record<ActionType, string> = {
  ai_response: "AI answer",
  create_ticket: "Ticket created",
  generate_report: "Report generated",
  fetch_employee: "Employee lookup",
  fetch_customer: "Customer lookup",
  get_profile: "Profile",
  query_data: "Data query",
  trigger_workflow: "Workflow triggered",
  error: "Could not respond",
};

function formatKey(key: string): string {
  return key.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function renderValue(value: unknown): string {
  if (value === null || value === undefined) {
    return "—";
  }
  if (typeof value === "object") {
    return JSON.stringify(value, null, 2);
  }
  return String(value);
}

function RecordCard({ title, record }: { title: string; record: Record<string, unknown> }) {
  return (
    <div className="action-card">
      <p className="action-card-title">{title}</p>
      <dl className="action-details">
        {Object.entries(record).map(([key, value]) => (
          <div key={key} className="action-detail-row">
            <dt>{formatKey(key)}</dt>
            <dd>{renderValue(value)}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

function MetricsGrid({ metrics }: { metrics: Record<string, unknown> }) {
  return (
    <div className="metrics-grid">
      {Object.entries(metrics).map(([key, value]) => (
        <div key={key} className="metric-card">
          <span className="metric-label">{formatKey(key)}</span>
          <strong className="metric-value">{renderValue(value)}</strong>
        </div>
      ))}
    </div>
  );
}

function ActionDataPanel({ message }: { message: ChatMessage }) {
  if (!message.action || message.action === "ai_response" || message.action === "error") {
    return null;
  }

  const data = message.data;
  const label = ACTION_LABELS[message.action];
  const metrics =
    data && typeof data.metrics === "object" && data.metrics !== null
      ? (data.metrics as Record<string, unknown>)
      : null;
  const employee =
    data && typeof data.employee === "object" && data.employee !== null
      ? (data.employee as Record<string, unknown>)
      : null;
  const customer =
    data && typeof data.customer === "object" && data.customer !== null
      ? (data.customer as Record<string, unknown>)
      : null;
  const rows = data && Array.isArray(data.rows) ? (data.rows as unknown[]) : null;
  const steps = data && Array.isArray(data.steps) ? (data.steps as string[]) : null;

  return (
    <div className="action-panel">
      <div className="message-meta">
        <span className={`badge action-${message.action}`}>{label}</span>
        {message.status && <span className="meta-text">{message.status}</span>}
        {message.ticketId && <span className="meta-text">{message.ticketId}</span>}
        {message.agent && <span className="badge agent">{message.agent}</span>}
      </div>

      {message.action === "generate_report" && metrics && <MetricsGrid metrics={metrics} />}

      {message.action === "fetch_employee" && employee && (
        <RecordCard title="Employee record" record={employee} />
      )}

      {message.action === "fetch_customer" && customer && (
        <RecordCard title="Customer record" record={customer} />
      )}

      {message.action === "get_profile" && data && (
        <RecordCard title="User profile" record={data} />
      )}

      {message.action === "query_data" && rows && (
        <div className="action-card">
          <p className="action-card-title">
            Query results · {String(data?.source_type ?? "source")} `{String(data?.source_name ?? "")}`
          </p>
          <pre className="action-json">{JSON.stringify(rows, null, 2)}</pre>
        </div>
      )}

      {message.action === "trigger_workflow" && steps && (
        <div className="action-card">
          <p className="action-card-title">{String(data?.name ?? "Workflow")}</p>
          <ol className="workflow-steps">
            {steps.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ol>
        </div>
      )}

      {message.action === "create_ticket" && data && (
        <RecordCard title="Ticket details" record={data} />
      )}
    </div>
  );
}

export { ActionDataPanel, ACTION_LABELS };
