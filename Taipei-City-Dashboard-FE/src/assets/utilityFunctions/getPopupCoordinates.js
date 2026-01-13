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
		return getBBoxCenter(feature);
	}

	return [clickLngLat.lng, clickLngLat.lat];
};

function getBBoxCenter(feature) {
	let minX = Infinity,
		minY = Infinity,
		maxX = -Infinity,
		maxY = -Infinity;

	const coords =
		feature.geometry.type === "Polygon"
			? feature.geometry.coordinates.flat()
			: feature.geometry.coordinates.flat(2);

	coords.forEach(([x, y]) => {
		minX = Math.min(minX, x);
		minY = Math.min(minY, y);
		maxX = Math.max(maxX, x);
		maxY = Math.max(maxY, y);
	});

	return [(minX + maxX) / 2, (minY + maxY) / 2];
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
