<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->
<!-- 靜態 key（GET …/translation/static）優先；缺詞時改用 text 備援（zh-TW 直出，其它語言走 POST /translate） -->

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

watch(
	[
		() => store.locale,
		() => store.dictionaryEpoch,
		() => props.text,
		() => props.dictKey,
		() => (props.dictKey ? store.staticDictionary[props.dictKey] : null),
		() => store.staticDictionary,
	],
	async () => {
		if (props.dictKey) {
			const dv = store.staticDictionary[props.dictKey];
			if (dv !== undefined && dv !== null && dv !== "") {
				display.value = dv;
				return;
			}
			const srcZh = props.text || "";
			if (store.locale === SOURCE_LOCALE) {
				display.value = srcZh || props.dictKey;
				return;
			}
			if (srcZh) {
				display.value = await store.translate(srcZh);
			} else {
				display.value = props.dictKey;
			}
			return;
		}
		display.value =
			store.locale === SOURCE_LOCALE || !props.text
				? props.text
				: await store.translate(props.text);
	},
	{ immediate: true }
);
</script>

<template>
  <component :is="props.tag">
    {{ display }}
  </component>
</template>
