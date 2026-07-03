import { defineConfig } from "vite";

// The browser only ever talks to the Vite dev server. Calls to /api are proxied
// to the FastAPI backend, so there is no cross-origin request and no CORS to set up.
export default defineConfig({
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: "dist",
  },
});
