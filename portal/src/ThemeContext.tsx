import { createContext, useCallback, useContext, useState } from "react";
import type { ReactNode } from "react";
import { applyTheme, initialTheme, otherTheme } from "./theme";
import type { Theme } from "./theme";

interface ThemeValue {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  toggle: () => void;
}

const ThemeContext = createContext<ThemeValue | null>(null);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(initialTheme);

  const setTheme = useCallback((next: Theme) => {
    applyTheme(next);
    setThemeState(next);
  }, []);
  const toggle = useCallback(() => setTheme(otherTheme(theme)), [setTheme, theme]);

  return <ThemeContext value={{ theme, setTheme, toggle }}>{children}</ThemeContext>;
}

export function useTheme(): ThemeValue {
  const value = useContext(ThemeContext);
  if (!value) throw new Error("useTheme fora do ThemeProvider");
  return value;
}
