import {
  AlertCircle,
  CheckCircle2,
  ChevronRight,
  FileCheck2,
  Loader2,
  UploadCloud,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { ChangeEvent, DragEvent, FormEvent, KeyboardEvent, MouseEvent } from "react";
import { uploadSkill } from "../api";
import { explainVersion } from "../version";

const ACCEPTED = /\.(md|zip)$/i;

interface Status {
  type: "" | "error" | "success";
  message: string;
}

export function UploadPage() {
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [version, setVersion] = useState("");
  const [status, setStatus] = useState<Status>({ type: "", message: "" });
  const [busy, setBusy] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const redirect = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  useEffect(() => () => clearTimeout(redirect.current), []);

  const check = explainVersion(version);
  const canSubmit = file !== null && check.valid && !busy;

  const handleDrag = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") setDragActive(true);
    else if (e.type === "dragleave") setDragActive(false);
  };

  const handleFileSelection = (selected: File) => {
    if (ACCEPTED.test(selected.name)) {
      setFile(selected);
      setStatus({ type: "", message: "" });
    } else {
      setFile(null);
      setStatus({ type: "error", message: "Formato inválido. Use apenas .zip ou .md." });
    }
  };

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) handleFileSelection(dropped);
  };

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const chosen = e.target.files?.[0];
    if (chosen) handleFileSelection(chosen);
    e.target.value = ""; // permite escolher o mesmo arquivo de novo
  };

  const openPicker = () => inputRef.current?.click();
  const onZoneKey = (e: KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      openPicker();
    }
  };

  const clearFile = (e: MouseEvent) => {
    e.stopPropagation();
    setFile(null);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!file) {
      setStatus({ type: "error", message: "Selecione um arquivo para enviar." });
      return;
    }
    if (!check.valid) {
      setStatus({ type: "error", message: check.message });
      return;
    }
    setBusy(true);
    setStatus({ type: "", message: "" });
    try {
      await uploadSkill(file, version);
      setStatus({
        type: "success",
        message: "Skill enviada com sucesso! Entrando no canal draft.",
      });
      redirect.current = setTimeout(() => {
        window.location.hash = "#/";
      }, 2000);
    } catch (err) {
      setStatus({ type: "error", message: (err as Error).message });
    } finally {
      setBusy(false);
    }
  };

  const versionInvalid = version !== "" && !check.valid;

  return (
    <div className="animate-slide-up max-w-2xl mx-auto px-4 py-8">
      {/* Breadcrumb simples */}
      <nav aria-label="Você está em" className="flex items-center gap-2 text-sm text-zinc-500 mb-6">
        <a href="#/" className="hover:text-zinc-300 transition-colors">
          Skills
        </a>
        <ChevronRight size={14} />
        <span className="text-zinc-100">Enviar Nova</span>
      </nav>

      <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden shadow-xl">
        <div className="p-6 border-b border-zinc-800 bg-zinc-900/50">
          <h1 className="text-xl font-semibold text-zinc-50">Enviar nova Skill</h1>
          <p className="text-sm text-zinc-400 mt-1">
            Faça o upload do seu pacote (.zip) ou manifesto (.md) para iniciar o versionamento como
            rascunho (draft).
          </p>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6" noValidate>
          {/* Alertas */}
          {status.message && (
            <div
              role="alert"
              className={`p-4 rounded-lg flex items-start gap-3 border ${
                status.type === "error"
                  ? "bg-red-950/30 border-red-900/50 text-red-400"
                  : "bg-green-950/30 border-green-900/50 text-green-400"
              }`}
            >
              {status.type === "error" ? (
                <AlertCircle size={20} className="shrink-0" />
              ) : (
                <CheckCircle2 size={20} className="shrink-0" />
              )}
              <p className="text-sm font-medium pt-0.5">{status.message}</p>
            </div>
          )}

          {/* Dropzone */}
          <div>
            <span className="block text-sm font-medium text-zinc-300 mb-2">Arquivo da Skill</span>
            <div
              role="button"
              tabIndex={0}
              aria-label="Escolher arquivo da skill"
              className={`relative flex flex-col items-center justify-center min-h-40 p-8 border-2 border-dashed rounded-xl transition-all duration-200 group cursor-pointer outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/50 ${
                dragActive
                  ? "border-indigo-500 border-solid bg-indigo-500/10"
                  : file
                    ? "border-zinc-700 bg-zinc-800/50"
                    : "border-zinc-700 hover:border-zinc-500 hover:bg-zinc-800/30"
              }`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={openPicker}
              onKeyDown={onZoneKey}
            >
              <input
                ref={inputRef}
                type="file"
                accept=".md,.zip"
                className="hidden"
                onChange={handleChange}
              />

              {file ? (
                <div className="flex flex-col items-center text-center max-w-full">
                  <div className="w-12 h-12 bg-indigo-500/20 text-indigo-400 rounded-full flex items-center justify-center mb-3">
                    <FileCheck2 size={24} />
                  </div>
                  <p className="text-zinc-200 font-medium break-all">{file.name}</p>
                  <p className="text-zinc-500 text-xs mt-1">{(file.size / 1024).toFixed(2)} KB</p>
                  <button
                    type="button"
                    onClick={clearFile}
                    className="text-xs text-indigo-400 mt-4 hover:text-indigo-300 min-h-8 px-2"
                  >
                    Trocar arquivo
                  </button>
                </div>
              ) : (
                <div className="flex flex-col items-center text-center pointer-events-none">
                  <div className="w-12 h-12 bg-zinc-800 text-zinc-400 rounded-full flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                    <UploadCloud size={24} />
                  </div>
                  <p className="text-zinc-300 font-medium">
                    Arraste o arquivo ou clique para selecionar
                  </p>
                  <p className="text-zinc-500 text-xs mt-1">
                    Apenas arquivos .md ou .zip (Máx: 5MB)
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Versão SemVer */}
          <div>
            <label htmlFor="version" className="block text-sm font-medium text-zinc-300 mb-1">
              Versão (SemVer)
            </label>
            <input
              id="version"
              type="text"
              inputMode="text"
              autoCapitalize="off"
              autoCorrect="off"
              spellCheck={false}
              placeholder="ex: 1.0.0"
              value={version}
              onChange={(e) => setVersion(e.target.value.trim())}
              aria-invalid={versionInvalid}
              aria-describedby="version-help"
              className={`w-full bg-zinc-950 border text-zinc-100 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-1 transition-shadow placeholder:text-zinc-700 ${
                versionInvalid
                  ? "border-red-500/70 focus:border-red-500 focus:ring-red-500"
                  : "border-zinc-800 focus:border-indigo-500 focus:ring-indigo-500"
              }`}
            />
            {!check.valid && version !== "" && (
              <p role="status" className="text-sm text-red-400 mt-2">
                {check.message}{" "}
                {check.suggestion && (
                  <button
                    type="button"
                    onClick={() => setVersion(check.suggestion ?? "")}
                    className="text-indigo-400 hover:text-indigo-300 font-medium underline underline-offset-2 min-h-8"
                  >
                    Usar {check.suggestion}
                  </button>
                )}
              </p>
            )}
            <p id="version-help" className="text-xs text-zinc-400 mt-2">
              Três números separados por pontos, sem ponto no fim (ex:{" "}
              <code className="text-zinc-300">1.0.0</code>). Se o manifesto já contiver a versão,
              elas devem coincidir.
            </p>
          </div>

          <div className="pt-4 border-t border-zinc-800 flex flex-col-reverse sm:flex-row sm:items-center sm:justify-between gap-3">
            <p className="text-xs text-zinc-400">
              {canSubmit || busy
                ? ""
                : file === null
                  ? "Escolha um arquivo .md ou .zip para enviar."
                  : "Informe uma versão válida para enviar."}
            </p>
            <button
              type="submit"
              disabled={!canSubmit}
              className="w-full sm:w-auto flex justify-center items-center gap-2 bg-indigo-500 hover:bg-indigo-600 disabled:bg-zinc-800 disabled:text-zinc-500 disabled:cursor-not-allowed text-white px-6 py-2.5 rounded-lg font-medium transition-colors focus:ring-2 focus:ring-indigo-500/50 outline-none"
            >
              {busy && <Loader2 size={18} className="animate-spin" />}
              {busy ? "Enviando…" : "Fazer Upload"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
