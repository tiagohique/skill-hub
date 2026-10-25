import { Box, Menu, User, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useAuth } from "../auth";
import { useTheme } from "../ThemeContext";
import { ThemeToggle } from "./ThemeToggle";
import type { ReactNode } from "react";

export type Page = "list" | "upload";

const LINKS: { page: Page; href: string; label: string }[] = [
  { page: "list", href: "#/", label: "Skills" },
  { page: "upload", href: "#/upload", label: "Enviar skill" },
];

// Documentação servida pelo hub (pede a senha da documentação); abre em outra aba.
const DOCS = [
  { href: "/docs", label: "API (Swagger)" },
  { href: "/mcp-docs", label: "MCP" },
];

export function Layout({ active, children }: { active: Page | null; children: ReactNode }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [userOpen, setUserOpen] = useState(false);
  const userMenu = useRef<HTMLDivElement>(null);
  const { theme } = useTheme();
  const { user, signOut, toggleTheme: toggle } = useAuth();

  // Fecha o menu do celular ao navegar e com a tecla Esc.
  useEffect(() => {
    const close = () => {
      setMenuOpen(false);
      setUserOpen(false);
    };
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && close();
    const onClickOutside = (e: MouseEvent) => {
      if (!userMenu.current?.contains(e.target as Node)) setUserOpen(false);
    };
    window.addEventListener("hashchange", close);
    window.addEventListener("keydown", onKey);
    document.addEventListener("mousedown", onClickOutside);
    return () => {
      window.removeEventListener("hashchange", close);
      window.removeEventListener("keydown", onKey);
      document.removeEventListener("mousedown", onClickOutside);
    };
  }, []);

  return (
    <div className="min-h-screen flex flex-col bg-zinc-50 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-50 font-sans selection:bg-indigo-500/30">
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

          <div className="hidden md:flex items-center gap-6 border-l border-zinc-200 dark:border-zinc-800 pl-6 ml-2">
            <ThemeToggle theme={theme} onToggle={toggle} />
            {/* Menu do usuário: o Sair aparece ao passar o mouse, focar ou clicar no ícone */}
            <div ref={userMenu} className="relative group flex flex-col items-center justify-center pt-1">
              <button
                type="button"
                onClick={() => setUserOpen((open) => !open)}
                aria-haspopup="menu"
                aria-expanded={userOpen}
                aria-label={`Menu do usuário ${user?.username ?? ""}`}
                className="flex flex-col items-center cursor-pointer outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/50 rounded-md"
              >
                <span className="bg-zinc-200 dark:bg-zinc-800 rounded-full p-1.5 text-zinc-600 dark:text-zinc-300 group-hover:bg-zinc-300 dark:group-hover:bg-zinc-700 transition-colors">
                  <User size={18} />
                </span>
                <span className="text-[10px] text-zinc-500 mt-0.5 leading-none">{user?.username}</span>
              </button>
              <div
                role="menu"
                className={`absolute top-full right-0 mt-2 w-32 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg shadow-lg transition-all duration-200 z-50 overflow-hidden group-hover:opacity-100 group-hover:visible group-focus-within:opacity-100 group-focus-within:visible ${
                  userOpen ? "opacity-100 visible" : "opacity-0 invisible"
                }`}
              >
                <button
                  type="button"
                  role="menuitem"
                  onClick={() => void signOut()}
                  className="w-full text-left px-4 py-2.5 text-sm font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors outline-none focus-visible:bg-red-50 dark:focus-visible:bg-red-500/10"
                >
                  Sair
                </button>
              </div>
            </div>
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

      <main className="flex-1">{children}</main>

      <footer className="border-t border-zinc-200 dark:border-zinc-800 py-6 mt-8 shrink-0">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex justify-center gap-8">
          {DOCS.map((d) => (
            <a
              key={d.href}
              href={d.href}
              target="_blank"
              rel="noreferrer"
              className="text-xs font-medium text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300 transition-colors outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/50 rounded-md"
            >
              {d.label}
            </a>
          ))}
        </div>
      </footer>
    </div>
  );
}
