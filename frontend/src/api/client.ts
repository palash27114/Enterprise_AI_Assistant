import { AgentId, AgentListResponse, ApiError, AskResponse, AuthTokens, AuthUser, ConversationDetail, ConversationSummary, TicketRecord } from "../types";
import {
  clearSession,
  isSessionExpired,
  loadSession,
  saveSession,
  StoredSession,
} from "../auth/storage";

const API_BASE = import.meta.env.VITE_API_URL ?? "";

let refreshPromise: Promise<StoredSession | null> | null = null;

async function parseError(response: Response): Promise<string> {
  let message = "Something went wrong. Please try again.";
  try {
    const data = (await response.json()) as { detail?: string | Array<{ msg?: string }> };
    if (typeof data.detail === "string" && data.detail) {
      message = data.detail;
    } else if (Array.isArray(data.detail) && data.detail[0]?.msg) {
      message = data.detail[0].msg;
    }
  } catch {
    // Use default message.
  }
  return message;
}

async function refreshSession(refreshToken: string): Promise<StoredSession> {
  const response = await fetch(`${API_BASE}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (!response.ok) {
    clearSession();
    throw new ApiError(await parseError(response));
  }

  const tokens = (await response.json()) as AuthTokens;
  return saveSession(tokens);
}

export async function getValidSession(): Promise<StoredSession | null> {
  const session = loadSession();
  if (!session) {
    return null;
  }

  if (!isSessionExpired(session)) {
    return session;
  }

  if (!refreshPromise) {
    refreshPromise = refreshSession(session.refreshToken)
      .catch(() => null)
      .finally(() => {
        refreshPromise = null;
      });
  }

  return refreshPromise;
}

async function authFetch(input: string, init: RequestInit = {}): Promise<Response> {
  const session = await getValidSession();
  if (!session) {
    throw new ApiError("Authentication required. Please log in.");
  }

  const headers = new Headers(init.headers);
  headers.set("Authorization", `Bearer ${session.accessToken}`);

  const response = await fetch(input, { ...init, headers });

  if (response.status !== 401) {
    return response;
  }

  const refreshed = await refreshSession(session.refreshToken).catch(() => null);
  if (!refreshed) {
    clearSession();
    throw new ApiError("Session expired. Please log in again.");
  }

  headers.set("Authorization", `Bearer ${refreshed.accessToken}`);
  return fetch(input, { ...init, headers });
}

export async function registerUser(
  email: string,
  password: string,
  fullName: string,
): Promise<StoredSession> {
  const response = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, full_name: fullName }),
  });

  if (!response.ok) {
    throw new ApiError(await parseError(response));
  }

  return saveSession((await response.json()) as AuthTokens);
}

export async function loginUser(email: string, password: string): Promise<StoredSession> {
  const response = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    throw new ApiError(await parseError(response));
  }

  return saveSession((await response.json()) as AuthTokens);
}

export async function logoutUser(): Promise<void> {
  const session = loadSession();
  if (session) {
    await fetch(`${API_BASE}/auth/logout`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: session.refreshToken }),
    }).catch(() => undefined);
  }
  clearSession();
}

export async function fetchCurrentUser(): Promise<AuthUser> {
  const response = await authFetch(`${API_BASE}/auth/me`);
  if (!response.ok) {
    throw new ApiError(await parseError(response));
  }
  return (await response.json()) as AuthUser;
}

export async function fetchConversations(): Promise<ConversationSummary[]> {
  const response = await authFetch(`${API_BASE}/conversations`);
  if (!response.ok) {
    throw new ApiError(await parseError(response));
  }
  return (await response.json()) as ConversationSummary[];
}

export async function fetchConversation(conversationId: string): Promise<ConversationDetail> {
  const response = await authFetch(`${API_BASE}/conversations/${conversationId}`);
  if (!response.ok) {
    throw new ApiError(await parseError(response));
  }
  return (await response.json()) as ConversationDetail;
}

export async function changePassword(currentPassword: string, newPassword: string): Promise<void> {
  const response = await authFetch(`${API_BASE}/auth/change-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword,
    }),
  });

  if (!response.ok) {
    throw new ApiError(await parseError(response));
  }
}

export interface ForgotPasswordResult {
  message: string;
  reset_url?: string | null;
}

export async function forgotPassword(email: string): Promise<ForgotPasswordResult> {
  const response = await fetch(`${API_BASE}/auth/forgot-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });

  if (!response.ok) {
    throw new ApiError(await parseError(response));
  }

  return (await response.json()) as ForgotPasswordResult;
}

export async function resetPassword(token: string, newPassword: string): Promise<void> {
  const response = await fetch(`${API_BASE}/auth/reset-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token, new_password: newPassword }),
  });

  if (!response.ok) {
    throw new ApiError(await parseError(response));
  }
}

export async function updateTicket(
  ticketId: string,
  updates: { issue?: string; status?: string; priority?: string },
): Promise<TicketRecord> {
  const response = await authFetch(`${API_BASE}/tickets/${ticketId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(updates),
  });

  if (!response.ok) {
    throw new ApiError(await parseError(response));
  }

  return (await response.json()) as TicketRecord;
}

export async function fetchAgents(): Promise<AgentListResponse> {
  const response = await fetch(`${API_BASE}/agents`);
  if (!response.ok) {
    throw new ApiError(await parseError(response));
  }
  return (await response.json()) as AgentListResponse;
}

export async function askQuestion(
  question: string,
  conversationId?: string | null,
  agent?: AgentId | null,
): Promise<AskResponse> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (conversationId) {
    headers["X-Conversation-Id"] = conversationId;
  }

  const body: { question: string; agent?: AgentId } = { question };
  if (agent) {
    body.agent = agent;
  }

  const response = await authFetch(`${API_BASE}/ask`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    throw new ApiError(await parseError(response));
  }

  return (await response.json()) as AskResponse;
}

export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/health`);
    if (!response.ok) {
      return false;
    }
    const data = (await response.json()) as { status?: string; database?: string };
    return data.status === "ok" && data.database === "ok";
  } catch {
    return false;
  }
}

export function getOAuthLoginUrl(provider: "google" | "github"): string {
  return `${API_BASE}/auth/${provider}/login`;
}
