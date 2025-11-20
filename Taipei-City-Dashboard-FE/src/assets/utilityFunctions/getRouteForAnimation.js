/**
 * 將多段 LineString 按頭尾接成一條 LineString
 */
function mergeSegmentsFallback(segments) {
	if (!segments || !segments.length) return [];
	if (segments.length === 1) return segments[0].slice();

	const idx = new Map();
	const keyOf = (pt) => `${pt[0]},${pt[1]}`;
	segments.forEach((coords, i) => {
		const startK = keyOf(coords[0]);
		const endK = keyOf(coords[coords.length - 1]);
		if (!idx.has(startK)) idx.set(startK, []);
		if (!idx.has(endK)) idx.set(endK, []);
		idx.get(startK).push({ i, atStart: true });
		idx.get(endK).push({ i, atStart: false });
	});

	let startKey = null;
	for (const [k, list] of idx.entries()) if (list.length === 1) { startKey = k; break; }
	if (!startKey) startKey = keyOf(segments[0][0]);

	const visited = new Array(segments.length).fill(false);
	const merged = [];
	let currentKey = startKey;
  
	// eslint-disable-next-line no-constant-condition 
	while (true) {
		const candidates = idx.get(currentKey) || [];
		let chosen = null;
		for (const c of candidates) if (!visited[c.i]) { chosen = c; break; }
		if (!chosen) break;

		const seg = segments[chosen.i].slice();
		visited[chosen.i] = true;
		const segStartKey = keyOf(seg[0]);
		if (segStartKey !== currentKey) seg.reverse();
		if (merged.length === 0) merged.push(...seg);
		else merged.push(...seg.slice(1));
		const last = merged[merged.length - 1];
		currentKey = keyOf(last);
	}

	for (let i = 0; i < segments.length; i++) {
		if (!visited[i]) {
			const seg = segments[i];
			const lastMerged = merged[merged.length - 1];
			const segStartKey = keyOf(seg[0]);
			const lastKey = lastMerged ? keyOf(lastMerged) : null;
			if (lastKey && lastKey === segStartKey) merged.push(...seg.slice(1));
			else merged.push(...seg);
			visited[i] = true;
		}
	}

	return merged;
}

/**
 * 計算兩點平方距離 (僅用於比較)
 */
function distance2(pt1, pt2) {
	const dx = pt1[0] - pt2[0];
	const dy = pt1[1] - pt2[1];
	return dx * dx + dy * dy;
}

/**
 * 找點在線段上最近的投影點
 */
function nearestPointOnLineCoords(lineCoords, pt) {
	let minDist = Infinity;
	let nearest = lineCoords[0];
	let nearestIndex = 0;

	for (let i = 0; i < lineCoords.length - 1; i++) {
		const [x1, y1] = lineCoords[i];
		const [x2, y2] = lineCoords[i + 1];
		const dx = x2 - x1;
		const dy = y2 - y1;
		const t = ((pt[0] - x1) * dx + (pt[1] - y1) * dy) / (dx * dx + dy * dy);
		let proj;
		if (t < 0) proj = [x1, y1];
		else if (t > 1) proj = [x2, y2];
		else proj = [x1 + t * dx, y1 + t * dy];

		const d = distance2(proj, pt);
		if (d < minDist) {
			minDist = d;
			nearest = proj;
			nearestIndex = i;
		}
	}

	return { nearest, nearestIndex };
}

/**
 * 切割線段並保證順序從 start 到 end
 */
export function cutRouteSegment(geojson, startCoord, endCoord) {
	if (!geojson) throw new Error("沒有輸入 geojson");
	let feature = geojson;
	if (feature.type === "FeatureCollection") feature = feature.features[0];
	if (feature.type !== "Feature") throw new Error("輸入必須是 Feature 或 FeatureCollection");

	const geom = feature.geometry;
	let coords;
	if (geom.type === "LineString") coords = geom.coordinates.slice();
	else if (geom.type === "MultiLineString") coords = mergeSegmentsFallback(geom.coordinates);
	else throw new Error("只支援 LineString 或 MultiLineString");

	const start = nearestPointOnLineCoords(coords, startCoord);
	const end = nearestPointOnLineCoords(coords, endCoord);

	let startIndex = start.nearestIndex;
	let endIndex = end.nearestIndex;

	// 保證順序從 start -> end
	if (startIndex > endIndex) {
		[startIndex, endIndex] = [endIndex, startIndex];
	}

	const slicedCoords = coords.slice(startIndex, endIndex + 2); // 包含投影點

	return {
		type: "Feature",
		properties: {},
		geometry: {
			type: "LineString",
			coordinates: slicedCoords
		}
	};
}
