/**
 * 計算兩點距離
 */
function distance(a, b) {
	const dx = a[0] - b[0];
	const dy = a[1] - b[1];
	return Math.sqrt(dx * dx + dy * dy);
}

/**
 * 計算點 p 到線段 [a,b] 的投影點
 */
function closestPointOnSegment(a, b, p) {
	const dx = b[0] - a[0];
	const dy = b[1] - a[1];
	const len2 = dx * dx + dy * dy;
	if (len2 === 0) return a.slice();
	const t = ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / len2;
	if (t <= 0) return a.slice();
	if (t >= 1) return b.slice();
	return [a[0] + t * dx, a[1] + t * dy];
}

/**
 * 找到線上最接近的點
 */
function nearestPointOnLine(coords, pt) {
	let minDist = Infinity;
	let closest = null;
	for (let i = 0; i < coords.length - 1; i++) {
		const proj = closestPointOnSegment(coords[i], coords[i + 1], pt);
		const d = distance(pt, proj);
		if (d < minDist) {
			minDist = d;
			closest = proj;
		}
	}
	return closest;
}

/**
 * 從 start 點切到 end 點
 */
function lineSlice(coords, startPt, endPt) {
	// 找到線上最近的索引
	let startIndex = 0;
	let endIndex = 0;
	let minStartDist = Infinity;
	let minEndDist = Infinity;

	for (let i = 0; i < coords.length; i++) {
		const dStart = distance(coords[i], startPt);
		if (dStart < minStartDist) {
			minStartDist = dStart;
			startIndex = i;
		}
		const dEnd = distance(coords[i], endPt);
		if (dEnd < minEndDist) {
			minEndDist = dEnd;
			endIndex = i;
		}
	}

	let sliced;
	if (startIndex <= endIndex) {
		sliced = [startPt, ...coords.slice(startIndex + 1, endIndex), endPt];
	} else {
		sliced = [startPt, ...coords.slice(endIndex + 1, startIndex).reverse(), endPt];
	}

	return {
		type: "Feature",
		geometry: { type: "LineString", coordinates: sliced },
		properties: {},
	};
}

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
 * 切割線段並保證順序從 start 到 end (純 JS)
 */
export function cutRouteSegment(geojson, startCoord, endCoord) {
	if (!geojson) throw new Error("沒有輸入 geojson");

	let geom;
	if (geojson.type === "FeatureCollection") geom = geojson.features[0].geometry;
	else if (geojson.type === "Feature") geom = geojson.geometry;
	else throw new Error("輸入必須是 Feature 或 FeatureCollection");

	let mergedCoords;
	if (geom.type === "LineString") mergedCoords = geom.coordinates.slice();
	else if (geom.type === "MultiLineString") mergedCoords = mergeSegmentsFallback(geom.coordinates);
	else throw new Error("只支援 LineString 或 MultiLineString");

	const snappedStart = nearestPointOnLine(mergedCoords, startCoord);
	const snappedEnd = nearestPointOnLine(mergedCoords, endCoord);

	let sliced = lineSlice(mergedCoords, snappedStart, snappedEnd);

	const firstPt = sliced.geometry.coordinates[0];
	const lastPt = sliced.geometry.coordinates[sliced.geometry.coordinates.length - 1];

	if (distance(startCoord, lastPt) < distance(startCoord, firstPt)) {
		sliced.geometry.coordinates.reverse();
	}

	return sliced;
}
