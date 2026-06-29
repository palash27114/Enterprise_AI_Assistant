import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  fetchCurrentUser,
  getOAuthLoginUrl,
  loginUser,
  logoutUser,
  registerUser,
} from "../api/client";
import { loadSession, saveSession, StoredSession, clearSession } from "../auth/storage";
import { ApiError, AuthTokens, AuthUser } from "../types";

interface AuthContextValue {
  user: AuthUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => Promise<void>;
  completeOAuthLogin: (tokens: AuthTokens) => void;
  googleLoginUrl: string;
  githubLoginUrl: string;
  error: string | null;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const bootstrap = useCallback(async () => {
    const session = loadSession();
    if (!session) {
      setUser(null);
      setIsLoading(false);
      return;
    }

    try {
      const currentUser = await fetchCurrentUser();
      setUser(currentUser);
    } catch {
      clearSession();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void bootstrap();
  }, [bootstrap]);

  const login = useCallback(async (email: string, password: string) => {
    setError(null);
    try {
      const session = await loginUser(email, password);
      setUser(session.user);
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Login failed.";
      setError(message);
      throw err;
    }
  }, []);

  const register = useCallback(async (email: string, password: string, fullName: string) => {
    setError(null);
    try {
      const session = await registerUser(email, password, fullName);
      setUser(session.user);
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Registration failed.";
      setError(message);
      throw err;
    }
  }, []);

  const logout = useCallback(async () => {
    await logoutUser();
    setUser(null);
    setError(null);
  }, []);

  const completeOAuthLogin = useCallback((tokens: AuthTokens) => {
    const session: StoredSession = saveSession(tokens);
    setUser(session.user);
    setError(null);
  }, []);

  const value = useMemo(
    () => ({
      user,
      isLoading,
      isAuthenticated: Boolean(user),
      login,
      register,
      logout,
      completeOAuthLogin,
      googleLoginUrl: getOAuthLoginUrl("google"),
      githubLoginUrl: getOAuthLoginUrl("github"),
      error,
      clearError: () => setError(null),
    }),
    [user, isLoading, login, register, logout, completeOAuthLogin, error],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
