import mapboxgl from "mapbox-gl";

export const getPopupCoordinates = (feature, clickLngLat) => {
	if (feature.geometry.type === "Point") {
		return feature.geometry.coordinates;
	}

	if (feature.geometry.type === "LineString") {
		return nearestPointOnLine(feature.geometry.coordinates, clickLngLat);
	}

	if (feature.geometry.type === "MultiLineString") {
		return nearestPointOnMultiLine(
			feature.geometry.coordinates,
			clickLngLat,
		);
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

	// 將點轉成 Web Mercator
	const clickMerc = mapboxgl.MercatorCoordinate.fromLngLat(lngLat);

	for (let i = 0; i < coords.length - 1; i++) {
		const [lng1, lat1] = coords[i];
		const [lng2, lat2] = coords[i + 1];

		const p1 = mapboxgl.MercatorCoordinate.fromLngLat({
			lng: lng1,
			lat: lat1,
		});
		const p2 = mapboxgl.MercatorCoordinate.fromLngLat({
			lng: lng2,
			lat: lat2,
		});

		const dx = p2.x - p1.x;
		const dy = p2.y - p1.y;

		// 投影比例 t
		const t =
			((clickMerc.x - p1.x) * dx + (clickMerc.y - p1.y) * dy) /
			(dx * dx + dy * dy);
		const clampedT = Math.max(0, Math.min(1, t));

		// 計算投影點
		const projX = p1.x + clampedT * dx;
		const projY = p1.y + clampedT * dy;

		// 計算距離平方
		const dist = (projX - clickMerc.x) ** 2 + (projY - clickMerc.y) ** 2;

		if (dist < minDist) {
			minDist = dist;

			// Mercator → 經緯度
			const closestMerc = new mapboxgl.MercatorCoordinate(projX, projY);
			const lngLatPoint = closestMerc.toLngLat();
			closestPoint = [lngLatPoint.lng, lngLatPoint.lat];
		}
	}

	return closestPoint;
}

function nearestPointOnMultiLine(multiCoords, lngLat) {
	let minDist = Infinity;
	let closestPoint = null;

	const clickMerc = mapboxgl.MercatorCoordinate.fromLngLat(lngLat);

	for (const coords of multiCoords) {
		// 遍歷每條線
		for (let i = 0; i < coords.length - 1; i++) {
			const [lng1, lat1] = coords[i];
			const [lng2, lat2] = coords[i + 1];

			const p1 = mapboxgl.MercatorCoordinate.fromLngLat({
				lng: lng1,
				lat: lat1,
			});
			const p2 = mapboxgl.MercatorCoordinate.fromLngLat({
				lng: lng2,
				lat: lat2,
			});

			const dx = p2.x - p1.x;
			const dy = p2.y - p1.y;

			const t =
				((clickMerc.x - p1.x) * dx + (clickMerc.y - p1.y) * dy) /
				(dx * dx + dy * dy);
			const clampedT = Math.max(0, Math.min(1, t));

			const projX = p1.x + clampedT * dx;
			const projY = p1.y + clampedT * dy;

			const dist =
				(projX - clickMerc.x) ** 2 + (projY - clickMerc.y) ** 2;

			if (dist < minDist) {
				minDist = dist;
				const closestMerc = new mapboxgl.MercatorCoordinate(
					projX,
					projY,
				);
				const lngLatPoint = closestMerc.toLngLat();
				closestPoint = [lngLatPoint.lng, lngLatPoint.lat];
			}
		}
	}

	return closestPoint;
}
