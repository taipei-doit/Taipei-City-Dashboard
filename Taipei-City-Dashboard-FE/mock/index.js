// Vite plugin: 攔截尚未實作的 BE endpoint，從本地 JSON 檔回傳 mock 資料。
// 等 BE 真的實作好對應路由後，把該條目從 routes 移除即可，FE 不用動。
//
// 加新 mock：在這個 routes map 加 "<path>": "<file under mock/>" 即可。

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// 路徑相對於 mock/ 資料夾
const routes = {};

export default function mockBE() {
	return {
		name: "mock-be",
		configureServer(server) {
			server.middlewares.use((req, res, next) => {
				const url = req.url?.split("?")[0];
				const file = routes[url];
				if (!file) return next();

				const filepath = path.join(__dirname, file);
				fs.readFile(filepath, "utf8", (err, data) => {
					if (err) {
						res.statusCode = 500;
						res.setHeader("Content-Type", "application/json");
						res.end(
							JSON.stringify({
								status: "error",
								message: `mock file not found: ${file}`,
							}),
						);
						return;
					}
					res.statusCode = 200;
					res.setHeader("Content-Type", "application/json");
					res.setHeader("X-Mocked-By", "vite-plugin-mock-be");
					res.end(data);
				});
			});
		},
	};
}
