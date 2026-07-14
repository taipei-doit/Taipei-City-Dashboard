// composables/useWindowManager.js
import { ref, computed } from "vue";

// 注意:這幾個 ref 宣告在模組最外層(不是函式內),
// 所以所有元件 import 進來共用同一份狀態,才能做到跨元件排版
const openWindows = ref([]); // 依開啟先後排序的 id 陣列

const CASCADE_STEP = 32;   // 每個視窗往右下位移的像素
const CASCADE_MAX = 8;     // 位移到第幾層之後開始重新繞回第一層
const BASE_Z_INDEX = 1000;

export function useWindowManager() {
	function open(id) {
		// 如果已經開著,先移除舊位置,重新放到陣列尾端(=移到最上層/最新位置)
		close(id);
		openWindows.value.push(id);
	}

	function close(id) {
		openWindows.value = openWindows.value.filter((w) => w !== id);
	}

	function isOpen(id) {
		return openWindows.value.includes(id);
	}

	// 依照開啟順序算出 cascade 位移
	function getOffset(id) {
		const idx = openWindows.value.indexOf(id);
		if (idx === -1) return { x: 0, y: 0 };
		const step = idx % CASCADE_MAX;
		return { x: step * CASCADE_STEP, y: step * CASCADE_STEP };
	}

	// 最後開啟的視窗疊在最上面
	function getZIndex(id) {
		const idx = openWindows.value.indexOf(id);
		return idx === -1 ? BASE_Z_INDEX : BASE_Z_INDEX + idx;
	}

	// 點擊視窗時把它移到最上層(重新排到陣列尾端),但不改變已開的位置
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