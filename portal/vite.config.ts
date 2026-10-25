import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

// No Compose, API_TARGET aponta para o contêiner do hub; o portal só fala com a REST (/api).
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, ".", "");
  const target = env.API_TARGET ?? "http://localhost:8000";
  return {
    plugins: [react()],
    server: {
      host: true,
      port: 5173,
      proxy: { "/api": { target, changeOrigin: true } },
    },
  };
});
