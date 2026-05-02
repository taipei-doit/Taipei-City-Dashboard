// Developed by Taipei Urban Intelligence Center 2023-2024

import { computed } from "vue";
import {
	useTranslationStore,
	SUPPORTED_LOCALES,
	SOURCE_LOCALE,
} from "../store/translationStore";

/**
 * 後端多語 — 在元件中使用：
 * - 靜態 key（字典）：store.t('nav.dashboard') 或 <BackendTranslatedText dict-key="nav.dashboard" />
 * - 動態 LLM 逐字翻譯：<BackendTranslatedText text="..." /> 或 await translate(s)
 */
export function useBackendTranslation() {
	const store = useTranslationStore();

	return {
		locale: computed(() => store.locale),
		setLocale: (code) => store.setLocale(code),
		translate: (text) => store.translate(text),
		t: (key) => store.t(key),
		fetchStaticDictionary: () => store.fetchStaticDictionary(),
		staticDictionary: computed(() => store.staticDictionary),
		isSourceLocale: computed(() => store.isSourceLocale),
		supportedLocales: SUPPORTED_LOCALES,
		sourceLocale: SOURCE_LOCALE,
	};
}
