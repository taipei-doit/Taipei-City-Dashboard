<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->
<!-- frontendBundles／靜態 key 優先；缺詞時 text 備援為繁中原文（不依賴 POST /translate LLM） -->

<script setup>
import { ref, watch } from "vue";
import {
	useTranslationStore,
	SOURCE_LOCALE,
} from "../../../store/translationStore";

const props = defineProps({
	dictKey: { type: String, default: "" },
	text: { type: String, default: "" },
	tag: { type: String, default: "span" },
});

const store = useTranslationStore();
const display = ref("");

/** 換語／字典更新時過濾未完成之 async watch，避免舊 await 覆寫新畫面 */
let watchGeneration = 0;

watch(
	[
		() => store.locale,
		() => store.dictionaryEpoch,
		() => store.staticDictionaryLocale,
		() => props.text,
		() => props.dictKey,
		() =>
			props.dictKey ? store.staticDictionary[props.dictKey] : null,
		() => store.staticDictionary,
	],
	async () => {
		const gen = ++watchGeneration;

		function commit(next) {
			if (gen !== watchGeneration) {
				return;
			}
			display.value = next;
		}

		if (props.dictKey) {
			const dv = store.localizeStaticKey(props.dictKey);
			if (dv !== undefined && dv !== null && dv !== "") {
				commit(dv);
				return;
			}
			const srcZh = props.text || "";
			if (store.locale === SOURCE_LOCALE) {
				commit(srcZh || props.dictKey);
				return;
			}
			if (srcZh) {
				commit(await store.translate(srcZh));
				return;
			}
			commit(props.dictKey);
			return;
		}
		const plain =
			store.locale === SOURCE_LOCALE || !props.text
				? props.text
				: await store.translate(props.text);
		commit(plain ?? "");
	},
	{ immediate: true }
);
</script>

<template>
  <component :is="props.tag">
    {{ display }}
  </component>
</template>
