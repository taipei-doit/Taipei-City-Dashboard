// Developed by Taipei Urban Intelligence Center 2026

import http from "../router/axios";

const reqOpts = {
	skipGlobalLoading: false, // AI 處理較久，建議顯示全域 Loading 或由組件自行控制
	skipErrorHandler: false,
};

/**
 * POST /api/v1/ai/extract-insight/news
 * 透過新聞 URL 擷取內容、生成故事線並推薦對應數據組件
 * @param {string} url - 新聞網址
 * @returns {Promise<{
 *   content: string,
 *   storyline: string,
 *   components: Array,
 *   usage: object,
 *   latency_ms: number
 * }>}
 */
export async function extractNewsInsight(url) {
	try {
		const { data: body } = await http.post(
			"/ai/extract-insight/news",
			{ url },
			reqOpts
		);

		if (body?.status === "success" && body?.data) {
			return body.data;
		}

		throw new Error(body?.message || "Failed to extract insight");
	} catch (error) {
		console.error("AI Extract Insight Error:", error);
		throw error;
	}
}
