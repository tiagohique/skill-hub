import { Box, Menu, X } from "lucide-react";
import { useEffect, useState } from "react";
import { useAuth } from "../auth";
import { useTheme } from "../ThemeContext";
import { ThemeToggle } from "./ThemeToggle";
import type { ReactNode } from "react";

export type Page = "list" | "upload";

const LINKS: { page: Page; href: string; label: string }[] = [
  { page: "list", href: "#/", label: "Skills" },
  { page: "upload", href: "#/upload", label: "Enviar skill" },
];

export function Layout({ active, children }: { active: Page | null; children: ReactNode }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const { theme } = useTheme();
  const { user, signOut, toggleTheme: toggle } = useAuth();

  // Fecha o menu do celular ao navegar e com a tecla Esc.
  useEffect(() => {
    const close = () => setMenuOpen(false);
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && close();
    window.addEventListener("hashchange", close);
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("hashchange", close);
      window.removeEventListener("keydown", onKey);
    };
  }, []);

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-50 font-sans selection:bg-indigo-500/30">
      <header className="sticky top-0 z-50 bg-white/80 dark:bg-zinc-950/80 backdrop-blur-md border-b border-zinc-200 dark:border-zinc-800 h-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-full flex items-center justify-between">
          <a href="#/" className="flex items-center gap-3 outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/50 rounded-md">
            <div className="bg-indigo-100 dark:bg-indigo-500/10 text-indigo-600 dark:text-indigo-500 p-1.5 rounded-md">
              <Box size={22} strokeWidth={2.5} />
            </div>
            <span className="font-semibold text-lg tracking-tight">Skills Hub</span>
          </a>

          <nav className="hidden md:flex items-center gap-1" aria-label="Principal">
            {LINKS.map((l) => (
              <a
                key={l.page}
                href={l.href}
                aria-current={active === l.page ? "page" : undefined}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/50 ${
                  active === l.page
                    ? "bg-zinc-100 dark:bg-zinc-800/50 text-zinc-900 dark:text-zinc-100"
                    : "text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-900"
                }`}
              >
                {l.label}
              </a>
            ))}
          </nav>

          <div className="hidden md:flex items-center gap-4 border-l border-zinc-200 dark:border-zinc-800 pl-4 ml-2">
            <ThemeToggle theme={theme} onToggle={toggle} />
            <span className="text-sm text-zinc-500 dark:text-zinc-400">{user?.username}</span>
            <button
              type="button"
              onClick={() => void signOut()}
              className="text-sm font-medium text-zinc-500 hover:text-red-600 dark:text-zinc-400 dark:hover:text-red-400 transition-colors outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/50 rounded-md min-h-11 px-1"
            >
              Sair
            </button>
          </div>

          <div className="md:hidden flex items-center gap-1">
            <ThemeToggle theme={theme} onToggle={toggle} />
            <button
              type="button"
              onClick={() => setMenuOpen((open) => !open)}
              aria-label={menuOpen ? "Fechar menu" : "Abrir menu"}
              aria-expanded={menuOpen}
              aria-controls="menu-mobile"
              className="size-11 inline-flex items-center justify-center rounded-md text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/50"
            >
              {menuOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>
        </div>
      </header>

      {menuOpen && (
        <div
          id="menu-mobile"
          className="md:hidden fixed top-16 inset-x-0 bg-white dark:bg-zinc-900 border-b border-zinc-200 dark:border-zinc-800 z-40 animate-slide-down"
        >
          <nav className="flex flex-col p-4 gap-2" aria-label="Principal (celular)">
            {LINKS.map((l) => (
              <a
                key={l.page}
                href={l.href}
                aria-current={active === l.page ? "page" : undefined}
                className={`w-full text-left px-4 py-3 min-h-11 rounded-lg text-base font-medium ${
                  active === l.page ? "bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100" : "text-zinc-500 dark:text-zinc-400"
                }`}
              >
                {l.label}
              </a>
            ))}
            <div className="h-px bg-zinc-200 dark:bg-zinc-800 my-2" />
            <button
              type="button"
              onClick={() => void signOut()}
              className="w-full text-left px-4 py-3 min-h-11 rounded-lg text-base font-medium text-red-600 dark:text-red-400"
            >
              Sair{user ? ` (${user.username})` : ""}
            </button>
          </nav>
        </div>
      )}

      <main>{children}</main>
    </div>
  );
}
