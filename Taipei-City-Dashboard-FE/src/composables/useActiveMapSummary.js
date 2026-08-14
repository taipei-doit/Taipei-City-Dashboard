// composables/useActiveMapSummary.js
import { ref } from "vue";

const activeMapSummaryId = ref(null);

export function useActiveMapSummary() {
	const open = (id) => { activeMapSummaryId.value = id; };
	const close = (id) => {
		if (activeMapSummaryId.value === id) activeMapSummaryId.value = null;
	};
	const isOpen = (id) => activeMapSummaryId.value === id;
	return { activeMapSummaryId, open, close, isOpen };
}