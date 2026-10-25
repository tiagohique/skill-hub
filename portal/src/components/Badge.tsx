import type { ReactNode } from "react";

export type BadgeType = "stable" | "beta" | "draft" | "domain" | "deprecated" | "retired";

const STYLES: Record<BadgeType, string> = {
  stable: "bg-green-100 dark:bg-green-950 text-green-700 dark:text-green-400 border border-green-200 dark:border-green-800/50",
  beta: "bg-yellow-100 dark:bg-yellow-950 text-yellow-700 dark:text-yellow-400 border border-yellow-200 dark:border-yellow-800/50",
  draft: "bg-zinc-100 dark:bg-zinc-800 text-zinc-500 dark:text-zinc-400 border border-zinc-300 dark:border-zinc-700",
  domain: "bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 border border-zinc-300 dark:border-zinc-700",
  deprecated: "bg-red-100 dark:bg-red-950 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-900/50",
  retired: "bg-zinc-100 dark:bg-zinc-900 text-zinc-500 border border-zinc-200 dark:border-zinc-800",
};

/** Sem conteúdo mostra um traço cinza, para o espaço não ficar vazio e confuso. */
export function Badge({ type, children }: { type: BadgeType; children?: ReactNode }) {
  if (!children) return <span className="text-zinc-400 dark:text-zinc-600 font-medium">-</span>;
  return (
    <span className={`px-2 py-0.5 rounded-md text-xs font-medium tracking-wide ${STYLES[type]}`}>
      {children}
    </span>
  );
}
