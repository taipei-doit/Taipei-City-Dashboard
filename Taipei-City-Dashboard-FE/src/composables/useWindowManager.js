// composables/useWindowManager.js
import { ref, computed } from "vue";

// Shared module-level state keeps all floating windows in one stack.
const openWindows = ref([]);
const windowOffsets = ref({});

const CASCADE_STEP = 32;
const CASCADE_MAX = 8;
const BASE_Z_INDEX = 9;

export function useWindowManager() {
	function open(id) {
		close(id);
		if (!windowOffsets.value[id]) {
			const step = openWindows.value.length % CASCADE_MAX;
			windowOffsets.value[id] = {
				x: step * CASCADE_STEP,
				y: step * CASCADE_STEP,
			};
		}
		openWindows.value.push(id);
	}

	function close(id) {
		openWindows.value = openWindows.value.filter((w) => w !== id);
	}

	function isOpen(id) {
		return openWindows.value.includes(id);
	}

	// Offset is assigned once per window so closing siblings does not shift it.
	function getOffset(id) {
		return windowOffsets.value[id] ?? { x: 0, y: 0 };
	}

	function getZIndex(id) {
		const idx = openWindows.value.indexOf(id);
		return idx === -1 ? BASE_Z_INDEX : BASE_Z_INDEX + idx;
	}

	function bringToFront(id) {
		if (!openWindows.value.includes(id)) return;
		openWindows.value = openWindows.value.filter((w) => w !== id);
		openWindows.value.push(id);
	}

	return {
		open,
		close,
		isOpen,
		getOffset,
		getZIndex,
		bringToFront,
		openWindows: computed(() => openWindows.value),
	};
}
