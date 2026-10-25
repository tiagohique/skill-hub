import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

// No Compose, API_TARGET aponta para o contêiner do hub; o portal só fala com a REST (/api).
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, ".", "");
  const target = env.API_TARGET ?? "http://localhost:8000";
  return {
    plugins: [react(), tailwindcss()],
    server: {
      host: true,
      port: 5173,
      // /docs, /openapi.json e /mcp-docs: Swagger da API e referência do MCP (pedem a senha da documentação).
      proxy: Object.fromEntries(
        ["/api", "/docs", "/openapi.json", "/mcp-docs"].map((p) => [p, { target, changeOrigin: true }]),
      ),
    },
  };
});
