// Espelha os schemas da API REST do hub (hub/src/hub/api/schemas.py).

export type Status = "draft" | "beta" | "stable" | "deprecated" | "retired";
export type Channel = "beta" | "stable";

export interface SkillSummary {
  name: string;
  domain: string;
  owner: string;
  stable: string | null;
  beta: string | null;
}

export interface VersionSummary {
  version: string;
  status: Status;
  bundle_sha256: string;
  created_by: string;
  created_at: string;
}

export interface SkillDetail {
  name: string;
  domain: string;
  owner: string;
  description: string;
  channels: Partial<Record<Channel, string>>;
  versions: VersionSummary[];
}

export interface FileEntry {
  path: string;
  sha256: string;
  size: number;
}

export interface VersionDetail {
  name: string;
  version: string;
  status: Status;
  frontmatter: Record<string, unknown>;
  bundle_sha256: string;
  created_by: string;
  created_at: string;
  files: FileEntry[];
}
