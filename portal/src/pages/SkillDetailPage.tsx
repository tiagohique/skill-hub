import { AlertCircle, Check, ChevronRight, Copy, Loader2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { deprecate, getSkill, getVersion, promote } from "../api";
import { Badge } from "../components/Badge";
import type { Channel, SkillDetail, Status, VersionDetail } from "../types";

interface Props {
  name: string;
}

const dateFormat = new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" });

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  return `${(bytes / 1024).toFixed(1)} KB`;
}

/** Ações permitidas por status, espelhando o ciclo de vida do hub. */
function actionsFor(status: Status): { promoteTo?: Channel; canDeprecate: boolean } {
  switch (status) {
    case "draft":
      return { promoteTo: "beta", canDeprecate: false };
    case "beta":
      return { promoteTo: "stable", canDeprecate: true };
    case "stable":
      return { canDeprecate: true };
    default:
      return { canDeprecate: false };
  }
}

function Alert({ message }: { message: string }) {
  return (
    <div
      role="alert"
      className="p-4 mb-6 rounded-lg flex items-start gap-3 border bg-red-50 dark:bg-red-950/30 border-red-200 dark:border-red-900/50 text-red-700 dark:text-red-400"
    >
      <AlertCircle size={20} className="shrink-0" />
      <p className="text-sm font-medium pt-0.5">{message}</p>
    </div>
  );
}

function CopyHash({
  hash,
  copied,
  onCopy,
  className = "",
}: {
  hash: string;
  copied: boolean;
  onCopy: (hash: string) => void;
  className?: string;
}) {
  return (
    <button
      type="button"
      onClick={() => onCopy(hash)}
      title="Copiar"
      aria-label={`Copiar hash ${hash}`}
      className={`group inline-flex items-start gap-2 text-left font-mono text-xs text-zinc-700 dark:text-zinc-300 hover:text-indigo-700 dark:hover:text-indigo-300 transition-colors outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/50 rounded ${className}`}
    >
      <span className="break-all">{hash}</span>
      {copied ? (
        <Check size={14} className="shrink-0 mt-0.5 text-green-700 dark:text-green-400" />
      ) : (
        <Copy size={14} className="shrink-0 mt-0.5 text-zinc-500 group-hover:text-indigo-700 dark:group-hover:text-indigo-300" />
      )}
    </button>
  );
}

