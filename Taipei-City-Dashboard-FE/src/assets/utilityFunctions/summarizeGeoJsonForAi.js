function parsePopupFields(propertyConfig) {
	if (!propertyConfig || typeof propertyConfig !== "string") return [];

	return [
		...new Set(
			propertyConfig
				.split(/[\n,]/)
				.map((field) => field.trim())
				.filter(Boolean),
		),
	];
}

function visitCoordinates(coordinates, visitor) {
	if (!Array.isArray(coordinates)) return;

	if (
		coordinates.length >= 2 &&
		typeof coordinates[0] === "number" &&
		typeof coordinates[1] === "number"
	) {
		visitor(coordinates[0], coordinates[1]);
		return;
	}

	coordinates.forEach((item) => visitCoordinates(item, visitor));
}

function getFeatureBbox(features) {
	let minLng = Infinity;
	let minLat = Infinity;
	let maxLng = -Infinity;
	let maxLat = -Infinity;

	features.forEach((feature) => {
		visitCoordinates(feature?.geometry?.coordinates, (lng, lat) => {
			minLng = Math.min(minLng, lng);
			minLat = Math.min(minLat, lat);
			maxLng = Math.max(maxLng, lng);
			maxLat = Math.max(maxLat, lat);
		});
	});

	if (
		!Number.isFinite(minLng) ||
		!Number.isFinite(minLat) ||
		!Number.isFinite(maxLng) ||
		!Number.isFinite(maxLat)
	) {
		return null;
	}

	return {
		minLng,
		minLat,
		maxLng,
		maxLat,
	};
}

function getRepresentativeFields(propertyKeys, popupFields) {
	if (popupFields.length) {
		return popupFields.filter((field) => propertyKeys.includes(field));
	}

	const preferredFields = [
		"name",
		"title",
		"label",
		"type",
		"category",
		"status",
		"district",
		"town",
		"village",
		"value",
		"count",
	];

	const prioritized = preferredFields.filter((field) =>
		propertyKeys.includes(field),
	);

	if (prioritized.length) return prioritized;

	return propertyKeys.slice(0, 8);
}

function summarizeFieldValues(values, maxCategories) {
	if (!values.length) return null;

	const numericValues = values
		.map((value) => Number(value))
		.filter((value) => !Number.isNaN(value));

	if (numericValues.length >= Math.ceil(values.length * 0.8)) {
		const sum = numericValues.reduce((acc, value) => acc + value, 0);
		return {
			type: "numeric",
			count: numericValues.length,
			min: Math.min(...numericValues),
			max: Math.max(...numericValues),
			avg: Number((sum / numericValues.length).toFixed(2)),
		};
	}

	const counter = {};
	values.forEach((value) => {
		const label = String(value);
		counter[label] = (counter[label] || 0) + 1;
	});

	return {
		type: "categorical",
		count: values.length,
		topValues: Object.entries(counter)
			.sort((a, b) => b[1] - a[1])
			.slice(0, maxCategories)
			.map(([value, count]) => ({ value, count })),
	};
}

export function summarizeGeoJsonForAi(geojson, mapConfig = {}, options = {}) {
	const { sampleSize = 5, maxCategories = 5 } = options;
	const features = Array.isArray(geojson?.features) ? geojson.features : [];
	const geometryTypes = [
		...new Set(
			features.map((feature) => feature?.geometry?.type).filter(Boolean),
		),
	];
	const allProperties = features
		.map((feature) => feature?.properties || {})
		.filter((properties) => Object.keys(properties).length > 0);
	const propertyKeys = [
		...new Set(allProperties.flatMap((properties) => Object.keys(properties))),
	];
	const popupFields = parsePopupFields(mapConfig.property);
	const representativeFields = getRepresentativeFields(
		propertyKeys,
		popupFields,
	);

	const fieldStats = representativeFields.reduce((acc, field) => {
		const values = allProperties
			.map((properties) => properties[field])
			.filter((value) => value !== null && value !== undefined && value !== "");
		const summary = summarizeFieldValues(values, maxCategories);
		if (summary) acc[field] = summary;
		return acc;
	}, {});

	const samples = features.slice(0, sampleSize).map((feature) => {
		const sampleProperties = representativeFields.reduce((acc, field) => {
			if (feature?.properties?.[field] !== undefined) {
				acc[field] = feature.properties[field];
			}
			return acc;
		}, {});

		return {
			geometryType: feature?.geometry?.type || null,
			properties: sampleProperties,
		};
	});

	return {
		layerIndex: mapConfig.index || "",
		layerTitle: mapConfig.title || "",
		layerType: mapConfig.type || "",
		featureCount: features.length,
		geometryTypes,
		bbox: getFeatureBbox(features),
		propertyKeys,
		popupFields,
		representativeFields,
		fieldStats,
		samples,
		paint: mapConfig.paint || "",
	};
}

export function buildMapSummaryPromptPayload(component, layerSummaries) {
	return {
		component: {
			name: component?.name || "",
			city: component?.city || "",
			short_desc: component?.short_desc || "",
			long_desc: component?.long_desc || "",
			time_from: component?.time_from || "",
			updated_at: component?.updated_at || "",
		},
		mapLayers: layerSummaries,
	};
}
