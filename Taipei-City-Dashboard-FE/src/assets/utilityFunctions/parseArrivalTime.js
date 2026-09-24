export function parseArrivalTime(seconds, timeType, arrival_time) {
	if (timeType === 'departure') {
		const h = Math.floor(seconds / 3600);
		const m = Math.floor((seconds % 3600) / 60);
		const s = seconds % 60;

		const ampm = h < 12 ? "上午" : "下午";
		const h12 = h % 12 || 12;

		return `${ampm} ${h12}點${String(m).padStart(2, "0")}分${String(s).padStart(2, "0")}秒`;
	} else {
		// arrival_time 是基準時間（假設是 "HH:mm:ss" 或 timestamp）
		const base = new Date(arrival_time);

		// 往回推 seconds
		const target = new Date(base.getTime() - seconds * 1000);

		const h = target.getHours();
		const m = target.getMinutes();
		const s = target.getSeconds();

		const ampm = h < 12 ? "上午" : "下午";
		const h12 = h % 12 || 12;

		return `${ampm} ${h12}點${String(m).padStart(2, "0")}分${String(s).padStart(2, "0")}秒`;
	}
}