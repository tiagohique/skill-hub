import { useEffect, useState } from "react";
import { listSkills } from "../api";
import type { SkillSummary } from "../types";

export function SkillsPage() {
  const [skills, setSkills] = useState<SkillSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listSkills()
      .then(setSkills)
      .catch((e: Error) => setError(e.message));
  }, []);

  return (
    <section>
      <h1>Skills</h1>
      {error && (
        <p role="alert" className="alert">
          {error}
        </p>
      )}
      {!error && skills === null && <p className="muted">Carregando…</p>}
      {skills !== null && skills.length === 0 && (
        <p className="muted">Nenhuma skill publicada ainda.</p>
      )}
      {skills !== null && skills.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Nome</th>
              <th>Domínio</th>
              <th>Stable</th>
              <th>Beta</th>
            </tr>
          </thead>
          <tbody>
            {skills.map((s) => (
              <tr key={s.name}>
                <td>
                  <a href={`#/skills/${encodeURIComponent(s.name)}`}>{s.name}</a>
                </td>
                <td>{s.domain}</td>
                <td>{s.stable ?? "—"}</td>
                <td>{s.beta ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
