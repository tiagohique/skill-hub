import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import { AuthProvider } from "./auth";
import { ThemeProvider } from "./ThemeContext";
import "./styles.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ThemeProvider>
      <AuthProvider>
        <App />
      </AuthProvider>
    </ThemeProvider>
  </StrictMode>,
);
