import nearestPointOnLine from "@turf/nearest-point-on-line";
import { point, lineString } from "@turf/helpers";
import center from "@turf/center";

export const getPopupCoordinates = (feature, clickLngLat) => {
	const clickPoint = point([clickLngLat.lng, clickLngLat.lat]);

	if (feature.geometry.type === "Point") {
		return feature.geometry.coordinates;
	}

	if (feature.geometry.type === "LineString") {
		// 找到線上最近點
		const line = lineString(feature.geometry.coordinates);
		return nearestPointOnLine(line, clickPoint).geometry.coordinates;
	}

	if (
		feature.geometry.type === "Polygon" ||
		feature.geometry.type === "MultiPolygon"
	) {
		// 可以先取中心
		const polyCenter = center(feature);
		return polyCenter.geometry.coordinates;
	}

	// fallback
	return [clickLngLat.lng, clickLngLat.lat];
};
