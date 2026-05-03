import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

// https://vitejs.dev/config/
export default defineConfig({
	plugins: [vue()],
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
		assetsInlineLimit: 10000,
	},
	base: "/documentation",
	assetsInclude: ["**/*.md"],
	server: {
		hmr: {
			protocol: 'ws',
			host: '0.0.0.0',
			clientPort: 8082,
		},
		proxy: {
			"/api/v1": {
				target: "http://localhost:8088",
				changeOrigin: true,
			},
		},
	},
});
