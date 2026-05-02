// Developed by Taipei Urban Intelligence Center 2023-2024
// 城市顯示名稱：優先靜態字典 `city.area.*` / `city.expanded.*` / `city.collapsed.*`，無則沿用 cityManager 繁中。

import { useContentStore } from "../store/contentStore";
import { useTranslationStore } from "../store/translationStore";

export function useCityLabels() {
	const contentStore = useContentStore();
	const translationStore = useTranslationStore();

	function dictOr(key, fallback) {
		void translationStore.staticDictionary;
		void translationStore.dictionaryEpoch;
		void translationStore.locale;
		const raw = translationStore.staticDictionary[key];
		return raw !== undefined && raw !== null && raw !== ""
			? raw
			: fallback;
	}

	function areaName(value) {
		const fb =
			contentStore.cityManager.getCities(value)[0]?.name ?? String(value);
		return dictOr(`city.area.${value}`, fb);
	}

	function expandedLabel(cityKey) {
		return dictOr(
			`city.expanded.${cityKey}`,
			contentStore.cityManager.getExpandedNameName(cityKey)
		);
	}

	function collapsedLabel(cityKey) {
		return dictOr(
			`city.collapsed.${cityKey}`,
			contentStore.cityManager.getCollapsedName(cityKey)
		);
	}

	function translatedTagList(dashboardCity) {
		return contentStore.cityManager.getTagList(dashboardCity).map((c) => ({
			...c,
			name: areaName(c.value),
		}));
	}

	function translatedSelectList(dashboardCity) {
		return contentStore.cityManager.getSelectList(dashboardCity).map((c) => ({
			...c,
			name: areaName(c.value),
		}));
	}

	function translatedCities(keys) {
		return contentStore.cityManager.getCities(keys).map((c) => ({
			...c,
			name: areaName(c.value),
		}));
	}

	return {
		dictOr,
		areaName,
		expandedLabel,
		collapsedLabel,
		translatedTagList,
		translatedSelectList,
		translatedCities,
	};
}
