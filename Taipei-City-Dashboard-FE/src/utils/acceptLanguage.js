// Developed by Taipei Urban Intelligence Center 2023-2024

/** 與 translationStore 的 localStorage 鍵一致 */
export const LOCALE_STORAGE_KEY = "tcd-locale";

/**
 * 對應後端 Accept-Language：en, ja, ko, vi, th, id；缺省／繁中為 zh-TW。
 * @param {string | null | undefined} localeCode
 * @returns {string}
 */
export function toAcceptLanguage(localeCode) {
	if (!localeCode || localeCode === "zh-TW") {
		return "zh-TW";
	}
	const supported = new Set(["en", "ja", "ko", "vi", "th", "id"]);
	if (supported.has(localeCode)) {
		return localeCode;
	}
	return "zh-TW";
}

/**
 * 從 localStorage 讀目前語系並轉成 Accept-Language（供 axios 使用，避免循環 import store）。
 */
export function getAcceptLanguageHeader() {
	try {
		const code = localStorage.getItem(LOCALE_STORAGE_KEY);
		return toAcceptLanguage(code);
	} catch {
		return "zh-TW";
	}
}
