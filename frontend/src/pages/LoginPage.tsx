import { FormEvent, useEffect, useState } from "react";
import { hasAccountBefore, markHasAccount, setWelcomePending } from "../auth/flags";
import { useAuth } from "../context/AuthContext";

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
  const [mode, setMode] = useState<"login" | "register">("register");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    const returning = hasAccountBefore();
    setIsReturningVisitor(returning);
    setMode(returning ? "login" : "register");
  }, []);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    clearError();
    setIsSubmitting(true);

    try {
      if (mode === "login") {
        await login(email, password);
        markHasAccount();
        setWelcomePending(true);
      } else {
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

  const switchMode = (next: "login" | "register") => {
    clearError();
    setMode(next);
  };

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
            <h2>{mode === "register" ? "Create your account" : "Welcome back"}</h2>
            <p>
              {mode === "register"
                ? "First time here? Register to start chatting with the assistant."
                : "Sign in to continue where you left off."}
            </p>
          </div>

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
              Password
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

          <p className="auth-switch">
            {mode === "register" ? (
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
