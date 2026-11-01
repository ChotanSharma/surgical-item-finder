import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const BACKEND = "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    // During development, send API calls to the FastAPI server
    proxy: {
      "/agent": BACKEND,
      "/items": BACKEND,
      "/locations": BACKEND,
      "/health": BACKEND,
    },
    // WSL can't see file changes on /mnt/c without polling
    watch: { usePolling: true },
  },
});
