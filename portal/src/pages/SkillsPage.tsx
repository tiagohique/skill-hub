import { AlertCircle, ChevronRight, Filter, Plus, Search, Terminal } from "lucide-react";
import { useEffect, useState } from "react";
import { listSkills } from "../api";
import { Badge } from "../components/Badge";
import { domainsOf, filterSkills } from "../skills";
import type { SkillSummary } from "../types";

const capitalize = (text: string) => text.charAt(0).toUpperCase() + text.slice(1);
const STATUS_FILTERS = ["stable", "beta", "deprecated"] as const;
const detailHref = (name: string) => `#/skills/${encodeURIComponent(name)}`;

export function SkillsPage() {
  const [skills, setSkills] = useState<SkillSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [domainFilter, setDomainFilter] = useState("todos");
  const [statusFilter, setStatusFilter] = useState("todos");

  useEffect(() => {
    listSkills()
      .then(setSkills)
      .catch((e: Error) => setError(e.message));
  }, []);

  const filtered = skills ? filterSkills(skills, search, domainFilter, statusFilter) : [];
  const emptyText = skills?.length === 0 ? "Nenhuma skill publicada ainda." : "Nenhuma skill encontrada.";

  return (
    <div className="animate-fade-in max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-50 tracking-tight">Skills</h1>
          <p className="text-sm text-zinc-500 dark:text-zinc-400 mt-1">Gerencie e versione suas skills de IA.</p>
        </div>
        <a
          href="#/upload"
          className="inline-flex items-center justify-center gap-2 bg-indigo-500 hover:bg-indigo-600 text-white px-4 py-2 rounded-lg font-medium transition-colors focus:ring-2 focus:ring-indigo-500/50 outline-none"
        >
          <Plus size={18} />
          Enviar Skill
        </a>
      </div>

      {error && (
        <div
          role="alert"
          className="p-4 mb-6 rounded-lg flex items-start gap-3 border bg-red-50 dark:bg-red-950/30 border-red-200 dark:border-red-900/50 text-red-700 dark:text-red-400"
        >
          <AlertCircle size={20} className="shrink-0" />
          <p className="text-sm font-medium pt-0.5">{error}</p>
        </div>
      )}

      {!error && skills === null && <p className="text-zinc-500">Carregando…</p>}

      {skills !== null && (
        <>
          {/* Toolbar (Busca e Filtro) */}
          <div className="flex flex-col sm:flex-row gap-4 mb-6">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" size={18} />
              <input
                type="text"
                aria-label="Buscar skills"
                placeholder="Buscar skills..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 text-zinc-900 dark:text-zinc-100 rounded-lg pl-10 pr-4 py-2 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-shadow placeholder:text-zinc-400 dark:placeholder:text-zinc-600"
              />
            </div>
            <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative sm:w-48">
              <Filter className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" size={18} />
              <select
                aria-label="Filtrar por domínio"
                value={domainFilter}
                onChange={(e) => setDomainFilter(e.target.value)}
                className="w-full bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 text-zinc-900 dark:text-zinc-100 rounded-lg pl-10 pr-8 py-2 appearance-none focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-shadow"
              >
                <option value="todos">Todos os domínios</option>
                {domainsOf(skills).map((d) => (
                  <option key={d} value={d}>
                    {capitalize(d)}
                  </option>
                ))}
              </select>
            </div>
            <div className="relative sm:w-48">
              <Filter className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" size={18} />
              <select
                aria-label="Filtrar por status"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 text-zinc-900 dark:text-zinc-100 rounded-lg pl-10 pr-8 py-2 appearance-none focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-shadow"
              >
                <option value="todos">Todos os status</option>
                {STATUS_FILTERS.map((st) => (
                  <option key={st} value={st}>
                    {capitalize(st)}
                  </option>
                ))}
              </select>
            </div>
            </div>
          </div>

          {/* Tabela (Desktop) */}
          <div className="hidden md:block overflow-hidden border border-zinc-200 dark:border-zinc-800 rounded-xl bg-white dark:bg-zinc-900/50 shadow-sm">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900/80">
                  <th className="px-6 py-4 text-xs font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider w-1/3">Nome</th>
                  <th className="px-6 py-4 text-xs font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-4 text-xs font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider">Domínio</th>
                  <th className="px-6 py-4 text-xs font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider">Stable</th>
                  <th className="px-6 py-4 text-xs font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider">Beta</th>
                  <th className="px-6 py-4 text-xs font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider">Descrição</th>
                  <th className="px-6 py-4"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800/50">
                {filtered.map((skill) => (
                  <tr
                    key={skill.name}
                    onClick={() => {
                      window.location.hash = detailHref(skill.name);
                    }}
                    className="hover:bg-zinc-50 dark:hover:bg-zinc-800/30 transition-colors group cursor-pointer"
                  >
                    <td className="px-6 py-4">
                      <a href={detailHref(skill.name)} className="flex items-center gap-3 outline-none">
                        <div className="p-2 bg-zinc-100 dark:bg-zinc-800 rounded-md text-zinc-500 dark:text-zinc-400 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 group-hover:bg-indigo-100 dark:group-hover:bg-indigo-500/10 transition-colors">
                          <Terminal size={16} />
                        </div>
                        <span className="font-medium text-zinc-800 dark:text-zinc-200 group-hover:text-indigo-700 dark:group-hover:text-indigo-300 transition-colors break-all">
                          {skill.name}
                        </span>
                      </a>
                    </td>
                    <td className="px-6 py-4">
                      <Badge type={skill.status}>{skill.status}</Badge>
                    </td>
                    <td className="px-6 py-4">
                      <Badge type="domain">{skill.domain}</Badge>
                    </td>
                    <td className="px-6 py-4">
                      <Badge type="stable">{skill.stable}</Badge>
                    </td>
                    <td className="px-6 py-4">
                      <Badge type="beta">{skill.beta}</Badge>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-sm text-zinc-500 dark:text-zinc-400 truncate max-w-[200px] block" title={skill.description}>
                        {skill.description}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <ChevronRight
                        size={18}
                        className="text-zinc-400 dark:text-zinc-600 group-hover:text-zinc-700 dark:group-hover:text-zinc-300 inline-block opacity-0 group-hover:opacity-100 transition-all transform group-hover:translate-x-1"
                      />
                    </td>
                  </tr>
                ))}
                {filtered.length === 0 && (
                  <tr>
                    <td colSpan={7} className="px-6 py-12 text-center text-zinc-500">
                      {emptyText}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Lista de Cards (Mobile) */}
          <div className="grid grid-cols-1 gap-4 md:hidden">
            {filtered.map((skill) => (
              <a
                key={skill.name}
                href={detailHref(skill.name)}
                className="block bg-white dark:bg-zinc-900/50 border border-zinc-200 dark:border-zinc-800 rounded-xl p-4 active:bg-zinc-100 dark:active:bg-zinc-800/50 transition-colors"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2 min-w-0">
                    <Terminal size={18} className="text-zinc-500 shrink-0" />
                    <span className="font-medium text-zinc-800 dark:text-zinc-200 break-all">{skill.name}</span>
                  </div>
                  <Badge type={skill.status}>{skill.status}</Badge>
                </div>
                <p className="text-sm text-zinc-500 dark:text-zinc-400 mb-4 line-clamp-2">{skill.description}</p>
                <div className="flex flex-wrap gap-x-6 gap-y-3 border-t border-zinc-100 dark:border-zinc-800/50 pt-3 text-sm">
                  <div>
                    <span className="block text-xs text-zinc-500 mb-1 uppercase tracking-wider">Domínio</span>
                    <Badge type="domain">{skill.domain}</Badge>
                  </div>
                  <div>
                    <span className="block text-xs text-zinc-500 mb-1 uppercase tracking-wider">Stable</span>
                    <Badge type="stable">{skill.stable}</Badge>
                  </div>
                  <div>
                    <span className="block text-xs text-zinc-500 mb-1 uppercase tracking-wider">Beta</span>
                    <Badge type="beta">{skill.beta}</Badge>
                  </div>
                </div>
              </a>
            ))}
            {filtered.length === 0 && (
              <div className="py-8 text-center text-zinc-500 border border-zinc-200 dark:border-zinc-800 rounded-xl bg-white dark:bg-zinc-900/50">
                {emptyText}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
