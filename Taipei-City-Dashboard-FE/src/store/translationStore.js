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
		/** GET /translation/static 回傳之字典（繁中備援） */
		staticDictionary: {},
		/** 後端回報的字典語系（供非同步載入後比對用） */
		staticDictionaryLocale: null,
		/** 字典載入／語系切換計數 */
		dictionaryEpoch: 0,
	}),
	getters: {
		isSourceLocale: (s) => s.locale === SOURCE_LOCALE,
	},
	actions: {
		/**
         * 載入後端靜態 key→繁中原文（ Navbar 等備援）。
         */
		async fetchStaticDictionary() {
			try {
				const { data } = await http.get(STATIC_TRANSLATION_PATH, {
					skipGlobalLoading: true,
					skipErrorHandler: true,
				});
				const body = data?.data ?? data;
				const strings = body?.strings;
				if (strings && typeof strings === "object") {
					this.staticDictionary = { ...strings };
					this.staticDictionaryLocale =
                        body?.locale ?? this.locale;
				}
			} catch {
				// 後端未上線或路由未開時不中斷流程
			} finally {
				this.dictionaryEpoch += 1;
			}
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
			this.releasePendingTranslates();
			this.locale = code;
			localStorage.setItem(LOCALE_STORAGE_KEY, code);
			await this.fetchStaticDictionary();


			if (changed && contentStore.currentDashboard?.index) {
				contentStore.setCurrentDashboardAllContent();
			} else if (changed) {
				contentStore.setDashboards(true);
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


