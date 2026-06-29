export function parseArrivalTime(seconds) {
	const h = Math.floor(seconds / 3600);
	const m = Math.floor((seconds % 3600) / 60);
	const s = seconds % 60;

	const ampm = h < 12 ? "上午" : "下午";
	const h12 = h % 12 || 12;

	return `${ampm} ${h12}點${String(m).padStart(2, "0")}分${String(s).padStart(2, "0")}秒`;
}
