import { FormEvent, useEffect, useState } from "react";
import { forgotPassword } from "../api/client";
import { hasAccountBefore, markHasAccount, setWelcomePending } from "../auth/flags";
import { useAuth } from "../context/AuthContext";
import { ApiError } from "../types";

type AuthMode = "login" | "register" | "forgot";

export function LoginPage() {
  const {
    login,
    register,
    googleLoginUrl,
    githubLoginUrl,
    error,
    clearError,
  } = useAuth();

  const [isReturningVisitor, setIsReturningVisitor] = useState(false);
  const [mode, setMode] = useState<AuthMode>("register");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [forgotMessage, setForgotMessage] = useState<string | null>(null);
  const [resetUrl, setResetUrl] = useState<string | null>(null);
  const [forgotError, setForgotError] = useState<string | null>(null);

  useEffect(() => {
    const returning = hasAccountBefore();
    setIsReturningVisitor(returning);
    setMode(returning ? "login" : "register");
  }, []);

  const switchMode = (next: AuthMode) => {
    clearError();
    setForgotMessage(null);
    setResetUrl(null);
    setForgotError(null);
    setMode(next);
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    clearError();
    setIsSubmitting(true);

    try {
      if (mode === "login") {
        await login(email, password);
        markHasAccount();
        setWelcomePending(true);
      } else if (mode === "register") {
        await register(email, password, fullName);
        markHasAccount();
        setWelcomePending(false);
      }
    } catch {
      // Error is handled in context.
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleForgotSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setForgotError(null);
    setForgotMessage(null);
    setResetUrl(null);
    setIsSubmitting(true);

    try {
      const result = await forgotPassword(email);
      setForgotMessage(result.message);
      setResetUrl(result.reset_url ?? null);
    } catch (err) {
      setForgotError(err instanceof ApiError ? err.message : "Could not process request.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const title =
    mode === "register" ? "Create your account" : mode === "forgot" ? "Forgot password?" : "Welcome back";

  const subtitle =
    mode === "register"
      ? "First time here? Register to start chatting with the assistant."
      : mode === "forgot"
        ? "Enter your work email and we will send reset instructions."
        : "Sign in to continue where you left off.";

  return (
    <div className="auth-page split">
      <section className="auth-hero">
        <div className="auth-hero-content">
          <div className="brand-icon hero-icon">EA</div>
          <p className="brand-eyebrow light">Enterprise Platform</p>
          <h1>Your AI assistant for HR, IT, and operations</h1>
          <p className="auth-hero-text">
            Ask questions, pull live employee data, generate reports, and manage support — all in
            one secure workspace.
          </p>
          <ul className="auth-feature-list">
            <li>Natural AI chat with smart tool routing</li>
            <li>Personal chat history saved to your account</li>
            <li>Tickets, reports, and workflows in one place</li>
          </ul>
        </div>
      </section>

      <section className="auth-panel">
        <div className="auth-card modern">
          <div className="auth-panel-header">
            <h2>{title}</h2>
            <p>{subtitle}</p>
          </div>

          {mode !== "forgot" && (
            <>
              <div className="oauth-buttons">
                <a
                  href={googleLoginUrl}
                  className="oauth-button google"
                  onClick={() => {
                    markHasAccount();
                    setWelcomePending(isReturningVisitor);
                  }}
                >
                  Continue with Google
                </a>
                <a
                  href={githubLoginUrl}
                  className="oauth-button github"
                  onClick={() => {
                    markHasAccount();
                    setWelcomePending(isReturningVisitor);
                  }}
                >
                  Continue with GitHub
                </a>
              </div>

              <div className="auth-divider">
                <span>or continue with email</span>
              </div>
            </>
          )}

          {mode === "forgot" ? (
            <form className="auth-form" onSubmit={(event) => void handleForgotSubmit(event)}>
              <label>
                Work email
                <input
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="you@company.com"
                  required
                />
              </label>

              {forgotError && <div className="error-banner">{forgotError}</div>}
              {forgotMessage && <div className="success-banner">{forgotMessage}</div>}
              {resetUrl && (
                <p className="auth-reset-link">
                  Dev reset link:{" "}
                  <a href={resetUrl}>{resetUrl}</a>
                </p>
              )}

              <button type="submit" className="primary-button wide" disabled={isSubmitting}>
                {isSubmitting ? "Sending..." : "Send reset instructions"}
              </button>
            </form>
          ) : (
            <form className="auth-form" onSubmit={handleSubmit}>
              {mode === "register" && (
                <label>
                  Full name
                  <input
                    type="text"
                    value={fullName}
                    onChange={(event) => setFullName(event.target.value)}
                    placeholder="Palash Joshi"
                    required
                  />
                </label>
              )}

              <label>
                Work email
                <input
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="you@company.com"
                  required
                />
              </label>

              <label>
                <span className="password-label-row">
                  Password
                  {mode === "login" && (
                    <button type="button" className="link-button inline" onClick={() => switchMode("forgot")}>
                      Forgot password?
                    </button>
                  )}
                </span>
                <input
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="Minimum 8 characters"
                  minLength={8}
                  required
                />
              </label>

              {error && <div className="error-banner">{error}</div>}

              <button type="submit" className="primary-button wide" disabled={isSubmitting}>
                {isSubmitting
                  ? "Please wait..."
                  : mode === "login"
                    ? "Sign in"
                    : "Create account & start"}
              </button>
            </form>
          )}

          <p className="auth-switch">
            {mode === "forgot" ? (
              <>
                Remember your password?{" "}
                <button type="button" onClick={() => switchMode("login")}>
                  Back to sign in
                </button>
              </>
            ) : mode === "register" ? (
              <>
                Already have an account?{" "}
                <button type="button" onClick={() => switchMode("login")}>
                  Sign in
                </button>
              </>
            ) : (
              <>
                {isReturningVisitor ? "New to the platform?" : "First time visiting?"}{" "}
                <button type="button" onClick={() => switchMode("register")}>
                  Create an account
                </button>
              </>
            )}
          </p>
        </div>
      </section>
    </div>
  );
}
