<script setup>
import { onUnmounted, ref, watch } from "vue";

const props = defineProps({
	text: {
		type: String,
		default: "",
	},
	enabled: {
		type: Boolean,
		default: false,
	},
});

const emit = defineEmits(["tick", "done"]);

const shown = ref("");
const typing = ref(false);
let timer = null;

const stop = () => {
	if (timer) {
		clearInterval(timer);
		timer = null;
	}
	typing.value = false;
};

const play = (text) => {
	stop();
	const content = text || "";
	const reduceMotion = window.matchMedia(
		"(prefers-reduced-motion: reduce)",
	).matches;

	if (!props.enabled) {
		shown.value = content;
		return;
	}

	if (reduceMotion || !content) {
		shown.value = content;
		emit("done");
		return;
	}

	shown.value = "";
	typing.value = true;
	let index = 0;
	timer = setInterval(() => {
		index += 1;
		shown.value = content.slice(0, index);
		emit("tick");
		if (index >= content.length) {
			stop();
			emit("done");
		}
	}, 28);
};

watch(
	() => [props.text, props.enabled],
	() => play(props.text),
	{ immediate: true },
);

onUnmounted(stop);
</script>

<template>
  <p>
    {{ shown }}<span
      v-if="typing"
      class="type-caret"
    />
  </p>
</template>
