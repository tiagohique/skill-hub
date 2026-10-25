export type Theme = "light" | "dark";

const KEY = "theme";

/** Lê a escolha guardada no navegador; sem ela, segue o sistema e cai em dark. */
export function initialTheme(): Theme {
  try {
    const saved = localStorage.getItem(KEY);
    if (saved === "light" || saved === "dark") return saved;
    return window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
  } catch {
    return "dark";
  }
}

/** Troca a classe `dark` do <html>, a cor da barra do navegador e guarda a escolha. */
export function applyTheme(theme: Theme): void {
  document.documentElement.classList.toggle("dark", theme === "dark");
  document
    .querySelector('meta[name="theme-color"]')
    ?.setAttribute("content", theme === "dark" ? "#09090b" : "#fafafa");
  try {
    localStorage.setItem(KEY, theme);
  } catch {
    // navegador sem armazenamento: o tema vale só nesta visita
  }
}

export const otherTheme = (theme: Theme): Theme => (theme === "dark" ? "light" : "dark");
