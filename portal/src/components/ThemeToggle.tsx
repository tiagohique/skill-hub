import { Moon, Sun } from "lucide-react";
import type { Theme } from "../theme";

/** Mostra o ícone do tema para o qual vai trocar (sol no escuro, lua no claro). */
export function ThemeToggle({
  theme,
  onToggle,
  className = "",
}: {
  theme: Theme;
  onToggle: () => void;
  className?: string;
}) {
  return (
    <button
      type="button"
      onClick={onToggle}
      title="Alternar tema"
      aria-label={theme === "dark" ? "Mudar para o tema claro" : "Mudar para o tema escuro"}
      className={`size-11 inline-flex items-center justify-center rounded-full text-zinc-500 hover:text-indigo-600 dark:text-zinc-400 dark:hover:text-indigo-400 transition-colors outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/50 ${className}`}
    >
      {theme === "dark" ? <Sun size={20} /> : <Moon size={20} />}
    </button>
  );
}
