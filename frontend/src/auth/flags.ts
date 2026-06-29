const HAS_ACCOUNT_KEY = "ea_has_account";
const WELCOME_KEY = "ea_welcome_pending";
const WELCOME_RETURNING_KEY = "ea_welcome_returning";

export function hasAccountBefore(): boolean {
  return localStorage.getItem(HAS_ACCOUNT_KEY) === "true";
}

export function markHasAccount(): void {
  localStorage.setItem(HAS_ACCOUNT_KEY, "true");
}

export function setWelcomePending(returning: boolean): void {
  sessionStorage.setItem(WELCOME_KEY, "true");
  sessionStorage.setItem(WELCOME_RETURNING_KEY, returning ? "true" : "false");
}

export function consumeWelcomePending(): { show: boolean; returning: boolean } {
  const show = sessionStorage.getItem(WELCOME_KEY) === "true";
  const returning = sessionStorage.getItem(WELCOME_RETURNING_KEY) === "true";
  sessionStorage.removeItem(WELCOME_KEY);
  sessionStorage.removeItem(WELCOME_RETURNING_KEY);
  return { show, returning };
}
