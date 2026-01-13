import nearestPointOnLine from "@turf/nearest-point-on-line";
import bbox from "@turf/bbox";
import { point, lineString } from "@turf/helpers";

export const getPopupCoordinates = (feature, clickLngLat) => {
	const clickPoint = point([clickLngLat.lng, clickLngLat.lat]);

	if (feature.geometry.type === "Point") {
		return feature.geometry.coordinates;
	}

	if (feature.geometry.type === "LineString") {
		const line = lineString(feature.geometry.coordinates);
		return nearestPointOnLine(line, clickPoint).geometry.coordinates;
	}

	if (
		feature.geometry.type === "Polygon" ||
		feature.geometry.type === "MultiPolygon"
	) {
		const [minX, minY, maxX, maxY] = bbox(feature);
		return [(minX + maxX) / 2, (minY + maxY) / 2];
	}

	return [clickLngLat.lng, clickLngLat.lat];
};
