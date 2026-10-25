import type { SkillSummary } from "./types";

/** Domínios existentes no catálogo, sem repetição e em ordem alfabética. */
export function domainsOf(skills: SkillSummary[]): string[] {
  return [...new Set(skills.map((s) => s.domain))].sort((a, b) => a.localeCompare(b));
}

/** Filtra por nome (parcial, sem diferenciar maiúsculas), domínio e status ("todos" não filtra). */
export function filterSkills(
  skills: SkillSummary[],
  search: string,
  domain: string,
  status = "todos",
): SkillSummary[] {
  const term = search.trim().toLowerCase();
  return skills.filter(
    (s) =>
      (term === "" || s.name.toLowerCase().includes(term)) &&
      (domain === "todos" || s.domain === domain) &&
      (status === "todos" || s.status === status),
  );
}
