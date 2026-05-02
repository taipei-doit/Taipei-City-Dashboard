<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->
<!-- 靜態 key：後端 GET /translation/static；動態：後端 LLM POST /translate -->

<script setup>
import { computed, ref, watch } from "vue";
import { useTranslationStore } from "../../../store/translationStore";

const props = defineProps({
	/** 後端字典 key，例如 nav.dashboard（與 GET /translation/static 的 strings 鍵一致） */
	dictKey: { type: String, default: "" },
	/** 原文（繁中）；語系非繁中時走 LLM 批次翻譯 */
	text: { type: String, default: "" },
	tag: { type: String, default: "span" },
});

const store = useTranslationStore();

const displayFromDict = computed(() => {
	if (!props.dictKey) {
		return null;
	}
	return store.staticDictionary[props.dictKey] ?? props.dictKey;
});

const displayFromLlm = ref(props.text);

watch(
	() => [store.locale, props.text, props.dictKey],
	async () => {
		if (props.dictKey) {
			return;
		}
		displayFromLlm.value = props.text;
		displayFromLlm.value = await store.translate(props.text);
	},
	{ immediate: true }
);

const display = computed(() =>
	props.dictKey ? displayFromDict.value : displayFromLlm.value
);
</script>

<template>
  <component :is="tag">
    {{ display }}
  </component>
</template>
