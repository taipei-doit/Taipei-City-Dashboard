export const getPopupCoordinates = (feature, clickLngLat) => {
	if (feature.geometry.type === "Point") {
		return feature.geometry.coordinates;
	}

	if (feature.geometry.type === "LineString") {
		return nearestPointOnLine(feature.geometry.coordinates, clickLngLat);
	}

	if (
		feature.geometry.type === "Polygon" ||
		feature.geometry.type === "MultiPolygon"
	) {
		return getPointInsidePolygon(feature);
	}

	return [clickLngLat.lng, clickLngLat.lat];
};

function getPointInsidePolygon(feature) {
	const polygons =
		feature.geometry.type === "Polygon"
			? [feature.geometry.coordinates]
			: feature.geometry.coordinates;

	for (const poly of polygons) {
		const ring = poly[0]; // exterior ring
		const center = getBBoxCenter(ring);

		if (pointInPolygon(center, ring)) {
			return center;
		}

		// 從中心往邊界射線找第一個進入 polygon 的點
		const found = raycastToPolygon(center, ring);
		if (found) return found;
	}

	// fallback
	return getBBoxCenter(
		feature.geometry.type === "Polygon"
			? feature.geometry.coordinates.flat()
			: feature.geometry.coordinates.flat(2),
	);
}

function getBBoxCenter(coords) {
	let minX = Infinity,
		minY = Infinity,
		maxX = -Infinity,
		maxY = -Infinity;

	coords.forEach(([x, y]) => {
		minX = Math.min(minX, x);
		minY = Math.min(minY, y);
		maxX = Math.max(maxX, x);
		maxY = Math.max(maxY, y);
	});

	return [(minX + maxX) / 2, (minY + maxY) / 2];
}

function pointInPolygon(point, vs) {
	const [x, y] = point;
	let inside = false;

	for (let i = 0, j = vs.length - 1; i < vs.length; j = i++) {
		const [xi, yi] = vs[i];
		const [xj, yj] = vs[j];

		const intersect =
			yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi;

		if (intersect) inside = !inside;
	}

	return inside;
}

function raycastToPolygon(center, ring) {
	const [cx, cy] = center;
	const step = 0.0001; // 地圖座標步進距離，可依 zoom 調整
	const maxSteps = 500;

	// 嘗試多個方向（8 向）
	const directions = [
		[1, 0],
		[-1, 0],
		[0, 1],
		[0, -1],
		[1, 1],
		[-1, -1],
		[1, -1],
		[-1, 1],
	];

	for (const [dx, dy] of directions) {
		for (let i = 1; i < maxSteps; i++) {
			const testPoint = [cx + dx * step * i, cy + dy * step * i];

			if (pointInPolygon(testPoint, ring)) {
				return testPoint;
			}
		}
	}

	return null;
}

function nearestPointOnLine(coords, lngLat) {
	let minDist = Infinity;
	let closestPoint = coords[0];

	for (let i = 0; i < coords.length - 1; i++) {
		const [x1, y1] = coords[i];
		const [x2, y2] = coords[i + 1];

		const dx = x2 - x1;
		const dy = y2 - y1;

		const t =
			((lngLat.lng - x1) * dx + (lngLat.lat - y1) * dy) /
			(dx * dx + dy * dy);

		const clampedT = Math.max(0, Math.min(1, t));

		const projX = x1 + clampedT * dx;
		const projY = y1 + clampedT * dy;

		const dist = (projX - lngLat.lng) ** 2 + (projY - lngLat.lat) ** 2;

		if (dist < minDist) {
			minDist = dist;
			closestPoint = [projX, projY];
		}
	}

	return closestPoint;
}
