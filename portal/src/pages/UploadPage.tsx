import { useRef, useState } from "react";
import type { DragEvent, FormEvent } from "react";
import { uploadSkill } from "../api";
import { explainVersion } from "../version";

const ACCEPTED = /\.(md|zip)$/i;

export function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [version, setVersion] = useState("");
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const input = useRef<HTMLInputElement>(null);

  const check = explainVersion(version);
  const versionValid = check.valid;
  const canSubmit = file !== null && versionValid && !busy;

  function choose(candidate: File | undefined) {
    if (!candidate) return;
    if (!ACCEPTED.test(candidate.name)) {
      setFile(null);
      setError("Envie um arquivo .md (SKILL.md) ou .zip.");
      return;
    }
    setError(null);
    setFile(candidate);
  }

  function onDrop(event: DragEvent) {
    event.preventDefault();
    setDragging(false);
    choose(event.dataTransfer.files[0]);
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!file || !versionValid) return;
    setBusy(true);
    setError(null);
    try {
      const created = await uploadSkill(file, version);
      window.location.hash = `#/skills/${encodeURIComponent(created.name)}`;
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section>
      <h1>Enviar skill</h1>
      <form onSubmit={onSubmit}>
        <div
          className={`dropzone${dragging ? " dragging" : ""}`}
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          onClick={() => input.current?.click()}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") input.current?.click();
          }}
        >
          {file ? (
            <strong>{file.name}</strong>
          ) : (
            <span>Arraste um SKILL.md ou .zip aqui, ou clique para escolher.</span>
          )}
          <input
            ref={input}
            type="file"
            accept=".md,.zip"
            hidden
            onChange={(e) => choose(e.target.files?.[0])}
          />
        </div>

        <label className="field">
          Versão (semver)
          <input
            type="text"
            value={version}
            onChange={(e) => setVersion(e.target.value.trim())}
            placeholder="1.0.0"
            aria-invalid={version !== "" && !versionValid}
          />
        </label>
        <p className="muted hint">
          Exemplo: <code>1.0.0</code> (três números separados por pontos, sem ponto no fim).
        </p>
        {!check.valid && version !== "" && (
          <p role="status" className="field-error">
            {check.message}{" "}
            {check.suggestion && (
              <button
                type="button"
                className="link"
                onClick={() => setVersion(check.suggestion ?? "")}
              >
                Usar {check.suggestion}
              </button>
            )}
          </p>
        )}

        {error && (
          <p role="alert" className="alert">
            {error}
          </p>
        )}

        <button type="submit" disabled={!canSubmit}>
          {busy ? "Enviando…" : "Enviar"}
        </button>
        {!canSubmit && !busy && (
          <p className="muted">
            {file === null
              ? "Escolha um arquivo .md ou .zip para enviar."
              : "Informe uma versão válida para enviar."}
          </p>
        )}
      </form>
    </section>
  );
}
