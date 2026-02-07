// src/utils/geometryUtils.js

/**
 * 沿著線段陣列插值取得位置
 * @param {Array<Array<number>>} coords - 線段座標陣列 [[x,y] 或 [x,y,z], ...]
 * @param {number} t - 插值百分比，0 ~ 1
 * @returns {Array<number>} 插值後的座標
 */
export function interpolateAlongSegment(coords, t) {
	if (!coords || coords.length === 0) return null;
	t = Math.max(0, Math.min(1, t)); // clamp t

	const lengths = [];
	let totalLength = 0;

	for (let i = 0; i < coords.length - 1; i++) {
		const dx = coords[i + 1][0] - coords[i][0];
		const dy = coords[i + 1][1] - coords[i][1];
		const dz = (coords[i + 1][2] || 0) - (coords[i][2] || 0);
		const len = Math.sqrt(dx * dx + dy * dy + dz * dz);
		lengths.push(len);
		totalLength += len;
	}

	const targetDist = t * totalLength;
	let accum = 0;
	let i = 0;
	while (i < lengths.length && accum + lengths[i] < targetDist) {
		accum += lengths[i];
		i++;
	}

	if (i >= coords.length - 1) return coords[coords.length - 1];

	const localT = (targetDist - accum) / lengths[i];
	const from = coords[i];
	const to = coords[i + 1];
	const lng = from[0] + (to[0] - from[0]) * localT;
	const lat = from[1] + (to[1] - from[1]) * localT;
	const z = (from[2] || 0) + ((to[2] || 0) - (from[2] || 0)) * localT;

	return [lng, lat, z];
}
