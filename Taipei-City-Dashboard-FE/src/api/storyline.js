// Developed by Taipei Urban Intelligence Center 2023-2024

import http from "../router/axios";

const reqOpts = {
	skipGlobalLoading: true,
	skipErrorHandler: true,
};

/**
 * GET …/storyline/topics（與後端掛在 /v1 下之契約一致；axios base 已為 /api/dev 等）
 * @returns {Promise<Array<{ id, title, summary, lang, updated_at }>>}
 */
export async function fetchStorylineTopics() {
	const { data: body } = await http.get("/storyline/topics", reqOpts);
	if (Array.isArray(body)) {
		return body;
	}
	if (body?.data && Array.isArray(body.data)) {
		return body.data;
	}
	return [];
}

/**
 * POST /v1/storyline/recommend
 * @param {{ lang: string, topic_id?: string, user_context?: object, limit?: number }} payload
 * @returns {Promise<{ steps: Array }>}
 */
export async function postStorylineRecommend(payload) {
	const { data: body } = await http.post(
		"/storyline/recommend",
		payload,
		reqOpts
	);
	if (body?.steps) {
		return body;
	}
	if (body?.data?.steps) {
		return body.data;
	}
	return { steps: [] };
}

/** 後端契約 lang：zh-TW | en | ja */
export function toStorylineApiLang(localeCode) {
	if (localeCode === "en" || localeCode === "ja" || localeCode === "zh-TW") {
		return localeCode;
	}
	return "zh-TW";
}

/** 將 recommend steps 內的新聞合併去重 */
export function collectRelatedNewsFromSteps(steps) {
	const seen = new Set();
	const list = [];
	for (const step of steps || []) {
		for (const n of step.related_news || []) {
			const key = n.news_id ?? `${n.title}-${n.url}`;
			if (seen.has(key)) {
				continue;
			}
			seen.add(key);
			list.push(n);
		}
	}
	return list;
}
