// Developed by Taipei Urban Intelligence Center 2023-2024


/**
 * UI 語系：靜態文案以前端 frontendBundles 為主；
 * GET /translation/static 備援未覆蓋的 key。
 * 少量動態繁中短文（如新聞標題／摘要／洞察）可走 POST …/translate（後端 TWCC／快取）；
 * 儀表板組件大批量欄位仍由 GET /dashboard/ 後端批次處理。
 */


import { defineStore } from "pinia";
import http from "../router/axios";
import { useContentStore } from "./contentStore";
import { LOCALE_STORAGE_KEY } from "../utils/acceptLanguage";
import { lookupFrontendStatic } from "../i18n/frontendBundles";


/**
 * GET …/translation/static（備援鍵→繁中原文）
 */
const STATIC_TRANSLATION_PATH =
	import.meta.env.VITE_STATIC_TRANSLATION_PATH || "/translation/static";

const TRANSLATE_PATH =
	import.meta.env.VITE_TRANSLATE_PATH?.trim?.() || "/translate";

/** locale + 原文 → 動態短文譯文（與組件級 dashboard 批次翻譯分開） */
const dynTranslateMem = new Map();

/** 合併同時進行的相同請求 */
const dynTranslateInflight = new Map();

function bypassDynamicTranslateLocale(code) {
	return (
		code === SOURCE_LOCALE || code === "zh-Hant" || code === "zh-tw"
	);
}


/** 介面預設以繁中為源文案 */
export const SOURCE_LOCALE = "zh-TW";


/** 下拉選項顯示各語言自稱 */
export const SUPPORTED_LOCALES = [
	{ code: "zh-TW", label: "繁體中文" },
	{ code: "en", label: "English" },
	{ code: "ja", label: "日本語" },
	{ code: "ko", label: "한국어" },
	{ code: "vi", label: "Tiếng Việt" },
	{ code: "th", label: "ไทย" },
	{ code: "id", label: "Bahasa Indonesia" },
];


function readInitialLocale() {
	try {
		const s = localStorage.getItem(LOCALE_STORAGE_KEY);
		if (SUPPORTED_LOCALES.some((l) => l.code === s)) return s;
	} catch {
		// ignore
	}
	return SOURCE_LOCALE;
}


