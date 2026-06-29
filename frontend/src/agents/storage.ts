export type AgentId = "openai" | "gemini";

const STORAGE_KEY = "ea_selected_agent";

export function loadSelectedAgent(): AgentId | null {
  const value = localStorage.getItem(STORAGE_KEY);
  if (value === "openai" || value === "gemini") {
    return value;
  }
  return null;
}

export function saveSelectedAgent(agent: AgentId): void {
  localStorage.setItem(STORAGE_KEY, agent);
}
