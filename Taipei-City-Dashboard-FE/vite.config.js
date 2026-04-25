import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import viteCompression from "vite-plugin-compression";
import basicSsl from "@vitejs/plugin-basic-ssl";
import mockBE from "./mock/index.js";

// 嘗試讀取環境變數，若不存在則回傳 false
let isDockerCompose = process?.env.DOCKER_COMPOSE === "true"; // eslint-disable-line no-undef

const serverConfig = isDockerCompose
	? {
		// Docker Compose override config
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
		host: "0.0.0.0",
		port: 80,
		https: true,
		proxy: {
			// 雙城暢行 MRT 無障礙 BE（contract: 13_雙城暢行_BE_api_contract.yaml）
			// 注意：合約寫 localhost:8080 是 BE container 內部視角；本機是 8088（docker-compose 對外 mapping）
			"/api/v1": {
				target: "http://localhost:8088",
				changeOrigin: true,
				secure: false
			},
			// 非 docker 模式下，VITE_API_URL=/api/dev 走這條（剝掉 /api/dev 再接到 prod /api/v1）
			"/api/dev": {
				target: "https://citydashboard.taipei/api/v1",
				changeOrigin: true,
				secure: false,
				rewrite: (path) => path.replace(/^\/api\/dev/, "")
			},
			"/api": {
				target: "https://citydashboard.taipei/api/v1",
				changeOrigin: true,
				secure: false,
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
	plugins: [mockBE(), vue(), viteCompression(), basicSsl()],
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