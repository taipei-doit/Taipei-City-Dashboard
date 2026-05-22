// Developed by Bombs King, Taipei Codefest 2026

import { IsochroneMapConfig } from "../configs/mapbox/mapConfig.js";

export function getIsochroneLayerIds(layerId) {
	return {
		area: layerId,
		network: `${layerId}${IsochroneMapConfig.layers.networkSuffix}`,
		networkStops: `${layerId}${IsochroneMapConfig.layers.networkStopsSuffix}`,
		outline: `${layerId}${IsochroneMapConfig.layers.outlineSuffix}`,
	};
}

export function getIsochroneAuxLayerIds(layerId) {
	const ids = getIsochroneLayerIds(layerId);
	return [ids.network, ids.networkStops, ids.outline];
}

export function getIsochroneTimeSlots() {
	const slots = [];
	const interval = IsochroneMapConfig.time.slotIntervalMinutes;
	for (let h = 0; h < 24; h++) {
		const hh = h.toString().padStart(2, "0");
		for (let m = 0; m < 60; m += interval) {
			const mm = m.toString().padStart(2, "0");
			slots.push(`${hh}:${mm}`);
		}
	}
	return slots;
}

export function getIsochroneQueryDate(dayType) {
	return (
		IsochroneMapConfig.time.queryDates[dayType] ||
		IsochroneMapConfig.time.queryDates[IsochroneMapConfig.defaults.dayType]
	);
}

export function getIsochroneTimeParams(timeSlot, dayType, timeDirection) {
	const dateTime = `${getIsochroneQueryDate(dayType)}T${timeSlot}:00+08:00`;
	const params = { departure_time: dateTime, time_type: timeDirection };
	if (timeDirection === "arrival") {
		params.arrival_time = dateTime;
	}
	return params;
}

export function buildIsochroneRequest(lngLat, options) {
	const { timeSlot, dayType, timeDirection, modes } = options;
	return {
		lat: lngLat.lat,
		lng: lngLat.lng,
		...getIsochroneTimeParams(timeSlot, dayType, timeDirection),
		service_profile: dayType,
		modes,
	};
}

export function prepareIsochroneRenderData(geojson) {
	const features = geojson?.features || [];
	const groups = new Map();
	const passthrough = [];

	features.forEach((feature) => {
		if (
			feature.properties?.layer !== IsochroneMapConfig.layers.featureLayers.isochrone ||
			!["Polygon", "MultiPolygon"].includes(feature.geometry?.type)
		) {
			passthrough.push(feature);
			return;
		}
		const key =
			feature.properties?.time_slot ||
			feature.properties?.departure_time ||
			"__default";
		if (!groups.has(key)) {
			groups.set(key, []);
		}
		groups.get(key).push(feature);
	});

	const enrichedIsochrones = [];
	groups.forEach((group) => {
		const sorted = [...group].sort(
			(a, b) =>
				Number(a.properties?.minutes || 0) -
				Number(b.properties?.minutes || 0),
		);

		sorted.forEach((feature) => {
			const minutes = Number(feature.properties?.minutes || 0);
			enrichedIsochrones.push({
				...feature,
				properties: {
					...feature.properties,
					layer: IsochroneMapConfig.layers.featureLayers.isochrone,
					color:
						feature.properties?.color ||
						IsochroneMapConfig.colors[minutes] ||
						IsochroneMapConfig.colors.default,
					name: feature.properties?.name || `${minutes}分鐘`,
				},
			});
		});
	});

	return {
		type: "FeatureCollection",
		features: [...enrichedIsochrones, ...passthrough],
	};
}

export function getIsochroneLegendMinutes(legendFilter) {
	if (!legendFilter) return null;
	const value = legendFilter[2];
	if (typeof value === "number") return value;
	if (typeof value !== "string") return null;
	const match = value.match(/\d+/);
	return match ? Number(match[0]) : null;
}

export function getIsochroneAreaLegendFilter(legendFilter) {
	const legendMinutes = getIsochroneLegendMinutes(legendFilter);
	if (legendMinutes !== null) {
		return ["<=", ["get", "minutes"], legendMinutes];
	}
	return legendFilter;
}

export function buildIsochroneAreaFilter(timeSlot, legendFilter = null) {
	const baseFilter = [
		"==",
		["get", "layer"],
		IsochroneMapConfig.layers.featureLayers.isochrone,
	];
	const timeFilter = ["==", ["get", "time_slot"], timeSlot];
	if (legendFilter) {
		return ["all", baseFilter, timeFilter, getIsochroneAreaLegendFilter(legendFilter)];
	}
	return ["all", baseFilter, timeFilter];
}

