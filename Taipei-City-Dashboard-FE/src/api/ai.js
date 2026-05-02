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
			reqOpts,
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

/**
 * 自動抓取網頁新聞並推薦與現有資料組件關聯之報導（預計 2–3 則；後端上線後實作）。
 *
 * POST /api/v1/ai/recommend-news/crawl — RSS（NEWS_RSS_FEEDS）＋TWCC LLM 篩選與公開組件相關報導。
 *
 * @typedef {Object} RecommendedNewsWithComponent
 * @property {string} title
 * @property {string} [summary]
 * @property {string} [url]
 * @property {string} [source]
 * @property {string} [published_at]
 * @property {Object} component - 與 extractNewsInsight 之 components 項同欄位（id / index / city / name / short_desc）
 *
 * @param {Record<string, unknown>} [params] - 日後：來源、sitemap、時間區間等
 * @returns {Promise<RecommendedNewsWithComponent[]>}
 */

const crawlReqOpts = {
	...reqOpts,
	skipGlobalLoading: true,
};

export async function fetchCrawledNewsRecommendations(params = {}) {
	try {
		const { data: body } = await http.post(
			"/ai/recommend-news/crawl",
			params,
			crawlReqOpts,
		);

		if (body?.status !== "success" || !body?.data) {
			throw new Error(body?.message || "Recommend news crawl failed");
		}

		const raw = body.data.items ?? body.data.news ?? [];
		if (!Array.isArray(raw)) {
			throw new Error("Invalid crawl response shape");
		}

		return raw.filter(
			(item) =>
				item &&
				typeof item === "object" &&
				item.title &&
				item.component &&
				Object.keys(item.component).length > 0,
		);
	} catch (error) {
		console.error("AI Crawl News Recommendations Error:", error);
		throw error;
	}
}
