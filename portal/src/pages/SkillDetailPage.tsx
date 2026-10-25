import { useCallback, useEffect, useState } from "react";
import { deprecate, getSkill, getVersion, promote } from "../api";
import type { Channel, SkillDetail, Status, VersionDetail } from "../types";

interface Props {
  name: string;
}

const dateFormat = new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" });

function StatusBadge({ status }: { status: Status }) {
  return <span className={`badge badge-${status}`}>{status}</span>;
}

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
      setTimeout(() => setCopied(null), 1500);
    } catch {
      // sem permissão de área de transferência: ignora
    }
  }

  if (!skill) {
    return error ? (
      <>
        <p role="alert" className="alert">
          {error}
        </p>
        <a href="#/">← Voltar para as skills</a>
      </>
    ) : (
      <p className="muted">Carregando…</p>
    );
  }

  const current = skill.versions.find((v) => v.version === selected);
  const actions = current ? actionsFor(current.status) : { canDeprecate: false };

  return (
    <section>
      <p>
        <a href="#/">← Skills</a>
      </p>
      <h1>{skill.name}</h1>
      <p>{skill.description}</p>
      <p className="muted">
        Domínio: {skill.domain} · Responsável: {skill.owner} · Stable: {skill.channels.stable ?? "—"} ·
        Beta: {skill.channels.beta ?? "—"}
      </p>

      {error && (
        <p role="alert" className="alert">
          {error}
        </p>
      )}

      <h2>Versões</h2>
      <table>
        <thead>
          <tr>
            <th>Versão</th>
            <th>Status</th>
            <th>Autor</th>
            <th>Criada em</th>
          </tr>
        </thead>
        <tbody>
          {skill.versions.map((v) => (
            <tr
              key={v.version}
              className={v.version === selected ? "selected" : undefined}
              onClick={() => setSelected(v.version)}
              style={{ cursor: "pointer" }}
            >
              <td>{v.version}</td>
              <td>
                <StatusBadge status={v.status} />
              </td>
              <td>{v.created_by}</td>
              <td>{dateFormat.format(new Date(v.created_at))}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {current && (
        <div className="panel">
          <h2>
            Versão {current.version} <StatusBadge status={current.status} />
          </h2>
          <div className="actions">
            {actions.promoteTo && (
              <button
                disabled={busy}
                onClick={() => run(() => promote(name, current.version, actions.promoteTo!))}
              >
                Promover para {actions.promoteTo}
              </button>
            )}
            {actions.canDeprecate && (
              <button
                className="danger"
                disabled={busy}
                onClick={() => {
                  if (window.confirm(`Depreciar a versão ${current.version} de ${name}?`)) {
                    void run(() => deprecate(name, current.version));
                  }
                }}
              >
                Depreciar
              </button>
            )}
          </div>

          <p className="muted">
            Hash do pacote:{" "}
            <button className="link mono" onClick={() => copy(current.bundle_sha256)}>
              {current.bundle_sha256}
            </button>
            {copied === current.bundle_sha256 && " (copiado)"}
          </p>

          {version && version.version === current.version && (
            <table>
              <thead>
                <tr>
                  <th>Arquivo</th>
                  <th>Tamanho</th>
                  <th>SHA-256</th>
                </tr>
              </thead>
              <tbody>
                {version.files.map((f) => (
                  <tr key={f.path}>
                    <td>{f.path}</td>
                    <td>{formatSize(f.size)}</td>
                    <td>
                      <button className="link mono" title="Copiar" onClick={() => copy(f.sha256)}>
                        {f.sha256}
                      </button>
                      {copied === f.sha256 && " (copiado)"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </section>
  );
}
