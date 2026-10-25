import { useEffect, useState } from "react";
import { Layout } from "./components/Layout";
import type { Page } from "./components/Layout";
import { SkillDetailPage } from "./pages/SkillDetailPage";
import { SkillsPage } from "./pages/SkillsPage";
import { UploadPage } from "./pages/UploadPage";

/** Rota por hash, sem biblioteca: "#/", "#/skills/<nome>" e "#/upload". */
function useHashRoute(): string {
  const [hash, setHash] = useState(window.location.hash || "#/");
  useEffect(() => {
    const onChange = () => {
      setHash(window.location.hash || "#/");
      window.scrollTo(0, 0);
    };
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);
  return hash;
}

export function App() {
  const route = useHashRoute();
  const detail = route.match(/^#\/skills\/([^/]+)$/);

  let active: Page | null = "list";
  let page;
  if (detail) {
    const name = decodeURIComponent(detail[1]!);
    page = <SkillDetailPage key={name} name={name} />;
  } else if (route === "#/upload") {
    active = "upload";
    page = <UploadPage />;
  } else {
    page = <SkillsPage />;
  }

  return <Layout active={active}>{page}</Layout>;
}
