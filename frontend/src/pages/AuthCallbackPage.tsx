import { useEffect, useState } from "react";
import { fetchCurrentUser } from "../api/client";
import { hasAccountBefore, markHasAccount, setWelcomePending } from "../auth/flags";
import { saveSession } from "../auth/storage";
import { useAuth } from "../context/AuthContext";
import { AuthTokens } from "../types";

export function AuthCallbackPage() {
  const { completeOAuthLogin } = useAuth();
  const [message, setMessage] = useState("Completing sign in...");

  useEffect(() => {
    const finalize = async () => {
      const params = new URLSearchParams(window.location.search);
      const error = params.get("error");
      const accessToken = params.get("access_token");
      const refreshToken = params.get("refresh_token");
      const expiresIn = params.get("expires_in");

      if (error) {
        setMessage("Sign in failed. Redirecting to login...");
        window.setTimeout(() => {
          window.history.replaceState({}, "", "/");
          window.location.href = "/";
        }, 1500);
        return;
      }

      if (!accessToken || !refreshToken || !expiresIn) {
        setMessage("Invalid authentication response.");
        return;
      }

      const tokens: AuthTokens = {
        access_token: accessToken,
        refresh_token: refreshToken,
        token_type: params.get("token_type") || "bearer",
        expires_in: Number(expiresIn),
        user: {
          id: "",
          email: "",
          full_name: "",
          provider: "oauth",
        },
      };

      saveSession(tokens);

      try {
        const user = await fetchCurrentUser();
        const fullTokens = { ...tokens, user };
        saveSession(fullTokens);
        const returning = hasAccountBefore();
        markHasAccount();
        setWelcomePending(returning);
        completeOAuthLogin(fullTokens);
        window.history.replaceState({}, "", "/");
      } catch {
        setMessage("Could not complete sign in. Redirecting...");
        window.setTimeout(() => {
          window.history.replaceState({}, "", "/");
          window.location.href = "/";
        }, 1500);
      }
    };

    void finalize();
  }, [completeOAuthLogin]);

  return (
    <div className="auth-page">
      <div className="auth-card callback-card">
        <p>{message}</p>
      </div>
    </div>
  );
}
