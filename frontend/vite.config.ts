import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const apiTarget = process.env.VITE_API_PROXY_TARGET || "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: {
      "/ask": {
        target: apiTarget,
        changeOrigin: true,
      },
      "/agents": {
        target: apiTarget,
        changeOrigin: true,
      },
      "/profile": { target: apiTarget, changeOrigin: true },
      "/tickets": { target: apiTarget, changeOrigin: true },
      "/reports": { target: apiTarget, changeOrigin: true },
      "/employees": { target: apiTarget, changeOrigin: true },
      "/customers": { target: apiTarget, changeOrigin: true },
      "/queries": { target: apiTarget, changeOrigin: true },
      "/workflows": { target: apiTarget, changeOrigin: true },
      "/conversations": { target: apiTarget, changeOrigin: true },
      "/docs": { target: apiTarget, changeOrigin: true },
      "/openapi.json": { target: apiTarget, changeOrigin: true },
      "/health": {
        target: apiTarget,
        changeOrigin: true,
      },
      "/auth/register": { target: apiTarget, changeOrigin: true },
      "/auth/login": { target: apiTarget, changeOrigin: true },
      "/auth/refresh": { target: apiTarget, changeOrigin: true },
      "/auth/logout": { target: apiTarget, changeOrigin: true },
      "/auth/me": { target: apiTarget, changeOrigin: true },
      "/auth/google": { target: apiTarget, changeOrigin: true },
      "/auth/github": { target: apiTarget, changeOrigin: true },
    },
  },
});