export function SkillDetailPage({ name }: Props) {
  const [skill, setSkill] = useState<SkillDetail | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [version, setVersion] = useState<VersionDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState<string | null>(null);

  const load = useCallback(
    async (keep?: string) => {
      try {
        const detail = await getSkill(name);
        setSkill(detail);
        setSelected((current) => keep ?? current ?? detail.versions[0]?.version ?? null);
      } catch (e) {
        setError((e as Error).message);
      }
    },
    [name],
  );

  useEffect(() => {
    setSkill(null);
    setSelected(null);
    setVersion(null);
    setError(null);
    void load();
  }, [load]);

  useEffect(() => {
    if (!selected) return;
    getVersion(name, selected)
      .then(setVersion)
      .catch((e: Error) => setError(e.message));
  }, [name, selected, skill]);

  async function run(action: () => Promise<unknown>) {
    setBusy(true);
    setError(null);
    try {
      await action();
      await load(selected ?? undefined);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function copy(hash: string) {
    try {
      await navigator.clipboard.writeText(hash);
      setCopied(hash);
      setTimeout(() => setCopied((c) => (c === hash ? null : c)), 1500);
    } catch {
      // sem permissão de área de transferência (ex.: página sem HTTPS): ignora
    }
  }

  const breadcrumb = (
    <nav aria-label="Você está em" className="flex items-center gap-2 text-sm text-zinc-500 mb-6 min-w-0">
      <a href="#/" className="hover:text-zinc-700 dark:hover:text-zinc-300 transition-colors">
        Skills
      </a>
      <ChevronRight size={14} className="shrink-0" />
      <span className="text-zinc-900 dark:text-zinc-100 break-all">{name}</span>
    </nav>
  );

  if (!skill) {
    return (
      <div className="animate-fade-in max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {breadcrumb}
        {error ? <Alert message={error} /> : <p className="text-zinc-500">Carregando…</p>}
      </div>
    );
  }

  const current = skill.versions.find((v) => v.version === selected);
  const actions = current ? actionsFor(current.status) : { canDeprecate: false };

  return (
    <div className="animate-fade-in max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {breadcrumb}

      {/* Cabeçalho da skill */}
      <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl p-6 mb-6">
        <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-50 tracking-tight break-all">{skill.name}</h1>
        <p className="text-sm text-zinc-500 dark:text-zinc-400 mt-2">{skill.description}</p>
        <dl className="flex flex-wrap gap-x-8 gap-y-4 mt-5 text-sm">
          <div>
            <dt className="text-xs text-zinc-500 mb-1 uppercase tracking-wider">Domínio</dt>
            <dd>
              <Badge type="domain">{skill.domain}</Badge>
            </dd>
          </div>
          <div>
            <dt className="text-xs text-zinc-500 mb-1 uppercase tracking-wider">Responsável</dt>
            <dd className="text-zinc-700 dark:text-zinc-300">{skill.owner}</dd>
          </div>
          <div>
            <dt className="text-xs text-zinc-500 mb-1 uppercase tracking-wider">Stable</dt>
            <dd>
              <Badge type="stable">{skill.channels.stable}</Badge>
            </dd>
          </div>
          <div>
            <dt className="text-xs text-zinc-500 mb-1 uppercase tracking-wider">Beta</dt>
            <dd>
              <Badge type="beta">{skill.channels.beta}</Badge>
            </dd>
          </div>
        </dl>
      </div>

      {error && <Alert message={error} />}

      {/* Versões */}
      <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50 mb-3">Versões</h2>

      <div className="hidden md:block overflow-hidden border border-zinc-200 dark:border-zinc-800 rounded-xl bg-white dark:bg-zinc-900/50 shadow-sm">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900/80">
              <th className="px-6 py-4 text-xs font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider">Versão</th>
              <th className="px-6 py-4 text-xs font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider">Status</th>
              <th className="px-6 py-4 text-xs font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider">Autor</th>
              <th className="px-6 py-4 text-xs font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider">Criada em</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800/50">
            {skill.versions.map((v) => (
              <tr
                key={v.version}
                onClick={() => setSelected(v.version)}
                aria-selected={v.version === selected}
                className={`cursor-pointer transition-colors ${
                  v.version === selected ? "bg-indigo-100 dark:bg-indigo-500/10" : "hover:bg-zinc-50 dark:hover:bg-zinc-800/30"
                }`}
              >
                <td className="px-6 py-4">
                  <button
                    type="button"
                    onClick={() => setSelected(v.version)}
                    className="font-medium text-zinc-800 dark:text-zinc-200 outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/50 rounded"
                  >
                    {v.version}
                  </button>
                </td>
                <td className="px-6 py-4">
                  <Badge type={v.status}>{v.status}</Badge>
                </td>
                <td className="px-6 py-4 text-zinc-500 dark:text-zinc-400">{v.created_by}</td>
                <td className="px-6 py-4 text-zinc-500 dark:text-zinc-400">{dateFormat.format(new Date(v.created_at))}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="grid grid-cols-1 gap-3 md:hidden">
        {skill.versions.map((v) => (
          <button
            type="button"
            key={v.version}
            onClick={() => setSelected(v.version)}
            aria-pressed={v.version === selected}
            className={`text-left rounded-xl p-4 border transition-colors ${
              v.version === selected
                ? "border-indigo-500 bg-indigo-100 dark:bg-indigo-500/10"
                : "border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900/50 active:bg-zinc-100 dark:active:bg-zinc-800/50"
            }`}
          >
            <div className="flex items-center justify-between gap-3">
              <span className="font-medium text-zinc-800 dark:text-zinc-200">{v.version}</span>
              <Badge type={v.status}>{v.status}</Badge>
            </div>
            <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-2">
              {v.created_by} · {dateFormat.format(new Date(v.created_at))}
            </p>
          </button>
        ))}
      </div>

      {/* Versão selecionada */}
      {current && (
        <div className="mt-6 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl overflow-hidden shadow-xl">
          <div className="p-6 border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900/50">
            <div className="flex flex-wrap items-center gap-3">
              <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">Versão {current.version}</h2>
              <Badge type={current.status}>{current.status}</Badge>
            </div>
            {(actions.promoteTo || actions.canDeprecate) && (
              <div className="flex flex-col sm:flex-row gap-3 mt-4">
                {actions.promoteTo && (
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => run(() => promote(name, current.version, actions.promoteTo!))}
                    className="inline-flex items-center justify-center gap-2 bg-indigo-500 hover:bg-indigo-600 disabled:bg-zinc-100 dark:disabled:bg-zinc-800 disabled:text-zinc-500 disabled:cursor-not-allowed text-white px-4 py-2.5 rounded-lg font-medium transition-colors focus:ring-2 focus:ring-indigo-500/50 outline-none"
                  >
                    {busy && <Loader2 size={16} className="animate-spin" />}
                    Promover para {actions.promoteTo}
                  </button>
                )}
                {actions.canDeprecate && (
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => {
                      if (window.confirm(`Depreciar a versão ${current.version} de ${name}?`)) {
                        void run(() => deprecate(name, current.version));
                      }
                    }}
                    className="inline-flex items-center justify-center gap-2 border border-red-500/60 text-red-700 dark:text-red-400 hover:bg-red-500/10 disabled:opacity-50 disabled:cursor-not-allowed px-4 py-2.5 rounded-lg font-medium transition-colors focus:ring-2 focus:ring-red-500/40 outline-none"
                  >
                    Depreciar
                  </button>
                )}
              </div>
            )}
          </div>

          <div className="p-6 space-y-6">
            <div>
              <span className="block text-xs text-zinc-500 mb-1 uppercase tracking-wider">
                Hash do pacote
              </span>
              <CopyHash hash={current.bundle_sha256} copied={copied === current.bundle_sha256} onCopy={copy} />
            </div>

            {version && version.version === current.version && (
              <div>
                <span className="block text-xs text-zinc-500 mb-2 uppercase tracking-wider">
                  Arquivos
                </span>
                <div className="hidden md:block overflow-hidden border border-zinc-200 dark:border-zinc-800 rounded-lg">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900/80">
                        <th className="px-4 py-3 text-xs font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider">Arquivo</th>
                        <th className="px-4 py-3 text-xs font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider">Tamanho</th>
                        <th className="px-4 py-3 text-xs font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider">SHA-256</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800/50">
                      {version.files.map((f) => (
                        <tr key={f.path}>
                          <td className="px-4 py-3 text-zinc-800 dark:text-zinc-200 break-all">{f.path}</td>
                          <td className="px-4 py-3 text-zinc-500 dark:text-zinc-400 whitespace-nowrap">{formatSize(f.size)}</td>
                          <td className="px-4 py-3">
                            <CopyHash hash={f.sha256} copied={copied === f.sha256} onCopy={copy} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="grid grid-cols-1 gap-3 md:hidden">
                  {version.files.map((f) => (
                    <div key={f.path} className="border border-zinc-200 dark:border-zinc-800 rounded-lg p-4 bg-white dark:bg-zinc-900/50">
                      <div className="flex items-start justify-between gap-3">
                        <span className="text-zinc-800 dark:text-zinc-200 text-sm font-medium break-all">{f.path}</span>
                        <span className="text-xs text-zinc-500 dark:text-zinc-400 whitespace-nowrap">{formatSize(f.size)}</span>
                      </div>
                      <CopyHash hash={f.sha256} copied={copied === f.sha256} onCopy={copy} className="mt-3" />
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
