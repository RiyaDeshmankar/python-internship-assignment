import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ command }) => ({
  base: command === "build" ? "/static/" : "/",
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/books": "http://127.0.0.1:8000",
      "/recommend": "http://127.0.0.1:8000",
      "/ask-question": "http://127.0.0.1:8000",
      "/upload-book": "http://127.0.0.1:8000"
    }
  }
}));
