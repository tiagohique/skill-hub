import { useEffect, useState } from "react";
import { SkillsPage } from "./pages/SkillsPage";

/** Rota por hash, sem biblioteca: "#/", "#/skills/<nome>" e "#/upload". */
function useHashRoute(): string {
  const [hash, setHash] = useState(window.location.hash || "#/");
  useEffect(() => {
    const onChange = () => setHash(window.location.hash || "#/");
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);
  return hash;
}

export function App() {
  const route = useHashRoute();
  const detail = route.match(/^#\/skills\/([^/]+)$/);

  let page;
  if (detail) {
    page = <p className="muted">Detalhe de {decodeURIComponent(detail[1]!)} em construção.</p>;
  } else if (route === "#/upload") {
    page = <p className="muted">Envio de skill em construção.</p>;
  } else {
    page = <SkillsPage />;
  }

  return (
    <>
      <header className="topbar">
        <a className="brand" href="#/">
          Skills Hub
        </a>
        <nav>
          <a href="#/" aria-current={route === "#/" ? "page" : undefined}>
            Skills
          </a>
          <a href="#/upload" aria-current={route === "#/upload" ? "page" : undefined}>
            Enviar skill
          </a>
        </nav>
      </header>
      <main className="container">{page}</main>
    </>
  );
}
