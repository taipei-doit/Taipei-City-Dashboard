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
		return getPointOnPolygon(feature, clickLngLat);
	}

	return [clickLngLat.lng, clickLngLat.lat];
};

function getPointOnPolygon(feature, clickLngLat) {
	const polygons =
		feature.geometry.type === "Polygon"
			? [feature.geometry.coordinates]
			: feature.geometry.coordinates;

	const clickPoint = [clickLngLat.lng, clickLngLat.lat];

	let closestPoint = null;
	let minDist = Infinity;

	for (const poly of polygons) {
		const ring = poly[0]; // exterior ring

		// 如果點在面內，直接回傳點擊點
		if (pointInPolygon(clickPoint, ring)) {
			return clickPoint;
		}

		// 不在面內，找邊界最近點
		const edgePoint = nearestPointOnLine(ring, clickLngLat);
		const dist =
			(edgePoint[0] - clickPoint[0]) ** 2 +
			(edgePoint[1] - clickPoint[1]) ** 2;

		if (dist < minDist) {
			minDist = dist;
			closestPoint = edgePoint;
		}
	}

	// fallback
	return closestPoint || clickPoint;
}

function pointInPolygon(point, ring) {
	const [x, y] = point;
	let inside = false;

	// 有些 GeoJSON ring 最後一點會等於第一點，這樣處理比較安全
	const len = ring.length;
	for (let i = 0, j = len - 1; i < len; j = i++) {
		const [xi, yi] = ring[i];
		const [xj, yj] = ring[j];

		// 射線法判斷是否穿越邊
		const intersect =
			yi > y !== yj > y &&
			x < ((xj - xi) * (y - yi)) / (yj - yi + 0.0) + xi;

		if (intersect) inside = !inside;
	}

	return inside;
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
