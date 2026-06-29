export type MessageRole = "user" | "assistant";

export type ActionType =
  | "ai_response"
  | "create_ticket"
  | "generate_report"
  | "fetch_employee"
  | "fetch_customer"
  | "get_profile"
  | "query_data"
  | "trigger_workflow"
  | "error";

export type AgentId = "openai" | "gemini";

export interface AgentInfo {
  id: AgentId;
  name: string;
  model: string;
  available: boolean;
  is_default: boolean;
  healthy: boolean;
}

export interface AgentListResponse {
  default_agent: AgentId;
  agents: AgentInfo[];
}

export interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  provider: string;
  employee_id?: string | null;
  job_title?: string | null;
  access_role?: string | null;
  access_role_label?: string | null;
}

export interface TicketRecord {
  id: string;
  issue: string;
  status: string;
  priority?: string | null;
  created_at: string;
  updated_at?: string | null;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: AuthUser;
}

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  action?: ActionType;
  ticketId?: string | null;
  status?: string | null;
  agent?: AgentId | null;
  data?: Record<string, unknown> | null;
}

export interface AskResponse {
  response: string;
  action: ActionType;
  ticket_id: string | null;
  conversation_id: string;
  status: string | null;
  agent?: AgentId | null;
  data?: Record<string, unknown> | null;
}

export interface ConversationSummary {
  conversation_id: string;
  title: string;
  preview: string;
  message_count: number;
  updated_at: string;
}

export interface ConversationDetail {
  conversation_id: string;
  title: string;
  updated_at: string;
  messages: Array<{ role: MessageRole; content: string }>;
}

export class ApiError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ApiError";
  }
}
