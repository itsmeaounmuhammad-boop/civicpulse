import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// The frontend only ever calls a relative "/api". In dev this proxy forwards it
// to the backend; in Compose/Kubernetes nginx does the same job (ADR-0002).
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});