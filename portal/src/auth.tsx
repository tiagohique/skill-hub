import { createContext, useCallback, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";
import * as api from "./api";
import { useTheme } from "./ThemeContext";
import type { User } from "./types";

type AuthState = "loading" | "anonymous" | "authenticated";

interface AuthValue {
  state: AuthState;
  user: User | null;
  signIn: (username: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  /** Alterna o tema e, logado, guarda a escolha no banco. */
  toggleTheme: () => void;
}

const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const { theme, setTheme } = useTheme();
  const [user, setUser] = useState<User | null>(null);
  const [state, setState] = useState<AuthState>("loading");

  const enter = useCallback(
    (u: User) => {
      setUser(u);
      setState("authenticated");
      setTheme(u.theme);
    },
    [setTheme],
  );
  const leave = useCallback(() => {
    setUser(null);
    setState("anonymous");
  }, []);

  useEffect(() => {
    api.setUnauthorizedHandler(leave);
    api
      .me()
      .then(enter)
      .catch(leave);
    return () => api.setUnauthorizedHandler(null);
  }, [enter, leave]);

  const signIn = useCallback(
    async (username: string, password: string) => {
      enter(await api.login(username, password));
      if (window.location.hash === "#/login") window.location.hash = "#/";
    },
    [enter],
  );

  const signOut = useCallback(async () => {
    try {
      await api.logout();
    } finally {
      leave();
      window.location.hash = "#/";
    }
  }, [leave]);

  const toggleTheme = useCallback(() => {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    if (state === "authenticated") void api.saveTheme(next).catch(() => undefined);
  }, [theme, setTheme, state]);

  return (
    <AuthContext value={{ state, user, signIn, signOut, toggleTheme }}>{children}</AuthContext>
  );
}

export function useAuth(): AuthValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth fora do AuthProvider");
  return value;
}
