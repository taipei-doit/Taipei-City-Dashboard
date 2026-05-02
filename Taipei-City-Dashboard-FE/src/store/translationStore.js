// Developed by Taipei Urban Intelligence Center 2023-2024


/**
 * UI 語系：靜態文案以前端 frontendBundles 為主；
 * GET /translation/static 僅備援繁中原稿。
 * 動態儀表板／組件內容不再走後端 LLM；LLM 僅用於小幫手向量推薦與 Storyline。
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
         * 後端已不再對動態內容做 LLM；僅回傳原文（維持 async 契約）。
         */
		translate(text) {
			if (typeof text !== "string") return Promise.resolve(String(text));
			return Promise.resolve(text);
		},
	},
});


