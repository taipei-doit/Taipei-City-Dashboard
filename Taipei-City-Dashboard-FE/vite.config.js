import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import viteCompression from "vite-plugin-compression";

// 嘗試讀取環境變數，若不存在則回傳 false
let isDockerCompose = process?.env.DOCKER_COMPOSE === "true"; // eslint-disable-line no-undef

const serverConfig = isDockerCompose
  ? {
      // Docker Compose override config
      headers: { 'X-Robots-Tag': 'noindex, nofollow' },
      host: "0.0.0.0",
      port: 80, // 如有需要可變更 port
      proxy: {
        "/api/dev": {
          target: "http://dashboard-be:8080",
          changeOrigin: true,
          rewrite: (path) => path.replace("/dev", "/v1")
        }
      }
    }
  : {
      headers: { 'X-Robots-Tag': 'noindex, nofollow' },
      host: "0.0.0.0",
      port: 80,
      proxy: {
        "/api": {
          target: "https://citydashboard.taipei/api/v1",
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, "")
        },
        "/geo_server": {
          target: "https://citydashboard.taipei/geo_server/",
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/geo_server/, "")
        }
      }
    };

export default defineConfig({
  plugins: [vue(), viteCompression()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes("node_modules")) {
            return id
              .toString()
              .split("node_modules/")[1]
              .split("/")[0]
              .toString();
          }
        },
      },
    },
    chunkSizeWarningLimit: 1600,
  },
  base: "/",
  server: serverConfig,
});