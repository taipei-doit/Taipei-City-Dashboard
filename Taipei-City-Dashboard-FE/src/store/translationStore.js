// Developed by Taipei Urban Intelligence Center 2023-2024

/**
 * 後端 LLM 翻譯 — 與 API 契約（請後端實作對應路由）：
 *
 * POST {baseURL}/translate
 * Headers: Authorization（沿用 axios）
 * Body:
 *   { "target_locale": "en", "texts": ["字串1", "字串2"], "source_locale": "zh-TW" }
 * Response:
 *   { "translations": ["str1", "str2"] }  // 與 texts 同長度、同順序
 *
 * 若路徑不同，請改下方 TRANSLATE_PATH 或改由環境變數覆寫。
 */

import { defineStore } from "pinia";
import debounce from "lodash/debounce";
import http from "../router/axios";
import { useContentStore } from "./contentStore";
import { LOCALE_STORAGE_KEY } from "../utils/acceptLanguage";

/**
 * 後端靜態文案字典（見 GET …/translation/static）
 */
const STATIC_TRANSLATION_PATH =
	import.meta.env.VITE_STATIC_TRANSLATION_PATH || "/translation/static";
const CACHE_STORAGE_KEY = "tcd-translation-cache";
const CACHE_MAX_ENTRIES = 500;

/** 介面預設以繁中為源文案；與此相同時不呼叫 API */
export const SOURCE_LOCALE = "zh-TW";

export const SUPPORTED_LOCALES = [
	{ code: "zh-TW", label: "中文" },
	{ code: "en", label: "英文" },
	{ code: "ja", label: "日文" },
	{ code: "ko", label: "韓文" },
	{ code: "vi", label: "越南文" },
	{ code: "th", label: "泰語" },
	{ code: "id", label: "印尼文" },
];

const TRANSLATE_PATH =
	import.meta.env.VITE_TRANSLATE_PATH || "/translate";

function readCache() {
	try {
		const raw = sessionStorage.getItem(CACHE_STORAGE_KEY);
		if (!raw) return {};
		const o = JSON.parse(raw);
		return typeof o === "object" && o ? o : {};
	} catch {
		return {};
	}
}

function writeCache(obj) {
	try {
		const keys = Object.keys(obj);
		if (keys.length > CACHE_MAX_ENTRIES) {
			for (const k of keys.slice(0, keys.length - CACHE_MAX_ENTRIES)) {
				delete obj[k];
			}
		}
		sessionStorage.setItem(CACHE_STORAGE_KEY, JSON.stringify(obj));
	} catch {
		// ignore quota
	}
}

function cacheKey(locale, text) {
	return `${locale}::${text}`;
}

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
		/** 快取：key = cacheKey(locale, 原文) */
		stringCache: readCache(),
		/** 併發批次：原文 -> 等待同一譯文的 resolve 陣列 */
		_batchResolvers: new Map(),
		/** 本輪待送出的原文集合 */
		_batchTexts: new Set(),
		/** GET /translation/static 回傳之字典 */
		staticDictionary: {},
		/** 後端回報的字典語系（供非同步翻譯完成後比對用） */
		staticDictionaryLocale: null,
	}),
	getters: {
		isSourceLocale: (s) => s.locale === SOURCE_LOCALE,
	},
	actions: {
		/**
		 * 載入靜態 UI 字串（Navbar、Sidebar 等 key）。
		 * 依賴 axios 已帶 Accept-Language，後端回對應語系。
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
			}
		},

		/** 靜態 key -> 譯文；缺少時回傳 key */
		t(key) {
			if (typeof key !== "string" || !key) {
				return "";
			}
			const s = this.staticDictionary[key];
			return s !== undefined && s !== null && s !== ""
				? s
				: key;
		},

                setLocale(code) {
                        if (!SUPPORTED_LOCALES.some((l) => l.code === code)) return;
                        this.locale = code;
                        localStorage.setItem(LOCALE_STORAGE_KEY, code);
                        this.fetchStaticDictionary();
                        
                        // u81eau52d5u91cdu65b0u62c9u53d6u5167u5bb9uff0cu4e0du9700u8981u4f7fu7528u8005u624bu52d5 F5
                        const contentStore = useContentStore();
                        if (contentStore.currentDashboard.index) {
                            contentStore.setCurrentDashboardAllContent();
                        } else {
                            contentStore.setDashboards(true);
                        }
                },

		cacheGet(text) {
			const k = cacheKey(this.locale, text);
			return this.stringCache[k];
		},

		cacheSet(text, translated) {
			const k = cacheKey(this.locale, text);
			this.stringCache[k] = translated;
			writeCache({ ...this.stringCache });
		},

		/**
		 * 將單一字串加入批次佇列，debounce 後一次 POST，減少 LLM 呼叫次數。
		 */
		translate(text) {
			if (typeof text !== "string") return Promise.resolve(String(text));
			if (!text || this.locale === SOURCE_LOCALE)
				return Promise.resolve(text);
			const hit = this.cacheGet(text);
			if (hit !== undefined) return Promise.resolve(hit);

			return new Promise((resolve) => {
				const list = this._batchResolvers.get(text) || [];
				list.push(resolve);
				this._batchResolvers.set(text, list);
				this._batchTexts.add(text);
				this.flushTranslateBatch();
			});
		},

		flushTranslateBatch: debounce(async function flush() {
			const store = useTranslationStore();
			const texts = [...store._batchTexts];
			store._batchTexts.clear();
			if (!texts.length) return;

			const resolversByText = new Map(store._batchResolvers);
			store._batchResolvers.clear();

			try {
				const { data } = await http.post(
					TRANSLATE_PATH,
					{
						source_locale: SOURCE_LOCALE,
						target_locale: store.locale,
						texts,
					},
					{
						skipGlobalLoading: true,
						skipErrorHandler: true,
					}
				);
				const out = data?.translations;
				if (!Array.isArray(out) || out.length !== texts.length) {
					throw new Error("Invalid translation response shape");
				}
				texts.forEach((src, i) => {
					const translated = out[i] ?? src;
					store.cacheSet(src, translated);
					const waiters = resolversByText.get(src) || [];
					waiters.forEach((fn) => fn(translated));
				});
			} catch {
				for (const t of texts) {
					const waiters = resolversByText.get(t) || [];
					waiters.forEach((fn) => fn(t));
				}
			}
		}, 80),
	},
});