export function buildIsochroneInitialAreaFilter(timeSlot) {
	const baseFilter = [
		"==",
		["get", "layer"],
		IsochroneMapConfig.layers.featureLayers.isochrone,
	];
	if (!timeSlot) return baseFilter;
	return [
		"all",
		baseFilter,
		[
			"any",
			["!", ["has", "time_slot"]],
			["==", ["get", "time_slot"], timeSlot],
		],
	];
}

export function buildIsochroneNetworkFilter(geometryType, selectedModes, timeSlot, legendFilter = null) {
	const filterParts = [
		[
			"==",
			["get", "layer"],
			IsochroneMapConfig.layers.featureLayers.network,
		],
		["==", ["geometry-type"], geometryType],
		["!=", ["get", "transit_type"], IsochroneMapConfig.layers.walkTransitType],
		["in", ["get", "transit_type"], ["literal", selectedModes]],
	];
	if (timeSlot) {
		filterParts.push(["==", ["get", "time_slot"], timeSlot]);
	}
	const legendMinutes = getIsochroneLegendMinutes(legendFilter);
	if (legendMinutes !== null) {
		filterParts.push(["<=", ["get", "minutes"], legendMinutes]);
	}
	return ["all", ...filterParts];
}

export function buildIsochroneLayerDefinitions(mapConfig, sourceId, options = {}) {
	const ids = getIsochroneLayerIds(mapConfig.layerId);
	const selectedModes = options.selectedModes || IsochroneMapConfig.defaults.modes;
	const showNetwork = Boolean(options.showNetwork);
	const defaultTimeSlot = options.defaultTimeSlot;
	const areaFilter = buildIsochroneInitialAreaFilter(defaultTimeSlot);

	return [
		{
			id: ids.area,
			type: "fill",
			source: sourceId,
			layout: {
				"fill-sort-key": [
					"-",
					0,
					["coalesce", ["get", "cutoff"], 0],
				],
			},
			paint: {
				"fill-color": [
					"coalesce",
					["get", "color"],
					mapConfig.paint?.["fill-color"] || IsochroneMapConfig.colors.default,
				],
				"fill-opacity":
					mapConfig.paint?.["fill-opacity"] ?? IsochroneMapConfig.paint.areaOpacity,
			},
			filter: areaFilter,
		},
		{
			id: ids.network,
			type: "line",
			source: sourceId,
			layout: {
				visibility: showNetwork ? "visible" : "none",
			},
			paint: {
				"line-color": [
					"coalesce",
					["get", "stroke"],
					IsochroneMapConfig.colors.network,
				],
				"line-width":
					mapConfig.paint?.["line-width"] ?? IsochroneMapConfig.paint.networkWidth,
				"line-opacity":
					mapConfig.paint?.["line-opacity"] ??
					IsochroneMapConfig.paint.networkOpacity,
			},
			filter: buildIsochroneNetworkFilter("LineString", selectedModes),
		},
		{
			id: ids.outline,
			type: "line",
			source: sourceId,
			paint: {
				"line-color": IsochroneMapConfig.colors.outline,
				"line-width": IsochroneMapConfig.paint.outlineWidth,
				"line-opacity": IsochroneMapConfig.paint.outlineOpacity,
			},
			filter: areaFilter,
		},
		{
			id: ids.networkStops,
			type: "circle",
			source: sourceId,
			layout: {
				visibility: showNetwork ? "visible" : "none",
			},
			paint: {
				"circle-radius": IsochroneMapConfig.paint.stopRadius,
				"circle-color": [
					"coalesce",
					["get", "stroke"],
					IsochroneMapConfig.colors.network,
				],
				"circle-stroke-width": IsochroneMapConfig.paint.stopStrokeWidth,
				"circle-stroke-color": IsochroneMapConfig.colors.outline,
				"circle-opacity": IsochroneMapConfig.paint.stopOpacity,
			},
			filter: buildIsochroneNetworkFilter("Point", selectedModes),
		},
	];
}

export function buildIsochroneStopsMapConfig(mapConfig) {
	const ids = getIsochroneLayerIds(mapConfig.layerId);
	return {
		...mapConfig,
		type: "circle",
		layerId: ids.networkStops,
		isIsochroneAux: true,
		title: IsochroneMapConfig.auxProperties.stopsTitle,
		property:
			mapConfig.paint?.stops_property ||
			IsochroneMapConfig.auxProperties.stopsProperty,
	};
}
