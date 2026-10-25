import { AlertCircle, Box, Loader2, Lock, LogIn, User } from "lucide-react";
import { useState } from "react";
import type { FormEvent } from "react";
import { useAuth } from "../auth";
import { ThemeToggle } from "../components/ThemeToggle";
import { useTheme } from "../ThemeContext";

const INPUT =
  "w-full bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 text-zinc-900 dark:text-zinc-100 rounded-lg pl-10 pr-4 py-2.5 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-shadow placeholder:text-zinc-400 dark:placeholder:text-zinc-600";

export function LoginPage() {
  const { signIn, toggleTheme } = useAuth();
  const { theme } = useTheme();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password) return;
    setBusy(true);
    setError("");
    try {
      await signIn(username, password);
    } catch (err) {
      setError((err as Error).message);
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-zinc-50 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-50">
      <ThemeToggle
        theme={theme}
        onToggle={toggleTheme}
        className="absolute top-4 right-4 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-sm"
      />
      <div className="w-full max-w-md bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl shadow-xl overflow-hidden animate-slide-up">
        <div className="p-8">
          <div className="flex justify-center mb-8">
            <div className="bg-indigo-100 dark:bg-indigo-500/10 text-indigo-600 dark:text-indigo-500 p-3 rounded-xl">
              <Box size={32} strokeWidth={2.5} />
            </div>
          </div>
          <h1 className="text-2xl font-bold text-center mb-2">Bem-vindo ao Skills Hub</h1>
          <p className="text-center text-zinc-500 dark:text-zinc-400 mb-8 text-sm">
            Faça login para gerenciar suas skills de IA.
          </p>

          <form onSubmit={submit} className="space-y-5" noValidate>
            {error && (
              <div
                role="alert"
                className="p-3 rounded-lg flex items-start gap-3 border bg-red-50 text-red-700 border-red-200 dark:bg-red-950/30 dark:border-red-900/50 dark:text-red-400"
              >
                <AlertCircle size={20} className="shrink-0" />
                <p className="text-sm font-medium pt-0.5">{error}</p>
              </div>
            )}
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1.5">
                Usuário
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" size={18} />
                <input
                  id="username"
                  type="text"
                  autoComplete="username"
                  autoCapitalize="off"
                  autoCorrect="off"
                  spellCheck={false}
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="admin"
                  className={INPUT}
                  required
                />
              </div>
            </div>
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1.5">
                Senha
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" size={18} />
                <input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className={INPUT}
                  required
                />
              </div>
            </div>
            <button
              type="submit"
              disabled={busy}
              className="w-full flex justify-center items-center gap-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60 disabled:cursor-not-allowed text-white px-4 py-2.5 rounded-lg font-medium transition-colors focus:ring-2 focus:ring-indigo-500/50 outline-none mt-2"
            >
              {busy ? <Loader2 size={18} className="animate-spin" /> : <LogIn size={18} />}
              {busy ? "Entrando…" : "Entrar no sistema"}
            </button>
          </form>
        </div>
        <div className="px-8 py-4 bg-zinc-50 dark:bg-zinc-950/50 border-t border-zinc-200 dark:border-zinc-800 text-center">
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            Acesso restrito a desenvolvedores autorizados.
          </p>
        </div>
      </div>
    </div>
  );
}
