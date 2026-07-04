import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import mdx from "@mdx-js/rollup";

export default defineConfig({
  plugins: [
    mdx(),
    react(),
  ],
  server: {
    host: "127.0.0.1",
    port: 5173,
    proxy: {
      "/homepage/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/quadrant": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: "../static/homepage_app",
    emptyOutDir: true,
    assetsDir: "",
    rollupOptions: {
      output: {
        entryFileNames: "main.js",
        chunkFileNames: "[name].js",
        assetFileNames: "[name][extname]",
      },
    },
  },
});