export const useTranslationStore = defineStore("translation", {
	state: () => ({
		locale: readInitialLocale(),
		/** 語系切換中：用於 UI 暫時顯示 loading，避免新舊語系混雜 */
		isApplyingLocale: false,
		/** GET /translation/static 回傳之字典（繁中備援） */
		staticDictionary: {},
		/** 後端回報的字典語系（供非同步載入後比對用） */
		staticDictionaryLocale: null,
		/** 字典載入／語系切換計數 */
		dictionaryEpoch: 0,
		/**
		 * 每次使用者切換語系遞增。用於捨棄較慢的舊請求（GET /translation/static、GET /dashboard/），避免翻譯與目前語系不同步。
		 */
		localeApplyGeneration: 0,
	}),
	getters: {
		isSourceLocale: (s) => s.locale === SOURCE_LOCALE,
	},
	actions: {
		async sleep(ms) {
			return new Promise((resolve) => setTimeout(resolve, ms));
		},

		/**
		 * 針對偶發網路/冷啟/短暫 5xx：小幅重試，避免使用者必須 refresh 才成功。
		 * - 支援 isStale：切換到下一輪 generation 後立刻中止重試
		 */
		async retry(fn, { tries = 2, delayMs = 400, isStale } = {}) {
			let lastErr;
			for (let i = 0; i < tries; i++) {
				if (typeof isStale === "function" && isStale()) {
					return;
				}
				try {
					return await fn();
				} catch (e) {
					lastErr = e;
					if (i < tries - 1) {
						await this.sleep(delayMs * (i + 1));
					}
				}
			}
			throw lastErr;
		},

		/**
         * 載入後端靜態 key→繁中原文（ Navbar 等備援）。
         */
		async fetchStaticDictionary(forGeneration = undefined) {
			try {
				const { data } = await http.get(STATIC_TRANSLATION_PATH, {
					skipGlobalLoading: true,
					skipErrorHandler: true,
				});
				if (
					forGeneration !== undefined &&
                    forGeneration !== this.localeApplyGeneration
				) {
					return;
				}
				const body = data?.data ?? data;
				const strings = body?.strings;
				if (strings && typeof strings === "object") {
					this.staticDictionary = { ...strings };
					this.staticDictionaryLocale =
                        body?.locale ?? this.locale;
				}
			} catch {
				// 後端未上線或路由未開時不中斷流程
			}
			if (
				forGeneration !== undefined &&
				forGeneration !== this.localeApplyGeneration
			) {
				return;
			}
			this.dictionaryEpoch += 1;
		},


		releasePendingTranslates() {},


		/**
         * 先讀 frontendBundles.js，再走 GET /translation/static（語系對齊時）。
         */
		localizeStaticKey(key) {
			if (typeof key !== "string" || !key) {
				return "";
			}
			const fe = lookupFrontendStatic(this.locale, key);
			if (fe !== undefined && fe !== null && fe !== "") {
				return fe;
			}
			if (this.staticDictionaryLocale !== this.locale) {
				return "";
			}
			const s = this.staticDictionary[key];
			return s !== undefined && s !== null && s !== ""
				? s
				: "";
		},


		/**
         * 靜態 key -> 譯文
         */
		t(key) {
			return this.localizeStaticKey(key);
		},


		async setLocale(code) {
			if (!SUPPORTED_LOCALES.some((l) => l.code === code)) return;

			const contentStore = useContentStore();
			const changed = code !== this.locale;

			// 語系切換期間先蓋 loading，等 dashboard 文字合併完再放開
			if (changed) {
				this.isApplyingLocale = true;
				dynTranslateMem.clear();
				dynTranslateInflight.clear();
			}

			this.releasePendingTranslates();
			this.locale = code;
			localStorage.setItem(LOCALE_STORAGE_KEY, code);

			const applyGen = ++this.localeApplyGeneration;
			try {
				await this.fetchStaticDictionary(applyGen);

				if (applyGen !== this.localeApplyGeneration) return;

				// 單支 GET /dashboard/：後端可帶 includeIndex 直接回傳該 dashboard 的翻譯後組件文字欄位，
				// 前端在 setDashboards(true) 內合併回既有物件，避免再打第二支 /dashboard/:index。
				if (changed) {
					const isStale = () =>
						applyGen !== this.localeApplyGeneration;
					await this.retry(
						() => contentStore.setDashboards(true, isStale),
						{ tries: 2, delayMs: 500, isStale }
					);
				}
			} finally {
				// 只有最新一輪切換才可以放開 loading
				if (applyGen === this.localeApplyGeneration) {
					this.isApplyingLocale = false;
				}
			}
		},


		/**
		 * 單段繁中 → 目標語系（POST /translate，後端快取＋LLM）。
		 * 失敗時回傳原文；VITE_MOCK_TRANSLATION=true 時回傳前綴標記供本機離線測試。
		 */
		translate(text) {
			if (typeof text !== "string") {
				return Promise.resolve(String(text));
			}
			const loc = this.locale;
			if (bypassDynamicTranslateLocale(loc)) {
				return Promise.resolve(text);
			}
			const trimmed = text.trim();
			if (!trimmed) {
				return Promise.resolve(text);
			}

			const ck = `${loc}::${trimmed}`;
			if (dynTranslateMem.has(ck)) {
				return Promise.resolve(dynTranslateMem.get(ck));
			}
			const pending = dynTranslateInflight.get(ck);
			if (pending) {
				return pending;
			}

			const promise = (async () => {
				try {
					if (String(import.meta.env.VITE_MOCK_TRANSLATION) === "true") {
						const out = `[${loc}·mock] ${trimmed}`;
						dynTranslateMem.set(ck, out);
						return out;
					}

					const { data } = await http.post(
						TRANSLATE_PATH,
						{
							source_locale: SOURCE_LOCALE,
							target_locale: loc,
							texts: [trimmed],
						},
						{ skipGlobalLoading: true, skipErrorHandler: true }
					);

					const body = data?.data ?? data;
					const arr = body?.translations;
					let out =
						Array.isArray(arr) && typeof arr[0] === "string"
							? arr[0]
							: trimmed;
					out =
						String(out || "").trim() !== ""
							? String(out)
							: trimmed;

					dynTranslateMem.set(ck, out);
					return out;
				} catch {
					dynTranslateMem.set(ck, trimmed);
					return trimmed;
				} finally {
					dynTranslateInflight.delete(ck);
				}
			})();

			dynTranslateInflight.set(ck, promise);
			return promise;
		},
	},
});


