import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import mdx from "@mdx-js/rollup";
import { dirname, resolve } from "path";
import { fileURLToPath } from "url";

const frontendHomeDir = dirname(fileURLToPath(import.meta.url));
const workspaceRoot = resolve(frontendHomeDir, "..");

export default defineConfig({
  plugins: [
    mdx(),
    react(),
  ],
  server: {
    host: "127.0.0.1",
    port: 5173,
    fs: {
      allow: [workspaceRoot],
    },
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
  test: {
    exclude: [
      "e2e/**",
      "node_modules/**",
      "dist/**",
      "coverage/**",
      "**/.{idea,git,cache,output,temp}/**",
      "**/{karma,rollup,webpack,vite,vitest,jest,ava,babel,nyc,cypress,tsup,build}.config.*",
    ],
  },
});
