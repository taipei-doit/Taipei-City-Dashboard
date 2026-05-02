// Developed by Taipei Urban Intelligence Center 2023-2024

/* mapStore */
/*
The mapStore controls the map and includes methods to modify it.

!! PLEASE BE SURE TO REFERENCE THE MAPBOX DOCUMENTATION IF ANYTHING IS UNCLEAR !!
https://docs.mapbox.com/mapbox-gl-js/guides/
*/

/* global gtag */
import { createApp, defineComponent, nextTick, ref, watch, markRaw } from "vue";
import { defineStore } from "pinia";
import mapboxGl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import Hls from "hls.js";
import { ArcLayer } from "@deck.gl/layers";
import { MapboxOverlay } from "@deck.gl/mapbox";
import axios from "axios";
import http from "../router/axios.js";
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { FBXLoader } from "three/examples/jsm/loaders/FBXLoader.js";
import { TDSLoader } from "three/examples/jsm/loaders/TDSLoader.js";
import { point, distance } from "@turf/turf";

// Other Stores
import { useAuthStore } from "./authStore";
import { useDialogStore } from "./dialogStore";

// Vue Components
import MapPopup from "../components/map/MapPopup.vue";

// Utility Functions or Configs
import {
	MapObjectConfig,
	CityMapView,
	metroTaipeiTown,
	metroTaipeiVillage,
	metroTpDistrict,
	metroTpVillage,
	maplayerCommonLayout,
	maplayerCommonPaint,
} from "../assets/configs/mapbox/mapConfig.js";
import mapStyle from "../assets/configs/mapbox/mapStyle.js";
import { hexToRGB } from "../assets/utilityFunctions/colorConvert.js";
import { interpolation } from "../assets/utilityFunctions/interpolation.js";
import { marchingSquare } from "../assets/utilityFunctions/marchingSquare.js";
import { voronoi } from "../assets/utilityFunctions/voronoi.js";
import { calculateHaversineDistance } from "../assets/utilityFunctions/calculateHaversineDistance";
import { AnimatedArcLayer } from "../assets/configs/mapbox/arcAnimate.js";
// 3D Mrt Map 相關 Utility Functions
import { cutRouteSegment } from "../assets/utilityFunctions/getRouteForAnimation.js";
import { interpolateAlongSegment } from "../assets/utilityFunctions/geometryUtils.js";
import { updateCarsPosition } from "../assets/utilityFunctions/mrtCars.js";
import { getPopupCoordinates } from "../assets/utilityFunctions/getPopupCoordinates.js";
import {
	getCrowdColor,
	mrtLineColor,
} from "../assets/utilityFunctions/getThematicColor.js";
import {
	extractRoadNameFromAddress,
	findTaipeiRoadSpeedLimit,
} from "../assets/utilityFunctions/roadSpeedLimit.js";

function safelySetPaintProperty(map, layerId, property, value) {
	try {
		map.setPaintProperty(layerId, property, value);
	} catch {
		// Some style properties are only available on newer Mapbox GL versions.
	}
}

const mapImageNames = [
	"metro",
	"triangle_green",
	"triangle_white",
	"bike_green",
	"bike_orange",
	"bike_red",
	"cctv",
	"live",
	"youbike_elec",
];

const mrtModelConfigs = [
	{ id: "mrt_car_c381", url: "/images/map/mrt_car_c381.glb" },
	{ id: "mrt_car_c370", url: "/images/map/mrt_car_c370.glb" },
];

const ENABLE_AWWWARDS_MAP_STYLE = false;
const PERFORMANCE_STYLE_LAYER_IDS = new Set([
	"land",
	"water",
	"waterway",
	"admin-1-boundary",
	"admin-0-boundary",
	"road-motorway-trunk-navigation",
	"road-primary-navigation",
	"road-secondary-tertiary-navigation",
	"bridge-motorway-trunk-navigation",
	"bridge-primary-navigation",
	"bridge-secondary-tertiary-navigation",
	"road-label-navigation",
	"settlement-subdivision-label",
	"settlement-minor-label",
	"settlement-major-label",
]);
const MOVING_LABEL_LAYER_IDS = [
	"road-label-navigation",
	"settlement-subdivision-label",
	"settlement-minor-label",
	"settlement-major-label",
	"state-label",
	"country-label",
	"metrotaipei_town_label",
	"metrotaipei_village_label",
	"cinematic-map-labels",
];

const SIMPLE_ROUTE_SOURCE_ID = "simple-navigation-route-source";
const SIMPLE_ROUTE_LAYER_IDS = [
	"simple-navigation-route-case",
	"simple-navigation-route-glow",
	"simple-navigation-route-line",
];
const SIMPLE_ROUTE_CAR_SOURCE_ID = "simple-navigation-car-source";
const SIMPLE_ROUTE_CAR_LAYER_IDS = [
	"simple-navigation-car-layer",
];
const SIMPLE_ROUTE_SEARCH_BBOX = MapObjectConfig.maxBounds.flat().join(",");
const SIMPLE_ROUTE_SEARCH_PROXIMITY = "121.536609,25.044808";
const SIMPLE_ROUTE_SEARCH_TYPES = [
	"poi",
	"address",
	"street",
	"place",
	"city",
	"locality",
	"neighborhood",
	"district",
].join(",");
const SIMPLE_ROUTE_VEHICLE_MODELS = {
	default: {
		label: "cybertruck",
		loader: "fbx",
		url: "/cybertruck.fbx",
		lengthMeters: 132,
		altitudeMeters: 4,
		removeNames: ["Plane002"],
	},
	"mapbox/cycling": {
		label: "scooter",
		loader: "3ds",
		url: "/scooter.3DS",
		lengthMeters: 92,
		altitudeMeters: 3,
		orientation: [
			{ axis: "z", radians: Math.PI / 2 },
			{ axis: "z", radians: Math.PI },
			{ axis: "x", radians: -Math.PI / 2 },
		],
	},
};
const SIMPLE_ROUTE_CAR_BASE_ZOOM = 14.5;
const SIMPLE_ROUTE_CAR_MIN_SCALE = 0.5;
const SIMPLE_ROUTE_CAR_MAX_SCALE = 7;
const SIMPLE_ROUTE_CAR_MIN_DURATION_MS = 9000;
const SIMPLE_ROUTE_CAR_MAX_DURATION_MS = 36000;
const SIMPLE_ROUTE_CAR_MS_PER_METER = 2.6;
const SIMPLE_ROUTE_FIRST_PERSON_FORWARD_METERS = 0;
const SIMPLE_ROUTE_FIRST_PERSON_PITCH = 78;
const SIMPLE_ROUTE_FIRST_PERSON_ZOOM = 17.2;
const SIMPLE_ROUTE_FIRST_PERSON_UPDATE_INTERVAL_MS = 0;
const SIMPLE_ROUTE_SPEED_LIMIT_LOOKUP_THROTTLE_MS = 1800;
const ROAD_NAME_LOOKUP_API_URL = "/map_engine/search.ashx";
const SIMPLE_ROUTE_PROFILES = [
	"mapbox/driving",
	"mapbox/walking",
	"mapbox/cycling",
];

function createInitialRoadSpeedLimitState() {
	return {
		status: "idle",
		roadName: "",
		address: "",
		speedLimit: "",
		speedLimitText: "",
		category: "",
		segment: "",
		isDefault: false,
		isMultiple: false,
		updatedAt: null,
		error: "",
	};
}
const FUTURE_HOUR_RAIN_LAYER_INDEX = "future_hour_rain";
const RAIN_ANIMATION_LAYER_SUFFIX = "-rain-animation";
const RAIN_ANIMATION_MIN_DROPS = 1200;
const RAIN_ANIMATION_MAX_DROPS = 5200;
const RAIN_ANIMATION_DROP_FACTOR = 0.95;
const RAIN_ANIMATION_AVG_DROP_FACTOR = 2600;
const RAIN_VERTEX_SHADER = `
uniform float uTime;

attribute vec2 aRainInfo;
attribute vec4 aRainMotion;
attribute vec4 aRainTiming;

varying float vRainAlpha;
varying float vRainIntensity;

void main() {
	float meterScale = aRainInfo.x;
	float intensity = aRainInfo.y;
	float lengthMeters = aRainMotion.x;
	float topAltitudeMeters = aRainMotion.y;
	float spanMeters = topAltitudeMeters + lengthMeters + 420.0;
	float fallingMeters = mod(
		uTime * aRainTiming.x + aRainTiming.y * spanMeters,
		spanMeters
	);
	float fallProgress = fallingMeters / spanMeters;
	float role = aRainTiming.z;
	float headAltitudeMeters = topAltitudeMeters - fallingMeters;
	float altitudeMeters = headAltitudeMeters - (1.0 - role) * lengthMeters;
	float gust = sin(
		uTime * (1.2 + intensity * 1.7) +
		aRainTiming.w * 6.2831853 +
		fallProgress * 7.0
	) * (14.0 + intensity * 48.0);
	vec3 animatedPosition = position;

	animatedPosition.x +=
		(aRainMotion.z * fallProgress + gust) * meterScale;
	animatedPosition.y +=
		(aRainMotion.w * fallProgress - gust * 0.28) * meterScale;
	animatedPosition.z = altitudeMeters * meterScale;

	float groundFade = smoothstep(-220.0, 140.0, altitudeMeters);
	float skyFade =
		1.0 -
		smoothstep(
			topAltitudeMeters - lengthMeters * 0.35,
			topAltitudeMeters + 40.0,
			altitudeMeters
		);
	float headBrightness = mix(0.42, 1.0, role);

	vRainIntensity = intensity;
	vRainAlpha =
		(0.18 + intensity * 0.7) *
		groundFade *
		skyFade *
		headBrightness;

	gl_Position =
		projectionMatrix * modelViewMatrix * vec4(animatedPosition, 1.0);
}
`;
const RAIN_FRAGMENT_SHADER = `
uniform float uOpacity;

varying float vRainAlpha;
varying float vRainIntensity;

void main() {
	vec3 farRain = vec3(0.46, 0.72, 0.98);
	vec3 nearRain = vec3(0.9, 0.97, 1.0);
	vec3 rainColor = mix(farRain, nearRain, vRainIntensity);

	gl_FragColor = vec4(rainColor, vRainAlpha * uOpacity);
}
`;

function clampNumber(value, min, max) {
	return Math.max(min, Math.min(max, value));
}

function getRainAnimationLayerId(mapLayerId) {
	return `${mapLayerId}${RAIN_ANIMATION_LAYER_SUFFIX}`;
}

function seededRandom(seed) {
	const value = Math.sin(seed * 12.9898) * 43758.5453;
	return value - Math.floor(value);
}

function visitLngLatCoordinates(coordinates, callback) {
	if (!Array.isArray(coordinates)) return;
	if (
		typeof coordinates[0] === "number" &&
		typeof coordinates[1] === "number"
	) {
		callback(coordinates);
		return;
	}
	coordinates.forEach((coordinate) =>
		visitLngLatCoordinates(coordinate, callback),
	);
}

function getGeometryLngLatBbox(geometry) {
	if (!geometry?.coordinates) return null;
	const bbox = {
		minLng: Infinity,
		minLat: Infinity,
		maxLng: -Infinity,
		maxLat: -Infinity,
	};

	visitLngLatCoordinates(geometry.coordinates, ([lng, lat]) => {
		if (!Number.isFinite(lng) || !Number.isFinite(lat)) return;
		bbox.minLng = Math.min(bbox.minLng, lng);
		bbox.minLat = Math.min(bbox.minLat, lat);
		bbox.maxLng = Math.max(bbox.maxLng, lng);
		bbox.maxLat = Math.max(bbox.maxLat, lat);
	});

	if (!Number.isFinite(bbox.minLng) || !Number.isFinite(bbox.minLat)) {
		return null;
	}
	return bbox;
}

function getRainFeatureEntries(data) {
	const features = Array.isArray(data?.features) ? data.features : [];
	const entries = features
		.map((feature) => {
			const rain = Number(feature?.properties?.rain);
			const bbox = getGeometryLngLatBbox(feature?.geometry);
			if (!Number.isFinite(rain) || rain <= 0 || !bbox) return null;
			return {
				bbox,
				rain,
				weight: Math.max(4, rain ** 1.32),
			};
		})
		.filter(Boolean);

	if (!entries.length) return null;

	const stats = entries.reduce(
		(result, entry) => {
			result.maxRain = Math.max(result.maxRain, entry.rain);
			result.totalRain += entry.rain;
			result.totalWeight += entry.weight;
			result.cumulativeWeights.push(result.totalWeight);
			return result;
		},
		{
			maxRain: 0,
			totalRain: 0,
			totalWeight: 0,
			cumulativeWeights: [],
		},
	);

	stats.averageRain = stats.totalRain / entries.length;
	return { entries, stats };
}

function pickWeightedRainEntry(entries, cumulativeWeights, targetWeight) {
	let low = 0;
	let high = cumulativeWeights.length - 1;

	while (low < high) {
		const mid = Math.floor((low + high) / 2);
		if (targetWeight <= cumulativeWeights[mid]) {
			high = mid;
		} else {
			low = mid + 1;
		}
	}
	return entries[low];
}

function createRainDropDescriptors(data) {
	const rainData = getRainFeatureEntries(data);
	if (!rainData) return null;

	const { entries, stats } = rainData;
	const averageIntensity = clampNumber(
		stats.averageRain / Math.max(stats.maxRain, 1),
		0,
		1,
	);
	const dropCount = Math.round(
		clampNumber(
			entries.length * RAIN_ANIMATION_DROP_FACTOR +
				averageIntensity * RAIN_ANIMATION_AVG_DROP_FACTOR,
			RAIN_ANIMATION_MIN_DROPS,
			RAIN_ANIMATION_MAX_DROPS,
		),
	);

	const drops = Array.from({ length: dropCount }, (_, index) => {
		const entry = pickWeightedRainEntry(
			entries,
			stats.cumulativeWeights,
			seededRandom(index + 19) * stats.totalWeight,
		);
		const intensity = clampNumber(
			entry.rain / Math.max(stats.maxRain, 1),
			0.08,
			1,
		);
		const lng =
			entry.bbox.minLng +
			(entry.bbox.maxLng - entry.bbox.minLng) *
				seededRandom(index * 7 + 3);
		const lat =
			entry.bbox.minLat +
			(entry.bbox.maxLat - entry.bbox.minLat) *
				seededRandom(index * 11 + 5);
		const mercator = mapboxGl.MercatorCoordinate.fromLngLat([lng, lat], 0);

		return {
			x: mercator.x,
			y: mercator.y,
			meterScale: mercator.meterInMercatorCoordinateUnits(),
			intensity,
			lengthMeters:
				180 + intensity * 540 + seededRandom(index * 13 + 7) * 190,
			topAltitudeMeters:
				340 + intensity * 420 + seededRandom(index * 17 + 11) * 980,
			windXMeters:
				-55 -
				intensity * 135 +
				(seededRandom(index * 19 + 13) - 0.5) * 42,
			windYMeters: 18 + seededRandom(index * 23 + 17) * 72,
			speedMetersPerSecond:
				760 + intensity * 1420 + seededRandom(index * 29 + 23) * 520,
			phase: seededRandom(index * 31 + 29),
			shimmer: seededRandom(index * 37 + 31),
		};
	});

	return {
		averageIntensity,
		drops,
	};
}

function createRainAnimationGeometry(drops) {
	const vertexCount = drops.length * 2;
	const positions = new Float32Array(vertexCount * 3);
	const rainInfo = new Float32Array(vertexCount * 2);
	const rainMotion = new Float32Array(vertexCount * 4);
	const rainTiming = new Float32Array(vertexCount * 4);

	drops.forEach((drop, dropIndex) => {
		for (let vertexOffset = 0; vertexOffset < 2; vertexOffset++) {
			const vertexIndex = dropIndex * 2 + vertexOffset;
			const positionStride = vertexIndex * 3;
			const infoStride = vertexIndex * 2;
			const motionStride = vertexIndex * 4;
			const timingStride = vertexIndex * 4;

			positions[positionStride] = drop.x;
			positions[positionStride + 1] = drop.y;
			positions[positionStride + 2] = 0;
			rainInfo[infoStride] = drop.meterScale;
			rainInfo[infoStride + 1] = drop.intensity;
			rainMotion[motionStride] = drop.lengthMeters;
			rainMotion[motionStride + 1] = drop.topAltitudeMeters;
			rainMotion[motionStride + 2] = drop.windXMeters;
			rainMotion[motionStride + 3] = drop.windYMeters;
			rainTiming[timingStride] = drop.speedMetersPerSecond;
			rainTiming[timingStride + 1] = drop.phase;
			rainTiming[timingStride + 2] = vertexOffset === 0 ? 1 : 0;
			rainTiming[timingStride + 3] = drop.shimmer;
		}
	});

	const geometry = new THREE.BufferGeometry();
	geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
	geometry.setAttribute("aRainInfo", new THREE.BufferAttribute(rainInfo, 2));
	geometry.setAttribute(
		"aRainMotion",
		new THREE.BufferAttribute(rainMotion, 4),
	);
	geometry.setAttribute(
		"aRainTiming",
		new THREE.BufferAttribute(rainTiming, 4),
	);
	return geometry;
}

function createRainAnimationLayer(layerId, data) {
	const descriptorData = createRainDropDescriptors(data);
	if (!descriptorData) return null;
	const { averageIntensity, drops } = descriptorData;

	const customLayer = {
		id: layerId,
		type: "custom",
		renderingMode: "3d",
		visible: true,
		startedAt: performance.now(),
		onAdd(map, gl) {
			customLayer.map = markRaw(map);
			customLayer.camera = markRaw(new THREE.Camera());
			customLayer.scene = markRaw(new THREE.Scene());
			customLayer.geometry = markRaw(createRainAnimationGeometry(drops));
			customLayer.material = markRaw(
				new THREE.ShaderMaterial({
					uniforms: {
						uTime: { value: 0 },
						uOpacity: { value: 0.38 + averageIntensity * 0.26 },
					},
					vertexShader: RAIN_VERTEX_SHADER,
					fragmentShader: RAIN_FRAGMENT_SHADER,
					transparent: true,
					blending: THREE.AdditiveBlending,
					depthTest: false,
					depthWrite: false,
					toneMapped: false,
				}),
			);
			customLayer.rainLines = markRaw(
				new THREE.LineSegments(
					customLayer.geometry,
					customLayer.material,
				),
			);
			customLayer.rainLines.frustumCulled = false;
			customLayer.scene.add(customLayer.rainLines);
			customLayer.renderer = markRaw(
				new THREE.WebGLRenderer({
					canvas: map.getCanvas(),
					context: gl,
					antialias: false,
				}),
			);
			customLayer.renderer.autoClear = false;
			customLayer.renderer.sortObjects = false;
		},
		onRemove() {
			customLayer.geometry?.dispose?.();
			customLayer.material?.dispose?.();
			customLayer.scene?.remove?.(customLayer.rainLines);
			customLayer.map = null;
			customLayer.camera = null;
			customLayer.scene = null;
			customLayer.geometry = null;
			customLayer.material = null;
			customLayer.rainLines = null;
			customLayer.renderer = null;
		},
		render(gl, matrix) {
			if (
				!customLayer.visible ||
				!customLayer.camera ||
				!customLayer.geometry ||
				!customLayer.renderer ||
				!customLayer.scene
			) {
				return;
			}

			customLayer.material.uniforms.uTime.value =
				(performance.now() - customLayer.startedAt) / 1000;
			customLayer.camera.projectionMatrix =
				new THREE.Matrix4().fromArray(matrix);
			customLayer.renderer.resetState();
			customLayer.renderer.render(
				customLayer.scene,
				customLayer.camera,
			);
			customLayer.map?.triggerRepaint?.();
		},
	};

	return customLayer;
}

function getSimpleRouteCarScale(zoom) {
	const scale = 2 ** (SIMPLE_ROUTE_CAR_BASE_ZOOM - Number(zoom));
	if (!Number.isFinite(scale)) return 1;
	return clampNumber(
		scale,
		SIMPLE_ROUTE_CAR_MIN_SCALE,
		SIMPLE_ROUTE_CAR_MAX_SCALE,
	);
}

function getSimpleRouteCarDuration(distanceMeters) {
	const duration = Number(distanceMeters) * SIMPLE_ROUTE_CAR_MS_PER_METER;
	if (!Number.isFinite(duration)) return SIMPLE_ROUTE_CAR_MIN_DURATION_MS;
	return clampNumber(
		duration,
		SIMPLE_ROUTE_CAR_MIN_DURATION_MS,
		SIMPLE_ROUTE_CAR_MAX_DURATION_MS,
	);
}

function getSimpleRouteVehicleModel(profile) {
	return (
		SIMPLE_ROUTE_VEHICLE_MODELS[profile] ||
		SIMPLE_ROUTE_VEHICLE_MODELS.default
	);
}

function normalizeMapBearing(bearing) {
	return ((((bearing % 360) + 540) % 360) - 180);
}

function getSimpleRouteBearing(routeSample) {
	return normalizeMapBearing((routeSample.angle * 180) / Math.PI + 90);
}

function offsetSimpleRouteCoordinate(coordinate, angle, meters) {
	const center = mapboxGl.MercatorCoordinate.fromLngLat(coordinate, 0);
	const meterScale = center.meterInMercatorCoordinateUnits();
	const offset = new mapboxGl.MercatorCoordinate(
		center.x + Math.cos(angle) * meters * meterScale,
		center.y + Math.sin(angle) * meters * meterScale,
		0,
	);
	const lngLat = offset.toLngLat();
	return [lngLat.lng, lngLat.lat];
}

function getSimpleRouteFirstPersonCamera(routeSample) {
	return {
		center: offsetSimpleRouteCoordinate(
			routeSample.coordinate,
			routeSample.angle,
			SIMPLE_ROUTE_FIRST_PERSON_FORWARD_METERS,
		),
		zoom: SIMPLE_ROUTE_FIRST_PERSON_ZOOM,
		pitch: SIMPLE_ROUTE_FIRST_PERSON_PITCH,
		bearing: getSimpleRouteBearing(routeSample),
	};
}

function getSimpleRouteFeatureName(feature, fallbackName) {
	const properties = feature?.properties || {};
	const combinedName = [properties.name, properties.place_formatted]
		.filter(Boolean)
		.join("，");
	return (
		properties.name_preferred ||
		properties.full_address ||
		combinedName ||
		properties.name ||
		fallbackName
	);
}

function getSimpleRouteFeatureCoordinates(feature) {
	const propertyCoordinates = feature?.properties?.coordinates;
	const routablePoint = propertyCoordinates?.routable_points?.[0];
	const longitude =
		routablePoint?.longitude ??
		feature?.geometry?.coordinates?.[0] ??
		propertyCoordinates?.longitude;
	const latitude =
		routablePoint?.latitude ??
		feature?.geometry?.coordinates?.[1] ??
		propertyCoordinates?.latitude;

	if (
		!Number.isFinite(Number(longitude)) ||
		!Number.isFinite(Number(latitude))
	) {
		return null;
	}

	return [Number(longitude), Number(latitude)];
}

function normalizeSimpleRouteCoordinates(coordinates) {
	return coordinates
		.map((coordinate) => [
			Number(coordinate?.[0]),
			Number(coordinate?.[1]),
		])
		.filter(
			(coordinate, index, normalized) =>
				Number.isFinite(coordinate[0]) &&
				Number.isFinite(coordinate[1]) &&
				(index === 0 ||
					coordinate[0] !== normalized[index - 1][0] ||
					coordinate[1] !== normalized[index - 1][1]),
		);
}

function createSimpleRoutePath(coordinates) {
	const normalizedCoordinates = normalizeSimpleRouteCoordinates(coordinates);
	if (normalizedCoordinates.length < 2) return null;

	const points = normalizedCoordinates.map((coordinate) => ({
		coordinate,
		mercator: mapboxGl.MercatorCoordinate.fromLngLat(coordinate, 0),
	}));
	const segments = [];
	let totalLength = 0;

	for (let index = 0; index < points.length - 1; index++) {
		const from = points[index];
		const to = points[index + 1];
		const dx = to.mercator.x - from.mercator.x;
		const dy = to.mercator.y - from.mercator.y;
		const length = Math.hypot(dx, dy);

		if (length === 0) continue;

		segments.push({
			from,
			to,
			start: totalLength,
			end: totalLength + length,
			length,
			angle: Math.atan2(dy, dx),
		});
		totalLength += length;
	}

	if (!segments.length) return null;

	return {
		segments,
		totalLength,
	};
}

function interpolateSimpleRoutePath(routePath, progress) {
	const safeProgress = clampNumber(progress, 0, 1);
	const targetDistance = routePath.totalLength * safeProgress;
	const segment =
		routePath.segments.find((item) => targetDistance <= item.end) ||
		routePath.segments[routePath.segments.length - 1];
	const localProgress = clampNumber(
		(targetDistance - segment.start) / segment.length,
		0,
		1,
	);
	const lng =
		segment.from.coordinate[0] +
		(segment.to.coordinate[0] - segment.from.coordinate[0]) *
			localProgress;
	const lat =
		segment.from.coordinate[1] +
		(segment.to.coordinate[1] - segment.from.coordinate[1]) *
			localProgress;

	return {
		coordinate: [lng, lat],
		angle: segment.angle,
	};
}

function getCoordinateLookupKey(coordinate) {
	return coordinate
		.map((value) => Number(value).toFixed(5))
		.join(",");
}

function parseRoadNameLookupPayload(data) {
	if (!data) return {};
	if (typeof data === "object") return data;
	try {
		return JSON.parse(data);
	} catch {
		return {};
	}
}

function getRoadNameLookupAddress(data) {
	const payload = parseRoadNameLookupPayload(data);
	const firstResult = payload?.results?.[0] || {};

	return (
		payload.address ||
		payload.formatted_address ||
		firstResult.formatted_address ||
		firstResult.address ||
		firstResult.name ||
		""
	);
}

function disposeThreeObject(object) {
	object.traverse((child) => {
		if (!child.isMesh) return;
		child.geometry?.dispose?.();
		const materials = Array.isArray(child.material)
			? child.material
			: [child.material];
		materials.filter(Boolean).forEach((material) => material.dispose?.());
	});
}

function removeSimpleRouteModelExtras(model, modelConfig) {
	const extras = [];
	const removeNames = new Set(modelConfig.removeNames || []);
	model.traverse((child) => {
		if (
			child.isCamera ||
			child.isLight ||
			removeNames.has(child.name)
		) {
			extras.push(child);
		}
	});
	extras.forEach((child) => child.parent?.remove(child));
}

function orientSimpleRouteVehicleModel(model, modelConfig) {
	(modelConfig.orientation || []).forEach(({ axis, radians }) => {
		const vector =
			axis === "x"
				? new THREE.Vector3(1, 0, 0)
				: axis === "y"
					? new THREE.Vector3(0, 1, 0)
					: new THREE.Vector3(0, 0, 1);
		model.applyMatrix4(
			new THREE.Matrix4().makeRotationAxis(vector, radians),
		);
	});
}

function normalizeSimpleRouteVehicleModel(model, modelConfig) {
	removeSimpleRouteModelExtras(model, modelConfig);
	orientSimpleRouteVehicleModel(model, modelConfig);
	model.updateMatrixWorld(true);

	const box = new THREE.Box3().setFromObject(model);
	const size = new THREE.Vector3();
	const center = new THREE.Vector3();
	box.getSize(size);
	box.getCenter(center);

	if (!Number.isFinite(size.x) || size.x <= 0) {
		return createSimpleRouteFallbackCarModel();
	}

	model.position.x -= center.x;
	model.position.y -= box.min.y;
	model.position.z -= center.z;
	model.traverse((child) => {
		if (!child.isMesh) return;
		child.frustumCulled = false;
		const materials = Array.isArray(child.material)
			? child.material
			: [child.material];
		materials.filter(Boolean).forEach((material) => {
			material.side = THREE.DoubleSide;
			material.needsUpdate = true;
		});
	});

	const group = new THREE.Group();
	group.add(model);

	return {
		model: group,
		modelLengthUnits: size.x,
	};
}

function createSimpleRouteFallbackCarModel() {
	const group = new THREE.Group();
	const bodyMaterial = new THREE.MeshStandardMaterial({
		color: "#ff4ecb",
		roughness: 0.62,
		metalness: 0.18,
	});
	const cabinMaterial = new THREE.MeshStandardMaterial({
		color: "#f4f2eb",
		roughness: 0.48,
		metalness: 0.08,
	});
	const body = new THREE.Mesh(
		new THREE.BoxGeometry(1, 0.24, 0.34),
		bodyMaterial,
	);
	const cabin = new THREE.Mesh(
		new THREE.BoxGeometry(0.42, 0.22, 0.24),
		cabinMaterial,
	);
	body.position.y = 0.12;
	cabin.position.set(-0.05, 0.35, 0);
	group.add(body, cabin);

	return {
		model: group,
		modelLengthUnits: 1,
	};
}

function createSimpleRouteVehicleLoader(modelConfig) {
	if (modelConfig.loader === "3ds") {
		const loader = new TDSLoader();
		loader.setResourcePath("/");
		return loader;
	}
	return new FBXLoader();
}

function createSimpleRouteCarLayer(
	routePath,
	animationDuration,
	firstSample,
	modelConfig,
	options = {},
) {
	const customLayer = {
		id: SIMPLE_ROUTE_CAR_LAYER_IDS[0],
		type: "custom",
		renderingMode: "3d",
		startedAt: performance.now(),
		routePath,
		animationDuration,
		currentSample: firstSample,
		model: null,
		modelLengthUnits: 1,
		isRemoved: false,
		lastFirstPersonCameraUpdate: 0,
		shouldUseFirstPersonCamera:
			options.shouldUseFirstPersonCamera || (() => false),
		onRouteSample: options.onRouteSample || (() => {}),
		applyFirstPersonCamera(force = false) {
			if (
				!customLayer.map ||
				!customLayer.shouldUseFirstPersonCamera() ||
				!customLayer.currentSample
			) {
				return;
			}
			const now = performance.now();
			if (
				!force &&
				now - customLayer.lastFirstPersonCameraUpdate <
					SIMPLE_ROUTE_FIRST_PERSON_UPDATE_INTERVAL_MS
			) {
				return;
			}
			customLayer.lastFirstPersonCameraUpdate = now;
			customLayer.map.jumpTo({
				...getSimpleRouteFirstPersonCamera(
					customLayer.currentSample,
				),
				essential: true,
			});
		},
		onAdd(map, gl) {
			customLayer.map = markRaw(map);
			customLayer.camera = markRaw(new THREE.Camera());
			customLayer.scene = markRaw(new THREE.Scene());

			customLayer.scene.add(
				new THREE.HemisphereLight(0xffffff, 0x26213c, 2.2),
			);
			const keyLight = new THREE.DirectionalLight(0xffffff, 2.6);
			keyLight.position.set(-3, -4, 6);
			customLayer.scene.add(keyLight);

			customLayer.renderer = markRaw(
				new THREE.WebGLRenderer({
					canvas: map.getCanvas(),
					context: gl,
					antialias: true,
				}),
			);
			customLayer.renderer.autoClear = false;

			createSimpleRouteVehicleLoader(modelConfig).load(
				modelConfig.url,
				(model) => {
					const normalizedModel =
						normalizeSimpleRouteVehicleModel(model, modelConfig);
					if (customLayer.isRemoved) {
						disposeThreeObject(normalizedModel.model);
						return;
					}
					customLayer.model = markRaw(normalizedModel.model);
					customLayer.modelLengthUnits =
						normalizedModel.modelLengthUnits;
					customLayer.scene.add(customLayer.model);
					map.triggerRepaint();
				},
				undefined,
				(error) => {
					console.warn(
						`Failed to load simple route ${modelConfig.label} model.`,
						error,
					);
					const fallbackModel = createSimpleRouteFallbackCarModel();
					if (customLayer.isRemoved) {
						disposeThreeObject(fallbackModel.model);
						return;
					}
					customLayer.model = markRaw(fallbackModel.model);
					customLayer.modelLengthUnits =
						fallbackModel.modelLengthUnits;
					customLayer.scene.add(customLayer.model);
					map.triggerRepaint();
				},
			);
		},
		onRemove() {
			customLayer.isRemoved = true;
			if (customLayer.model) {
				customLayer.scene?.remove(customLayer.model);
				disposeThreeObject(customLayer.model);
			}
			customLayer.scene = null;
			customLayer.camera = null;
			customLayer.renderer = null;
			customLayer.model = null;
		},
		render(gl, matrix) {
			if (
				!customLayer.map ||
				!customLayer.scene ||
				!customLayer.camera ||
				!customLayer.renderer
			) {
				return;
			}

			const progress = clampNumber(
				(performance.now() - customLayer.startedAt) /
					customLayer.animationDuration,
				0,
				1,
			);
			const routeSample = interpolateSimpleRoutePath(
				customLayer.routePath,
				progress,
			);
			const isFirstPersonCamera =
				customLayer.shouldUseFirstPersonCamera();
			const renderSample = isFirstPersonCamera
				? customLayer.currentSample || routeSample
				: routeSample;
			if (!isFirstPersonCamera) {
				customLayer.currentSample = routeSample;
			}

			if (customLayer.model) {
				const mercator =
					mapboxGl.MercatorCoordinate.fromLngLat(
						renderSample.coordinate,
						modelConfig.altitudeMeters,
					);
				const zoomScale = getSimpleRouteCarScale(
					customLayer.map.getZoom(),
				);
				const modelScale =
					(mercator.meterInMercatorCoordinateUnits() *
						modelConfig.lengthMeters *
						zoomScale) /
					customLayer.modelLengthUnits;
				const rotationX = new THREE.Matrix4().makeRotationAxis(
					new THREE.Vector3(1, 0, 0),
					Math.PI / 2,
				);
				const rotationZ = new THREE.Matrix4().makeRotationZ(
					-renderSample.angle,
				);
				const translation = new THREE.Matrix4().makeTranslation(
					mercator.x,
					mercator.y,
					mercator.z,
				);
				const scaleMatrix = new THREE.Matrix4().makeScale(
					modelScale,
					-modelScale,
					modelScale,
				);
				const modelMatrix = new THREE.Matrix4()
					.multiply(translation)
					.multiply(scaleMatrix)
					.multiply(rotationZ)
					.multiply(rotationX);

				customLayer.camera.projectionMatrix = new THREE.Matrix4()
					.fromArray(matrix)
					.multiply(modelMatrix);
				customLayer.renderer.resetState();
				customLayer.renderer.render(
					customLayer.scene,
					customLayer.camera,
				);
			}

			if (isFirstPersonCamera) {
				customLayer.currentSample = routeSample;
				customLayer.onRouteSample(routeSample);
				customLayer.applyFirstPersonCamera();
			}

			if (progress < 1 || !customLayer.model) {
				customLayer.map.triggerRepaint();
			}
		},
	};

	return customLayer;
}

function isMotionLabelLayer(layer) {
	if (layer.type !== "symbol" || !layer.layout?.["text-field"]) {
		return false;
	}
	if (MOVING_LABEL_LAYER_IDS.includes(layer.id)) {
		return true;
	}

	const layerId = layer.id.toLowerCase();
	const sourceLayer = String(layer["source-layer"] || "").toLowerCase();
	const group = String(layer.metadata?.["mapbox:group"] || "").toLowerCase();
	const component = String(
		layer.metadata?.["mapbox:featureComponent"] || "",
	).toLowerCase();
	return (
		layerId.includes("metrotaipei") ||
		layerId.includes("district") ||
		layerId.includes("town") ||
		layerId.includes("village") ||
		layerId.includes("settlement") ||
		layerId.includes("road-label") ||
		sourceLayer === "place_label" ||
		group.includes("place labels") ||
		component.includes("place-labels")
	);
}

function getPerformanceMapStyle() {
	return {
		...mapStyle,
		layers: mapStyle.layers.filter((layer) =>
			PERFORMANCE_STYLE_LAYER_IDS.has(layer.id),
		),
	};
}

export const useMapStore = defineStore("map", {
	state: () => ({
		// Array of layer IDs that are in the map
		currentLayers: [],
		// Array of layer IDs that are in the map and currently visible
		currentVisibleLayers: [],
		// Stores all map configs for all layers (to be used to render popups)
		mapConfigs: {},
		// Stores the mapbox map instance
		map: null,
		// Store deck.gl layer overlay
		overlay: null,
		// Store deck.gl layer
		deckGlLayer: {},
		// Store Three.js rain animation layers keyed by their map layer id
		rainAnimationLayers: {},
		// Store animate step form 1 to 100
		step: 1,
		// Stores popup information
		popup: null,
		// Store currently loading layers,
		loadingLayers: [],
		// Store all view points
		viewPoints: [],
		marker: null,
		tempMarkerCoordinates: null,
		// Store the user's current location,
		userLocation: { latitude: null, longitude: null },
		// 3D Mrt Map 相關參數
		// 模型及圖徵是否預載中
		isPreloading: true,
		// 預載 3D 模型
		preloadedModels: {},
		// 前一包列車動畫資料
		prevMrtCars: [],
		// 儲存圖層更新時間
		layerUpdateTime: {
			// [layerId]: Date
		},
		pendingMapViewCity: "default",
		hasPlayedInitialReveal: false,
		hasAppliedCinematicStyle: false,
		cinematicPitch: MapObjectConfig.pitch,
		isArcAnimationRunning: false,
		arcAnimationFrame: null,
		hasLoadedDeferredMapData: false,
		labelRestoreTimer: null,
		hiddenMotionLabelLayers: {},
		navigationRouteMarkers: [],
		navigationRouteSummary: null,
		navigationRouteCarSample: null,
		navigationRouteCarLayer: null,
		navigationRouteCarZoomHandler: null,
		navigationRouteCarUpdateFrame: null,
		navigationRouteCarAnimationFrame: null,
		isSimpleRouteFirstPersonCamera: false,
		simpleRouteCameraSnapshot: null,
		currentRoadSpeedLimit: createInitialRoadSpeedLimitState(),
		lastRoadSpeedLimitLookupAt: 0,
		lastRoadSpeedLimitLookupKey: "",
		pendingRoadSpeedLimitCoordinate: null,
		roadSpeedLimitLookupTimer: null,
		roadSpeedLimitRequestId: 0,
	}),
	actions: {
		/* Initialize Mapbox */
		// 1. Creates the mapbox instance and passes in initial configs
		initializeMapBox() {
			this.clearSimpleRoute();
			this.map = null;
			this.marker = null;
			this.overlay = null;
			this.isPreloading = false;
			this.preloadedModels = {};
			this.deckGlLayer = {};
			this.rainAnimationLayers = {};
			this.isArcAnimationRunning = false;
			this.arcAnimationFrame = null;
			this.hasPlayedInitialReveal = false;
			this.hasAppliedCinematicStyle = false;
			this.hasLoadedDeferredMapData = false;
			this.labelRestoreTimer = null;
			this.hiddenMotionLabelLayers = {};
			this.navigationRouteMarkers = [];
			this.navigationRouteSummary = null;
			this.navigationRouteCarSample = null;
			this.navigationRouteCarLayer = null;
			this.navigationRouteCarZoomHandler = null;
			this.navigationRouteCarUpdateFrame = null;
			this.navigationRouteCarAnimationFrame = null;
			this.isSimpleRouteFirstPersonCamera = false;
			this.simpleRouteCameraSnapshot = null;
			this.resetCurrentRoadSpeedLimit();
			this.cinematicPitch = MapObjectConfig.pitch;
			const MAPBOXTOKEN = import.meta.env.VITE_MAPBOXTOKEN;
			mapboxGl.accessToken = MAPBOXTOKEN;
			this.map = new mapboxGl.Map({
				...MapObjectConfig,
				style: getPerformanceMapStyle(),
			});
			this.marker = new mapboxGl.Marker();
			this.map.doubleClickZoom.disable();
			let isFirstZoom = true;
			this.map
				.on("load", () => {
					if (!this.map) return;
					this.scheduleInitialMapReveal(this.pendingMapViewCity);
				})
				.on("styleimagemissing", (event) => {
					this.loadMapImage(event.id);
				})
				.on("movestart", () => {
					this.hideLabelsDuringMapMotion();
				})
				.on("zoomstart", () => {
					this.hideLabelsDuringMapMotion();
				})
				.on("rotatestart", () => {
					this.hideLabelsDuringMapMotion();
				})
				.on("pitchstart", () => {
					this.hideLabelsDuringMapMotion();
				})
				.on("dragstart", () => {
					this.hideLabelsDuringMapMotion();
				})
				.on("moveend", () => {
					this.scheduleLabelsAfterMapMotion();
				})
				.on("zoomend", () => {
					this.scheduleLabelsAfterMapMotion();
				})
				.on("rotateend", () => {
					this.scheduleLabelsAfterMapMotion();
				})
				.on("pitchend", () => {
					this.scheduleLabelsAfterMapMotion();
				})
				.on("dragend", () => {
					this.scheduleLabelsAfterMapMotion();
				})
				.on("click", (event) => {
					if (this.popup) {
						this.popup = null;
					}
					this.addPopup(event);
				})
				.on("dblclick", (event) => {
					let coordinates = event.lngLat;
					this.tempMarkerCoordinates = coordinates;
					this.marker.setLngLat(coordinates).addTo(this.map);
				})
				.on("idle", () => {
					this.loadingLayers = this.loadingLayers.filter(
						(el) => el !== "rendering",
					);
				})
				// 圖臺縮放時觸發GA自訂事件
				.on("zoomend", () => {
					if (isFirstZoom) {
						isFirstZoom = false;
					} else {
						gtag("event", "map_actions", {
							action_type: "地圖縮放",
							time: Date.now(),
						});
					}
				});
			this.renderMarkers();
			return null;
		},
		scheduleInitialMapReveal(city = "default") {
			if (!this.map || this.hasPlayedInitialReveal) return;
			const startReveal = () => {
				if (!this.map || this.hasPlayedInitialReveal) return;
				window.setTimeout(() => {
					if (!this.map || this.hasPlayedInitialReveal) return;
					this.playInitialMapReveal(
						this.pendingMapViewCity || city,
					);
				}, 120);
			};

			if (
				this.map.loaded() &&
				(typeof this.map.areTilesLoaded !== "function" ||
					this.map.areTilesLoaded())
			) {
				startReveal();
				return;
			}

			const fallbackTimer = window.setTimeout(startReveal, 1600);
			this.map.once("idle", () => {
				window.clearTimeout(fallbackTimer);
				startReveal();
			});
		},
		revealCinematicMapStyle() {
			if (!this.map || this.hasAppliedCinematicStyle) return;
			this.hasAppliedCinematicStyle = true;
			if (ENABLE_AWWWARDS_MAP_STYLE) {
				this.applyCinematicMapEffects();
				this.initializeCinematicMapAnnotations();
			}
			const idleLoad = window.requestIdleCallback || window.setTimeout;
			idleLoad(() => this.addSymbolSources());
			this.loadDeferredMapData();
		},
		setMapLayerVisibility(layerId, visibility) {
			if (!this.map?.getLayer(layerId)) return;
			try {
				this.map.setLayoutProperty(layerId, "visibility", visibility);
			} catch {
				// Layer visibility may fail while Mapbox is rebuilding the style.
			}
		},
		getMotionLabelLayerIds() {
			if (!this.map) return [];
			const layers = this.map.getStyle()?.layers || [];
			const layerIds = new Set(MOVING_LABEL_LAYER_IDS);
			layers.forEach((layer) => {
				if (isMotionLabelLayer(layer)) {
					layerIds.add(layer.id);
				}
			});
			return Array.from(layerIds).filter((layerId) =>
				this.map.getLayer(layerId),
			);
		},
		getMapLayerVisibility(layerId) {
			if (!this.map?.getLayer(layerId)) return null;
			try {
				return (
					this.map.getLayoutProperty(layerId, "visibility") ||
					"visible"
				);
			} catch {
				return null;
			}
		},
		hideLabelsDuringMapMotion() {
			if (!this.map) return;
			if (this.labelRestoreTimer) {
				window.clearTimeout(this.labelRestoreTimer);
				this.labelRestoreTimer = null;
			}
			const hiddenLayers = { ...this.hiddenMotionLabelLayers };
			this.getMotionLabelLayerIds().forEach((layerId) => {
				const currentVisibility = this.getMapLayerVisibility(layerId);
				if (!currentVisibility) return;
				if (currentVisibility === "none") return;
				hiddenLayers[layerId] = currentVisibility;
				this.setMapLayerVisibility(layerId, "none");
			});
			this.hiddenMotionLabelLayers = hiddenLayers;
		},
		scheduleLabelsAfterMapMotion() {
			if (!this.map) return;
			if (this.labelRestoreTimer) {
				window.clearTimeout(this.labelRestoreTimer);
			}
			this.labelRestoreTimer = window.setTimeout(() => {
				if (this.map?.isMoving()) {
					this.scheduleLabelsAfterMapMotion();
					return;
				}
				this.restoreLabelsAfterMapMotion();
			}, 160);
		},
		restoreLabelsAfterMapMotion() {
			if (!this.map) return;
			Object.entries(this.hiddenMotionLabelLayers).forEach(
				([layerId, visibility]) => {
					this.setMapLayerVisibility(layerId, visibility);
				},
			);
			this.hiddenMotionLabelLayers = {};
			this.labelRestoreTimer = null;
		},
		applyCinematicMapEffects() {
			if (!this.map) return;

			try {
				this.map.setFog({
					color: "rgb(8, 8, 9)",
					"high-color": "rgb(52, 52, 56)",
					"horizon-blend": 0.18,
					"space-color": "rgb(0, 0, 0)",
					"star-intensity": 0.35,
				});
			} catch {
				// Fog is a progressive enhancement for Mapbox GL.
			}

			const layers = this.map.getStyle()?.layers || [];
			layers.forEach((layer) => {
				if (layer.type === "background") {
					safelySetPaintProperty(
						this.map,
						layer.id,
						"background-color",
						"#020203",
					);
				}
				if (layer.type === "fill") {
					safelySetPaintProperty(
						this.map,
						layer.id,
						"fill-color",
						"#060607",
					);
					safelySetPaintProperty(
						this.map,
						layer.id,
						"fill-opacity",
						0.82,
					);
				}
				if (layer.type === "line") {
					safelySetPaintProperty(
						this.map,
						layer.id,
						"line-color",
						"#f2efe6",
					);
					safelySetPaintProperty(
						this.map,
						layer.id,
						"line-opacity",
						[
							"interpolate",
							["linear"],
							["zoom"],
							8,
							0.14,
							12,
							0.28,
							16,
							0.62,
						],
					);
					safelySetPaintProperty(
						this.map,
						layer.id,
						"line-blur",
						0.18,
					);
					safelySetPaintProperty(
						this.map,
						layer.id,
						"line-emissive-strength",
						0.9,
					);
				}
				if (layer.type === "symbol") {
					safelySetPaintProperty(
						this.map,
						layer.id,
						"text-color",
						"#f4f2eb",
					);
					safelySetPaintProperty(
						this.map,
						layer.id,
						"text-halo-color",
						"#050505",
					);
					safelySetPaintProperty(
						this.map,
						layer.id,
						"text-halo-width",
						1.2,
					);
					safelySetPaintProperty(
						this.map,
						layer.id,
						"text-opacity",
						0.62,
					);
					safelySetPaintProperty(
						this.map,
						layer.id,
						"icon-opacity",
						0.35,
					);
				}
				if (layer.type === "fill-extrusion") {
					safelySetPaintProperty(
						this.map,
						layer.id,
						"fill-extrusion-color",
						"#d7d4cb",
					);
					safelySetPaintProperty(
						this.map,
						layer.id,
						"fill-extrusion-opacity",
						0.44,
					);
					safelySetPaintProperty(
						this.map,
						layer.id,
						"fill-extrusion-emissive-strength",
						0.35,
					);
				}
			});
		},
		playInitialMapReveal(city = "default", force = false) {
			if (!this.map || (!force && this.hasPlayedInitialReveal)) return;
			const mapView = CityMapView[city] || CityMapView.default;
			const revealDuration = 1800;
			const minZoom =
				typeof this.map.getMinZoom === "function"
					? this.map.getMinZoom()
					: MapObjectConfig.minZoom;

			this.hasPlayedInitialReveal = true;
			this.cinematicPitch = 18;
			this.map.stop();
			this.map.jumpTo({
				center: [
					mapView.center[0] - 0.08,
					mapView.center[1] + 0.055,
				],
				zoom: Math.max(minZoom, mapView.zoom - 2.2),
				pitch: 18,
				bearing: mapView.bearing - 42,
			});

			window.setTimeout(() => {
				if (!this.map) return;
				const finishReveal = () => {
					if (!this.map) return;
					this.cinematicPitch = Math.round(this.map.getPitch());
					this.revealCinematicMapStyle();
					this.scheduleLabelsAfterMapMotion();
				};

				this.map.once("moveend", finishReveal);
				window.setTimeout(finishReveal, revealDuration + 360);
				this.cinematicPitch = mapView.pitch;
				this.map.easeTo({
					center: mapView.center,
					zoom: mapView.zoom,
					pitch: mapView.pitch,
					bearing: mapView.bearing,
					duration: revealDuration,
					essential: true,
				});
			}, 120);
		},
		initializeCinematicMapAnnotations() {
			if (!this.map) return;
			const annotationFeatures = [
				{
					label: "北投 / 士林",
					labelCoordinates: [121.47, 25.158],
					anchorCoordinates: [121.525, 25.12],
				},
				{
					label: "內湖 / 南港",
					labelCoordinates: [121.692, 25.088],
					anchorCoordinates: [121.62, 25.06],
				},
				{
					label: "都會核心",
					labelCoordinates: [121.596, 25.018],
					anchorCoordinates: [121.535, 25.044],
				},
				{
					label: "文山 / 南區",
					labelCoordinates: [121.478, 24.962],
					anchorCoordinates: [121.568, 24.998],
				},
			];
			const labelData = {
				type: "FeatureCollection",
				features: annotationFeatures.map((item) => ({
					type: "Feature",
					properties: {
						label: item.label,
					},
					geometry: {
						type: "Point",
						coordinates: item.labelCoordinates,
					},
				})),
			};
			const anchorData = {
				type: "FeatureCollection",
				features: annotationFeatures.map((item) => ({
					type: "Feature",
					properties: {
						label: item.label,
					},
					geometry: {
						type: "Point",
						coordinates: item.anchorCoordinates,
					},
				})),
			};
			const leaderData = {
				type: "FeatureCollection",
				features: annotationFeatures.map((item) => ({
					type: "Feature",
					properties: {
						label: item.label,
					},
					geometry: {
						type: "LineString",
						coordinates: [
							item.anchorCoordinates,
							item.labelCoordinates,
						],
					},
				})),
			};

			if (!this.map.getSource("cinematic-map-labels")) {
				this.map.addSource("cinematic-map-labels", {
					type: "geojson",
					data: labelData,
				});
			}
			if (!this.map.getSource("cinematic-map-anchors")) {
				this.map.addSource("cinematic-map-anchors", {
					type: "geojson",
					data: anchorData,
				});
			}
			if (!this.map.getSource("cinematic-map-leaders")) {
				this.map.addSource("cinematic-map-leaders", {
					type: "geojson",
					data: leaderData,
				});
			}

			if (!this.map.getLayer("cinematic-map-leaders")) {
				this.map.addLayer({
					id: "cinematic-map-leaders",
					type: "line",
					source: "cinematic-map-leaders",
					paint: {
						"line-color": "#f4f2eb",
						"line-width": [
							"interpolate",
							["linear"],
							["zoom"],
							8,
							0.45,
							14,
							1,
						],
						"line-opacity": [
							"interpolate",
							["linear"],
							["zoom"],
							8,
							0.22,
							12,
							0.58,
						],
					},
				});
			}
			if (!this.map.getLayer("cinematic-map-anchor-halo")) {
				this.map.addLayer({
					id: "cinematic-map-anchor-halo",
					type: "circle",
					source: "cinematic-map-anchors",
					paint: {
						"circle-radius": [
							"interpolate",
							["linear"],
							["zoom"],
							8,
							4,
							14,
							8,
						],
						"circle-color": "rgba(244, 242, 235, 0.2)",
						"circle-stroke-color": "#f4f2eb",
						"circle-stroke-width": 1,
						"circle-opacity": 0.75,
					},
				});
			}
			if (!this.map.getLayer("cinematic-map-labels")) {
				this.map.addLayer({
					id: "cinematic-map-labels",
					type: "symbol",
					source: "cinematic-map-labels",
					layout: {
						"text-field": ["get", "label"],
						"text-size": [
							"interpolate",
							["linear"],
							["zoom"],
							8,
							12,
							14,
							18,
						],
						"text-anchor": "center",
						"text-allow-overlap": true,
						"text-ignore-placement": true,
					},
					paint: {
						"text-color": "#f4f2eb",
						"text-halo-color": "#050505",
						"text-halo-width": 1.8,
						"text-opacity": [
							"interpolate",
							["linear"],
							["zoom"],
							8,
							0.54,
							12,
							0.92,
						],
					},
				});
			}
		},
		// 2. Adds three basic layers to the map (Taipei District, Taipei Village labels, and Taipei 3D Buildings)
		// Due to performance concerns, Taipei 3D Buildings won't be added in the mobile version
		initializeBasicLayers() {
			// Kept as a public action for compatibility. Base layers are now
			// lazy-loaded by the controls so the intro animation stays light.
			this.loadDeferredMapData();
		},
		loadDeferredMapData() {
			if (!this.map || this.hasLoadedDeferredMapData) return;
			this.hasLoadedDeferredMapData = true;
			this.addAdministrativeLabels();
			this.addBoundaryLayers();
		},
		addAdministrativeLabels() {
			if (!this.map) return;
			if (!this.map.getSource("metrotaipei_town_label")) {
				this.map.addSource("metrotaipei_town_label", {
					type: "geojson",
					data: "/mapData/metrotaipei_town.geojson",
				});
			}
			if (!this.map.getLayer("metrotaipei_town_label")) {
				this.map.addLayer(metroTaipeiTown);
			}
			if (!this.map.getSource("metrotaipei_village_label")) {
				this.map.addSource("metrotaipei_village_label", {
					type: "geojson",
					data: "/mapData/metrotaipei_village.geojson",
				});
			}
			if (!this.map.getLayer("metrotaipei_village_label")) {
				this.map.addLayer(metroTaipeiVillage);
			}
			if (this.map.isMoving()) {
				this.hideLabelsDuringMapMotion();
			}
		},
		addBoundaryLayers() {
			const hadDistrictLayer = this.map?.getLayer("metrotaipei_town");
			const hadVillageLayer = this.map?.getLayer("metrotaipei_village");
			this.ensureBoundaryLayer("district");
			this.ensureBoundaryLayer("village");
			if (!hadDistrictLayer) {
				this.setBoundaryLayerVisibility("metrotaipei_town", false);
			}
			if (!hadVillageLayer) {
				this.setBoundaryLayerVisibility("metrotaipei_village", false);
			}
		},
		// 3. Adds symbols that will be used by some map layers
		addSymbolSources() {
			if (!this.map) return;
			mapImageNames.forEach((imageName) => {
				this.loadMapImage(imageName);
			});
		},
		loadMapImage(imageName) {
			if (!this.map || !mapImageNames.includes(imageName)) return;
			if (this.map.hasImage(imageName)) return;
			this.map.loadImage(
				`/images/map/${imageName}.png`,
				(error, image) => {
					if (error || !this.map || this.map.hasImage(imageName)) {
						if (error) console.error(error);
						return;
					}
					this.map.addImage(imageName, image);
				},
			);
		},
		async preloadMrtModels() {
			const unloadedModels = mrtModelConfigs.filter(
				(model) => !this.preloadedModels[model.id],
			);
			if (unloadedModels.length === 0) return;
			this.isPreloading = true;
			const loader = new GLTFLoader();
			const loadModel = (model) =>
				new Promise((resolve) => {
					loader.load(
						model.url,
						(gltf) => {
							this.preloadedModels[model.id] = markRaw(
								gltf.scene,
							);
							resolve();
						},
						undefined,
						(error) => {
							console.error(
								`3D 模型 ${model.id} 載入失敗:`,
								error,
							);
							resolve();
						},
					);
				});

			await Promise.all(unloadedModels.map(loadModel));
			this.isPreloading = false;
		},
		ensureBoundaryLayer(layerType) {
			if (!this.map) return;
			const layerConfig =
				layerType === "district" ? metroTpDistrict : metroTpVillage;
			const layerId =
				layerType === "district"
					? "metrotaipei_town"
					: "metrotaipei_village";
			const hasServerVectorBoundaries = [
				"citydashboard.taipei",
				"test-citydashboard.taipei",
			].includes(window.location.hostname);

			if (this.map.getLayer(layerId)) return;
			if (!this.map.getSource(layerId)) {
				if (hasServerVectorBoundaries) {
					this.map.addSource(layerId, {
						type: "vector",
						scheme: "tms",
						tolerance: 0,
						tiles: [
							`${location.origin}/geo_server/gwc/service/tms/1.0.0/taipei_vioc:${layerId}@EPSG:900913@pbf/{z}/{x}/{y}.pbf`,
						],
					});
				} else {
					this.map.addSource(layerId, {
						type: "geojson",
						data: `/mapData/${layerId}.geojson`,
					});
				}
			}
			this.map.addLayer({
				...layerConfig,
				id: layerId,
				source: layerId,
			});
		},
		setBoundaryLayerVisibility(layerId, status) {
			if (!this.map?.getLayer(layerId)) return;
			this.map.setLayoutProperty(
				layerId,
				"visibility",
				status ? "visible" : "none",
			);
		},
		// 4. Toggle district boundaries
		toggleDistrictBoundaries(status) {
			this.ensureBoundaryLayer("district");
			this.setBoundaryLayerVisibility("metrotaipei_town", status);
			// if (status) {
			// 	this.map.setLayoutProperty(
			// 		"tp_district",
			// 		"visibility",
			// 		"visible"
			// 	);
			// } else {
			// 	this.map.setLayoutProperty("tp_district", "visibility", "none");
			// }
		},
		// 5. Toggle village boundaries
		toggleVillageBoundaries(status) {
			this.ensureBoundaryLayer("village");
			this.setBoundaryLayerVisibility("metrotaipei_village", status);
			// if (status) {
			// 	this.map.setLayoutProperty(
			// 		"tp_village",
			// 		"visibility",
			// 		"visible"
			// 	);
			// } else {
			// 	this.map.setLayoutProperty("tp_village", "visibility", "none");
			// }
		},
		// 6. Set User Location
		setCurrentLocation() {
			if (navigator.geolocation) {
				navigator.geolocation.getCurrentPosition(
					(position) => {
						this.userLocation = {
							latitude: position.coords.latitude,
							longitude: position.coords.longitude,
						};
					},
					(error) => {
						console.error(error.message);
					},
				);
			} else {
				console.error("Geolocation is not supported by this browser.");
			}
		},

		/* Adding Map Layers */
		// 1. Passes in the map_config (an Array of Objects) of a component and adds all layers to the map layer list
		addToMapLayerList(map_config) {
			map_config.forEach((element) => {
				let mapLayerId = `${element.index}-${element.type}-${element.city}`;
				// 1-1. If the layer exists, simply turn on the visibility and add it to the visible layers list
				if (
					this.currentLayers.find((element) => element === mapLayerId)
				) {
					this.loadingLayers.push("rendering");
					this.turnOnMapLayerVisibility(mapLayerId);
					if (
						!this.currentVisibleLayers.find(
							(element) => element === mapLayerId,
						)
					) {
						this.currentVisibleLayers.push(mapLayerId);
					}
					return;
				}
				let appendLayer = { ...element };
				appendLayer.layerId = mapLayerId;
				// 1-2. If the layer doesn't exist, call an API to get the layer data
				this.loadingLayers.push(appendLayer.layerId);
				if (element.source === "geojson") {
					this.fetchLocalGeoJson(appendLayer);
				} else if (element.source === "raster") {
					this.addRasterSource(appendLayer);
				}
			});
		},
		// 2. Call an API to get the layer data
		fetchLocalGeoJson(map_config) {
			axios
				.get(`/mapData/${map_config.index}.geojson`)
				.then((rs) => {
					this.addGeojsonSource(map_config, rs.data);
				})
				.catch((e) => console.error(e));
		},
		// 3-1. Add a local geojson as a source in mapbox
		addGeojsonSource(map_config, data) {
			if (
				!["voronoi", "isoline"].includes(map_config.type) &&
				map_config.type !== "symbol-3d"
			) {
				this.map.addSource(`${map_config.layerId}-source`, {
					type: "geojson",
					data: { ...data },
				});
			}
			if (map_config.type === "arc") {
				this.AddArcMapLayer(map_config, data);
			} else if (map_config.type === "voronoi") {
				this.AddVoronoiMapLayer(map_config, data);
			} else if (map_config.type === "isoline") {
				this.AddIsolineMapLayer(map_config, data);
			} else {
				this.addMapLayer(map_config, data);
			}
		},
		addRainAnimationLayer(map_config, data) {
			if (
				!this.map ||
				map_config.index !== FUTURE_HOUR_RAIN_LAYER_INDEX
			) {
				return;
			}

			this.removeRainAnimationLayer(map_config.layerId);
			const layerId = getRainAnimationLayerId(map_config.layerId);
			const rainLayer = createRainAnimationLayer(layerId, data);
			if (!rainLayer) return;

			this.rainAnimationLayers[map_config.layerId] = markRaw(rainLayer);
			this.map.addLayer(rainLayer);
		},
		removeRainAnimationLayer(mapLayerId) {
			const layerId = getRainAnimationLayerId(mapLayerId);
			if (this.map?.getLayer(layerId)) {
				this.map.removeLayer(layerId);
			}
			if (this.rainAnimationLayers[mapLayerId]) {
				delete this.rainAnimationLayers[mapLayerId];
			}
		},
		removeAllRainAnimationLayers() {
			Object.keys(this.rainAnimationLayers).forEach((mapLayerId) => {
				this.removeRainAnimationLayer(mapLayerId);
			});
			this.rainAnimationLayers = {};
		},
		setRainAnimationLayerVisibility(mapLayerId, isVisible) {
			const rainLayer = this.rainAnimationLayers[mapLayerId];
			if (!rainLayer) return;
			rainLayer.visible = isVisible;
			this.map?.triggerRepaint?.();
		},
		// 3-2. Add a raster map as a source in mapbox
		async addRasterSource(map_config) {
			if (
				["arc", "voronoi", "isoline", "symbol-3d"].includes(
					map_config.type,
				)
			) {
				let res = {};
				let res2 = {};
				let res3 = {};
				if (map_config.type === "symbol-3d") {
					await this.preloadMrtModels();
					res = await axios.get(
						`${location.origin}/geo_server/taipei_vioc/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=taipei_vioc%3A${map_config.index}&maxFeatures=1000000&outputFormat=application%2Fjson`,
					);
					res2 = await axios.get(
						`/mapData/${map_config.index}_route.geojson`,
					);
					if (
						map_config.index === "metro_o_line_car" ||
						map_config.index === "metro_g_line_car" ||
						map_config.index === "metro_r_line_car"
					) {
						res3 = await axios.get(
							`/mapData/${map_config.index}_route_2.geojson`,
						);
					}
				} else {
					res = await axios.get(
						`${location.origin}/geo_server/taipei_vioc/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=taipei_vioc%3A${map_config.index}&maxFeatures=1000000&outputFormat=application%2Fjson`,
					);
				}

				if (map_config.type === "arc") {
					this.map.addSource(`${map_config.layerId}-source`, {
						type: "geojson",
						data: { ...res.data },
					});
					this.AddArcMapLayer(map_config, res.data);
				} else if (map_config.type === "voronoi") {
					this.AddVoronoiMapLayer(map_config, res.data);
				} else if (map_config.type === "isoline") {
					this.AddIsolineMapLayer(map_config, res.data);
				} else if (map_config.type === "symbol-3d") {
					this.Add3dMapLayer(
						map_config,
						res.data,
						res2.data,
						res3?.data,
					);
				}
			} else {
				try {
					// 添加源
					this.map.addSource(`${map_config.layerId}-source`, {
						type: "vector",
						scheme: "tms",
						tolerance: 0,
						tiles: [
							`${location.origin}/geo_server/gwc/service/tms/1.0.0/taipei_vioc:${map_config.index}@EPSG:900913@pbf/{z}/{x}/{y}.pbf`,
						],
					});

					// 監聽錯誤
					this.map.on("error", (e) => {
						if (e.sourceId === `${map_config.layerId}-source`) {
							console.error("Source error:", e);

							// 清理已添加的源（如果存在）
							if (
								this.map.getSource(
									`${map_config.layerId}-source`,
								)
							) {
								this.map.removeSource(
									`${map_config.layerId}-source`,
								);
							}
							// 從 loadingLayers 中移除
							this.loadingLayers = this.loadingLayers.filter(
								(el) => el !== map_config.layerId,
							);
						}
					});

					// 監聽源加載完成
					const sourceLoaded = new Promise((resolve, reject) => {
						const checkSource = (e) => {
							if (e.sourceId === `${map_config.layerId}-source`) {
								if (e.isSourceLoaded) {
									this.map.off("sourcedata", checkSource);
									resolve();
								}
								// 如果有錯誤也需要處理
								if (e.error) {
									this.map.off("sourcedata", checkSource);
									reject(e.error);
								}
							}
						};

						this.map.on("sourcedata", checkSource);

						// 設置超時
						setTimeout(() => {
							this.map.off("sourcedata", checkSource);
							reject(new Error("Source load timeout"));
						}, 10000);
					});

					// 等待源加載完成後添加圖層
					await sourceLoaded;
					this.addMapLayer(map_config);
				} catch (error) {
					console.error("Failed to add source:", error);
					// 清理已添加的源（如果存在）
					if (this.map.getSource(`${map_config.layerId}-source`)) {
						this.map.removeSource(`${map_config.layerId}-source`);
					}
					// 從 loadingLayers 中移除
					this.loadingLayers = this.loadingLayers.filter(
						(el) => el !== map_config.layerId,
					);
				}
			}
		},
		// 4-1. Using the mapbox source and map config, create a new layer
		// The styles and configs can be edited in /assets/configs/mapbox/mapConfig.js
		addMapLayer(map_config, sourceData = null) {
			let extra_paint_configs = {};
			let extra_layout_configs = {};
			if (map_config.icon) {
				extra_paint_configs = {
					...maplayerCommonPaint[
						`${map_config.type}-${map_config.icon}`
					],
				};
				extra_layout_configs = {
					...maplayerCommonLayout[
						`${map_config.type}-${map_config.icon}`
					],
				};
			}
			if (map_config.size) {
				extra_paint_configs = {
					...extra_paint_configs,
					...maplayerCommonPaint[
						`${map_config.type}-${map_config.size}`
					],
				};
				extra_layout_configs = {
					...extra_layout_configs,
					...maplayerCommonLayout[
						`${map_config.type}-${map_config.size}`
					],
				};
			}
			this.loadingLayers.push("rendering");
			const filterClass = [
				["6h150r", "6h250r", "6h350r"],
				["12h200r", "12h300r", "12h400r"],
				["24h200r", "24h350r", "24h500r", "24h650r"],
			];

			// 初始 filter 設定為第一組 (6 小時降雨)
			const initialFilter = ["in", "hazard_class", ...filterClass[0]];
			const config = {
				id: map_config.layerId,
				type: map_config.type,
				"source-layer":
					map_config.source === "raster" ? map_config.index : "",
				paint: {
					...maplayerCommonPaint[`${map_config.type}`],
					...extra_paint_configs,
					...map_config.paint,
				},
				layout: {
					...maplayerCommonLayout[`${map_config.type}`],
					...extra_layout_configs,
				},
				source: `${map_config.layerId}-source`,
			};
			if (
				map_config.layerId ===
					"wee_hazard_water-fill-extrusion-metrotaipei" ||
				map_config.layerId ===
					"wee_hazard_water_tp-fill-extrusion-taipei"
			) {
				config.filter = initialFilter;
			}
			this.map.addLayer(config);
			this.addRainAnimationLayer(map_config, sourceData);
			if (
				map_config.layerId ===
					"wee_hazard_water-fill-extrusion-metrotaipei" ||
				map_config.layerId ===
					"wee_hazard_water_tp-fill-extrusion-taipei"
			)
				this.animateFilter(map_config.layerId);
			this.currentLayers.push(map_config.layerId);
			this.mapConfigs[map_config.layerId] = map_config;
			if (!this.currentVisibleLayers.includes(map_config.layerId)) {
				this.currentVisibleLayers.push(map_config.layerId);
			}
			this.loadingLayers = this.loadingLayers.filter(
				(el) => el !== map_config.layerId,
			);
		},
		animateFilter(mapLayerId) {
			this.stopAnimation();
			const filterClass = [
				["6h150r", "6h250r", "6h350r"],
				["12h200r", "12h300r", "12h400r"],
				["24h200r", "24h350r", "24h500r", "24h650r"],
			];

			let index = 1;

			this.waitUntilReady = setInterval(() => {
				if (this.loadingLayers.length !== 0) return;

				clearInterval(this.waitUntilReady); // 停止等待
				this.waitUntilReady = null;

				// 啟動動畫
				this.filterInterval = setInterval(() => {
					const currentFilter = [
						"in",
						"hazard_class",
						...filterClass[index],
					];

					this.map.setFilter(mapLayerId, currentFilter);
					index = (index + 1) % filterClass.length;
				}, 1000);
			}, 200);
		},
		stopAnimation() {
			if (this.arcAnimationFrame) {
				cancelAnimationFrame(this.arcAnimationFrame);
				this.arcAnimationFrame = null;
			}
			this.isArcAnimationRunning = false;
			if (this.filterInterval) {
				clearInterval(this.filterInterval);
				this.filterInterval = null;
			}
			if (this.waitUntilReady) {
				clearInterval(this.waitUntilReady);
				this.waitUntilReady = null;
			}
		},
		// 4-2-1. Add Map Layer for Arc Maps
		// Developed by Weeee Chill, Taipei Codefest 2024
		AddArcMapLayer(map_config, data) {
			// start loading
			this.loadingLayers.push("rendering");
			const mapLayerId = `${map_config.index}-${map_config.type}-${map_config.city}`;
			const paintSettings = map_config.paint
				? map_config.paint
				: { "arc-color": ["#ffffff"] };
			paintSettings["arc-color"] = paintSettings["arc-color"]
				? paintSettings["arc-color"]
				: ["#ffffff"];
			// formatted data
			const layerConfig = {
				id: map_config.index,
				data: data.features,
				getSourcePosition: (d) => d.geometry.coordinates[0],
				getTargetPosition: (d) => d.geometry.coordinates[1],
				// color format: [r, g, b, [a]]
				getSourceColor: () => {
					const color = hexToRGB(paintSettings["arc-color"][0]);
					return [
						parseInt(color.r, 16),
						parseInt(color.g, 16),
						parseInt(color.b, 16),
						255 * paintSettings["arc-opacity"] || 255 * 0.5,
					];
				},
				getTargetColor: () => {
					const color = hexToRGB(
						paintSettings["arc-color"][1] ||
							paintSettings["arc-color"][0],
					);
					return [
						parseInt(color.r, 16),
						parseInt(color.g, 16),
						parseInt(color.b, 16),
						255 * paintSettings["arc-opacity"] || 255 * 0.5,
					];
				},
				getWidth: paintSettings["arc-width"] || 2,
				pickable: true,
				...(paintSettings["arc-animate"] && {
					coef: this.step / 1000,
				}),
			};
			// add deckgl layer to overlay
			this.deckGlLayer[mapLayerId] = {
				type: paintSettings["arc-animate"]
					? "AnimatedArcLayer"
					: "ArcLayer",
				config: layerConfig,
				data: data.features,
			};
			// render deckgl layer
			this.currentVisibleLayers.push(map_config.layerId);
			this.renderDeckGLLayer();
			// end loading
			this.currentLayers.push(map_config.layerId);
			this.mapConfigs[map_config.layerId] = map_config;
			this.loadingLayers = this.loadingLayers.filter(
				(el) => el !== map_config.layerId,
			);
		},
		ensureDeckGlOverlay() {
			if (!this.map || this.overlay) return;
			this.overlay = new MapboxOverlay({
				interleaved: true,
				layers: [],
			});
			this.map.addControl(this.overlay);
		},
		updateDeckGlLayerProps() {
			if (!this.overlay) return;
			const layers = Object.keys(this.deckGlLayer)
				.map((index) => {
					const l = this.deckGlLayer[index];
					switch (l.type) {
					case "ArcLayer":
						return new ArcLayer(l.config);
					case "AnimatedArcLayer":
						return new AnimatedArcLayer({
							...l.config,
							coef: this.step / 1000,
						});
					default:
						return null;
					}
				})
				.filter(Boolean);
			this.overlay.setProps({ layers });
		},
		// 4-2-2. Render DeckGL Layer
		// Developed by Weeee Chill, Taipei Codefest 2024
		renderDeckGLLayer() {
			this.ensureDeckGlOverlay();
			this.updateDeckGlLayerProps();
			if (
				this.currentVisibleLayers.some(
					(l) =>
						l.indexOf("-arc") !== -1 &&
						typeof this.deckGlLayer[l].config.coef === "number",
				) &&
				this.step < 1000 &&
				!this.isArcAnimationRunning
			)
				this.animateArcLayer();
		},
		// 4-2-3. Animate Arc Layer
		// Developed by Weeee Chill, Taipei Codefest 2024
		animateArcLayer() {
			if (this.isArcAnimationRunning) return;
			this.isArcAnimationRunning = true;
			// 開始時間
			let startTime = performance.now();
			// 每個動畫步驟的持續時間（毫秒）
			const duration = 1000; // 1秒
			const _this = this;

			const step = (timestamp) => {
				// 計算已經過的時間
				const elapsedTime = timestamp - startTime;
				// 計算進度
				const progress = (elapsedTime / duration) * 100;

				// 如果時間已經超過一個步驟，則增加步驟數
				if (progress >= (_this.step / 1000) * 100) {
					_this.step = _this.step + 1;
					_this.updateDeckGlLayerProps();
				}

				// 如果動畫還未完成，繼續下一個動畫步驟
				if (_this.step <= 1000) {
					_this.arcAnimationFrame = requestAnimationFrame(step);
				} else {
					_this.isArcAnimationRunning = false;
					_this.arcAnimationFrame = null;
				}
			};
			// 啟動動畫
			this.arcAnimationFrame = requestAnimationFrame(step);
		},
		// 4-3. Add Map Layer for Voronoi Maps
		// Developed by 00:21, Taipei Codefest 2023
		AddVoronoiMapLayer(map_config, data) {
			this.loadingLayers.push("rendering");

			let voronoi_source = {
				type: data.type,
				crs: data.crs,
				features: [],
			};

			// Get features alone
			let { features } = data;

			// Get coordnates alone
			let coords = features.map(
				(location) => location.geometry.coordinates,
			);

			// Remove duplicate coordinates (so that they wont't cause problems in the Voronoi algorithm...)
			let shouldBeRemoved = coords.map((coord1, ind) => {
				return (
					coords.findIndex((coord2) => {
						return (
							coord2[0] === coord1[0] && coord2[1] === coord1[1]
						);
					}) !== ind
				);
			});

			features = features.filter((_, ind) => !shouldBeRemoved[ind]);
			coords = coords.filter((_, ind) => !shouldBeRemoved[ind]);

			// Calculate cell for each coordinate
			let cells = voronoi(coords);

			// Push cell outlines to source data
			for (let i = 0; i < cells.length; i++) {
				voronoi_source.features.push({
					...features[i],
					geometry: {
						type: "LineString",
						coordinates: cells[i],
					},
				});
			}

			// Add source and layer
			this.map.addSource(`${map_config.layerId}-source`, {
				type: "geojson",
				data: { ...voronoi_source },
			});

			let new_map_config = { ...map_config };
			new_map_config.type = "line";
			new_map_config.source = "geojson";
			this.addMapLayer(new_map_config);
		},
		// 4-4. Add Map Layer for Isoline Maps
		// Developed by 00:21, Taipei Codefest 2023
		AddIsolineMapLayer(map_config, data) {
			this.loadingLayers.push("rendering");
			// Step 1: Generate a 2D scalar field from known data points
			// - Turn the original data into the format that can be accepted by interpolation()
			let dataPoints = data.features
				.filter((item) => item.geometry)
				.map((item) => {
					return {
						x: item.geometry.coordinates[0],
						y: item.geometry.coordinates[1],
						value: item.properties[
							map_config.paint?.["isoline-key"] || "value"
						],
					};
				});

			let lngStart = 121.3;
			let lngEnd = 122;
			let latStart = 24.8;
			let latEnd = 25.3;

			let targetPoints = [];
			let gridSize = 0.001;
			let rowN = 0;
			let colN = 0;

			// - Generate target point coordinates
			for (let i = latStart; i <= latEnd; i += gridSize, rowN += 1) {
				colN = 0;
				for (let j = lngStart; j <= lngEnd; j += gridSize, colN += 1) {
					targetPoints.push({ x: j, y: i });
				}
			}

			// - Get target points interpolation result
			let interpolationResult = interpolation(dataPoints, targetPoints);

			// Step 2: Calculate isolines from the 2D scalar field
			// - Turn the interpolation result into the format that can be accepted by marchingSquare()
			let discreteData = [];
			for (let y = 0; y < rowN; y++) {
				discreteData.push([]);
				for (let x = 0; x < colN; x++) {
					discreteData[y].push(interpolationResult[y * colN + x]);
				}
			}

			// - Initialize geojson data
			let isoline_data = {
				type: "FeatureCollection",
				crs: {
					type: "name",
					properties: { name: "urn:ogc:def:crs:OGC:1.3:CRS84" },
				},
				features: [],
			};

			const min = map_config.paint?.["isoline-min"] || 0;
			const max = map_config.paint?.["isoline-max"] || 100;
			const step = map_config.paint?.["isoline-step"] || 2;

			// - Repeat the marching square algorithm for differnt iso-values (40, 42, 44 ... 74 in this case)
			for (let isoValue = min; isoValue <= max; isoValue += step) {
				let result = marchingSquare(discreteData, isoValue);

				let transformedResult = result.map((line) => {
					return line.map((point) => {
						return [
							point[0] * gridSize + lngStart,
							point[1] * gridSize + latStart,
						];
					});
				});

				isoline_data.features = isoline_data.features.concat(
					// Turn result into geojson format
					transformedResult.map((line) => {
						return {
							type: "Feature",
							properties: { value: isoValue },
							geometry: { type: "LineString", coordinates: line },
						};
					}),
				);
			}

			// Step 3: Add source and layer
			this.map.addSource(`${map_config.layerId}-source`, {
				type: "geojson",
				data: { ...isoline_data },
			});

			delete map_config.paint?.["isoline-key"];
			delete map_config.paint?.["isoline-min"];
			delete map_config.paint?.["isoline-max"];
			delete map_config.paint?.["isoline-step"];

			let new_map_config = {
				...map_config,
				type: "line",
				source: "geojson",
			};
			this.addMapLayer(new_map_config);
		},
		// 4-5. Create 3DMap for mrtp 202511月新開發
		Add3dMapLayer(map_config, data, data2, data3) {
			// 3D 動態圖載入前設定
			this.loadingLayers.push("rendering");
			this.currentLayers.push(map_config.layerId);
			this.mapConfigs[map_config.layerId] = map_config;

			// 紀錄資料更新時間
			this.layerUpdateTime[map_config.layerId] = new Date();

			// 注意重複加入Id
			if (!this.currentVisibleLayers.includes(map_config.layerId)) {
				this.currentVisibleLayers.push(map_config.layerId);
			}

			// 組成渲染所須的列車資料

			// 須注意的支線特例
			const branchLineStations = [
				"蘆洲",
				"三民高中",
				"徐匯中學",
				"三和國中",
				"三重國小",
				"小碧潭",
				"新北投",
			];

			// 建立 mrtCarsInit
			const mrtCarsInit = data.features.map((item, i) => {
				let routeCoordinates = null;

				if (
					branchLineStations.includes(
						item.properties.curr_stationname,
					) ||
					branchLineStations.includes(
						item.properties.next_stationname,
					)
				) {
					routeCoordinates = cutRouteSegment(
						data3,
						[item.properties.curr_lon, item.properties.curr_lat],
						[item.properties.next_lon, item.properties.next_lat],
					);
				} else {
					routeCoordinates = cutRouteSegment(
						data2,
						[item.properties.curr_lon, item.properties.curr_lat],
						[item.properties.next_lon, item.properties.next_lat],
					);
				}

				const coords = routeCoordinates.geometry.coordinates.map(
					(c) => [c[0], c[1], 0],
				);

				return {
					id: i,
					route_id: map_config.layerId,
					...item.properties,
					coords,
					car_icon: map_config.icon,
					final_coord: interpolateAlongSegment(coords, 1),
					progress: 0,
					speed: 0.00222,
				};
			});

			// 整併 prevMrtCars
			let mrtCars = [];
			// 把不同路線的舊資料保存起來
			let updatePrevCar = [];

			if (this.prevMrtCars.length > 0) {
				// 建立 Map 加速查找
				const initTrainMap = new Map(
					mrtCarsInit.map((car) => [car.trainnumber, car]),
				);
				// 先確認上一輪有的車
				this.prevMrtCars.forEach((prevCar) => {
					// 先確認新來的資料是不是同一路線
					if (prevCar.route_id !== mrtCarsInit[0].route_id) {
						updatePrevCar.push(prevCar);
						return;
					}

					const newCar = initTrainMap.get(prevCar.trainnumber);

					// 同路線新資料沒有該車 → 跳過
					if (!newCar) return;

					// 判斷車子是否進站（curr_stationname 有無變）
					const stationChanged =
						prevCar.curr_stationid !== newCar.curr_stationid;

					if (stationChanged) {
						// 用舊 final_coord 當作起點，切新路線到新 curr_station
						const start = prevCar.final_coord;
						const end = [newCar.curr_lon, newCar.curr_lat];

						let routeCoordinates = null;

						if (
							branchLineStations.includes(
								newCar.curr_stationname,
							) ||
							branchLineStations.includes(newCar.next_stationname)
						) {
							routeCoordinates = cutRouteSegment(
								data3,
								start,
								end,
							);
						} else {
							routeCoordinates = cutRouteSegment(
								data2,
								start,
								end,
							);
						}

						const coords =
							routeCoordinates.geometry.coordinates.map((c) => [
								c[0],
								c[1],
								0,
							]);

						// 更新新車物件
						newCar.coords = coords;
						newCar.final_coord = interpolateAlongSegment(coords, 1);

						// progress 重置
						newCar.progress = 0;
						newCar.dataChanged = true;
					} else {
						// curr_station 沒變 → 保留舊狀態
						newCar.coords = prevCar.coords;
						newCar.final_coord = prevCar.final_coord;
						newCar.progress = 0.99;
						newCar.dataChanged = false;
					}
					// 把新資料有找到的車推去待跑動畫列車陣列
					mrtCars.push(newCar);
				});

				// 新資料出現的車
				for (const [trainNumber, car] of initTrainMap) {
					const existed = this.prevMrtCars.some(
						(prev) => prev.trainnumber === trainNumber,
					);
					if (existed) continue; // 已存在 → 不處理
					const { coords } = car;

					if (!coords || coords.length === 0) {
						car.coords = [];
						car.final_coord = null;
						car.progress = 0;
						continue;
					}

					if (coords.length === 1) {
						const c = coords[0];
						car.coords = [c];
						car.final_coord = [c[0], c[1], c[2] ?? 0];
						car.progress = 0;
						continue;
					}

					const ratio = 90 / 100;
					const finalCoord = interpolateAlongSegment(coords, ratio); // 插值後 2/3 的點

					// 切出 2/3 的前段 coords
					const trimmed = [];
					trimmed.push(coords[0]);

					let total = 0;
					const segLens = [];
					for (let i = 0; i < coords.length - 1; i++) {
						const dx = coords[i + 1][0] - coords[i][0];
						const dy = coords[i + 1][1] - coords[i][1];
						const dz =
							(coords[i + 1][2] || 0) - (coords[i][2] || 0);
						const len = Math.sqrt(dx * dx + dy * dy + dz * dz);
						total += len;
						segLens.push(len);
					}

					const targetDist = total * ratio;
					let accum = 0;

					for (let i = 0; i < segLens.length; i++) {
						if (accum + segLens[i] < targetDist) {
							trimmed.push(coords[i + 1]);
							accum += segLens[i];
						} else {
							trimmed.push(finalCoord);
							break;
						}
					}

					car.coords = trimmed;
					car.final_coord = finalCoord;
					car.progress = 0;

					// 把新資料出現的車推去待跑動畫列車陣列
					mrtCars.push(car);
				}
			} else {
				// 如果是第一次開組件則執行初始化
				mrtCars = mrtCarsInit.map((item) => {
					const { coords } = item || {};

					// 無座標 -> 返回空 coords 且 final_coord 為 null
					if (!coords || coords.length === 0) {
						return {
							...item,
							coords: [],
							final_coord: null,
							progress: 0,
						};
					}

					// 只有一個點 -> 2/3 仍然是該點本身
					if (coords.length === 1) {
						const only = coords[0];
						return {
							...item,
							coords: [only],
							final_coord: [only[0], only[1], only[2] ?? 0],
							progress: 0,
						};
					}

					// 兩點或以上 -> 正常按距離計算 2/3 並切出前段 coords（含插值點）
					const ratio = 90 / 100;
					const finalCoord = interpolateAlongSegment(coords, ratio); // [lng, lat, z]

					// 計算每段長度以取得 trimmedCoords
					const segLens = [];
					let totalLength = 0;
					for (let i = 0; i < coords.length - 1; i++) {
						const dx = coords[i + 1][0] - coords[i][0];
						const dy = coords[i + 1][1] - coords[i][1];
						const dz =
							(coords[i + 1][2] || 0) - (coords[i][2] || 0);
						const len = Math.sqrt(dx * dx + dy * dy + dz * dz);
						segLens.push(len);
						totalLength += len;
					}

					const targetDist = totalLength * ratio;
					const trimmedCoords = [];
					trimmedCoords.push(coords[0]);

					let accum = 0;
					for (let i = 0; i < segLens.length; i++) {
						if (accum + segLens[i] < targetDist) {
							trimmedCoords.push(coords[i + 1]);
							accum += segLens[i];
						} else {
							// 2/3 落在這段 -> 補上精準的插值點（finalCoord）然後中斷
							trimmedCoords.push(finalCoord);
							break;
						}
					}

					return {
						...item,
						coords: trimmedCoords,
						final_coord: finalCoord,
						progress: 0,
					};
				});
			}

			if (mrtCars.length === 0) {
				console.error("待跑動畫列車資料為空，請確認!");
				return;
			}

			this.prevMrtCars = [...updatePrevCar, ...mrtCars];

			// === 自訂 3D 圖層 ===

			const customLayer = {
				id: map_config.layerId,
				type: "custom",
				renderingMode: "3d",
				onAdd: (map, gl) => {
					customLayer.map = markRaw(map);
					customLayer.camera = markRaw(new THREE.Camera());
					customLayer.scene = markRaw(new THREE.Scene());
					customLayer.lastUpdateTime = 0; // 節流用

					// 環境光
					const hemiLight = new THREE.HemisphereLight(
						0xffffff,
						0x444444,
						3.2,
					);
					hemiLight.position.set(0, 20, 0);
					customLayer.scene.add(hemiLight);

					// 預載列車模型
					for (const car of mrtCars) {
						if (!car.model) {
							const carIcon = car.car_icon;
							const preModel = this.preloadedModels[carIcon];

							if (preModel) {
								const modelClone = preModel.clone(true);
								modelClone.traverse((child) => {
									if (child.isMesh) {
										child.material = child.material.clone();
									}
								});
								const horizontalOffset = -30;
								modelClone.position.x += horizontalOffset;
								car.model = modelClone;
								customLayer.scene.add(modelClone);
							} else {
								console.warn(
									`⚠️ 3D 模型尚未預載完成: ${carIcon}`,
								);
							}
						}
					}

					customLayer.renderer = markRaw(
						new THREE.WebGLRenderer({
							canvas: map.getCanvas(),
							context: gl,
							antialias: true,
						}),
					);
					customLayer.renderer.autoClear = false;

					// 加入 2D 圓圈資料
					const sourceId = `mrt-2d-source-${map_config.layerId}`;
					const layerId = `mrt-2d-circles-${map_config.layerId}`;

					if (!map.getSource(sourceId)) {
						map.addSource(sourceId, {
							type: "geojson",
							data: {
								type: "FeatureCollection",
								features: [],
							},
						});

						map.addLayer({
							id: layerId,
							type: "circle",
							source: sourceId,
							paint: {
								"circle-radius": 10,
								"circle-color": mrtLineColor[map_config.index],
								"circle-stroke-width": 2,
								"circle-stroke-color": "#FFFFFF",
								"circle-opacity": 0.8,
							},
						});
					}

					// 儲存 sourceId 和 layerId 供 render 和 onRemove 使用
					customLayer.sourceId = sourceId;
					customLayer.layerId2D = layerId;

					// === Tooltip 只建一次 ===
					if (!customLayer.carTooltip) {
						// popup 最外層
						customLayer.carTooltip = document.createElement("div");
						customLayer.carTooltip.style.position = "absolute";
						customLayer.carTooltip.style.left = 0;
						customLayer.carTooltip.style.top = 0;
						customLayer.carTooltip.style.minWidth = "120px";
						customLayer.carTooltip.style.maxHeight = "220px";
						customLayer.carTooltip.style.height = "100%";
						customLayer.carTooltip.style.willChange = "transform";
						customLayer.carTooltip.style.background = "#282A2C";
						customLayer.carTooltip.style.border =
							"2px solid #817E79";
						customLayer.carTooltip.style.color = "#fff";
						customLayer.carTooltip.style.padding = "6px 10px";
						customLayer.carTooltip.style.borderRadius = "6px";
						customLayer.carTooltip.style.pointerEvents = "auto";
						customLayer.carTooltip.style.display = "none";
						customLayer.carTooltip.style.zIndex = "1";
						customLayer.carTooltip.style.overflow = "hidden";
						customLayer.tooltipOffsetX = 5;
						customLayer.tooltipOffsetY = 5;

						// popup 關閉按鈕
						const closeBtn = document.createElement("button");
						closeBtn.innerText = "×";
						closeBtn.style.position = "absolute";
						closeBtn.style.top = "1px";
						closeBtn.style.right = "8px";
						closeBtn.style.background = "transparent";
						closeBtn.style.border = "none";
						closeBtn.style.color = "#888787";
						closeBtn.style.cursor = "pointer";
						closeBtn.style.fontWeight = "bold";
						closeBtn.style.fontSize = "20px";
						closeBtn.onclick = () => {
							customLayer.carTooltip.style.display = "none";
							customLayer.selectedCar = null;
						};
						customLayer.carTooltip.appendChild(closeBtn);

						// popup 顯示屬性區塊
						const contentWrapper = document.createElement("div");
						contentWrapper.style.paddingRight = "12px";
						contentWrapper.style.height = "100%";
						contentWrapper.style.overflowY = "auto";

						customLayer.carTooltip.appendChild(closeBtn);
						customLayer.carTooltip.appendChild(contentWrapper);
						customLayer.tooltipContent = contentWrapper;
						map.getContainer().appendChild(customLayer.carTooltip);
					}

					// === Click 事件只綁一次 ===
					if (customLayer._carClickHandler) {
						map.off("click", customLayer._carClickHandler);
					}
					customLayer._carClickHandler = (e) => {
						const clickLngLat = [e.lngLat.lng, e.lngLat.lat];
						let closestCar = null;
						let minDist = Infinity;

						// 根據 zoom 等級調整點擊範圍
						const zoom = customLayer.map.getZoom();
						let clickRadius = 45; // 預設值

						if (zoom < 11) {
							clickRadius = 120; // zoom < 11 時範圍較大
						} else if (zoom < 13) {
							clickRadius = 90;
						} else {
							clickRadius = 45;
						}

						for (const car of mrtCars) {
							if (!car.currentLngLat || !car.lastDir) continue;

							const offsetMeters = 30;
							const norm = Math.sqrt(
								car.lastDir.x ** 2 + car.lastDir.y ** 2,
							);
							const dx = (car.lastDir.y / norm) * offsetMeters;
							const dy = (-car.lastDir.x / norm) * offsetMeters;
							const offsetCarPos = [
								car.currentLngLat[0] + dx * 0.00001,
								car.currentLngLat[1] + dy * 0.00001,
							];

							const dist = distance(
								point(clickLngLat),
								point(offsetCarPos),
								{
									units: "meters",
								},
							);

							if (dist < clickRadius && dist < minDist) {
								minDist = dist;
								closestCar = car;
							}
						}

						if (!closestCar) return;

						customLayer.selectedCar = closestCar;

						// 清空 tooltip 內容
						customLayer.tooltipContent.innerHTML = "";
						const infoContainer = document.createElement("div");
						const fields = map_config.property.map((prop) => ({
							label: prop.name,
							value: prop.name.includes("擁擠度")
								? getCrowdColor(closestCar[prop.key])
								: closestCar[prop.key] || "",
						}));

						fields.forEach((f) => {
							const row = document.createElement("div");
							row.style.marginBottom = "2px";
							row.textContent = `${f.label}: ${f.value ?? "-"}`;
							infoContainer.appendChild(row);
						});

						customLayer.tooltipContent.appendChild(infoContainer);
						customLayer.carTooltip.style.display = "block";
					};
					map.on("click", customLayer._carClickHandler);
				},

				onRemove(map) {
					// 清理 tooltip
					if (customLayer.carTooltip) {
						customLayer.carTooltip.remove();
						customLayer.carTooltip = null;
					}

					// 清理 click 事件
					if (customLayer._carClickHandler) {
						map.off("click", customLayer._carClickHandler);
						customLayer._carClickHandler = null;
					}

					// 用 sourceId 和 layerId 清理該路線的 2D 圖層
					if (
						customLayer.layerId2D &&
						map.getLayer(customLayer.layerId2D)
					) {
						map.removeLayer(customLayer.layerId2D);
					}

					if (
						customLayer.sourceId &&
						map.getSource(customLayer.sourceId)
					) {
						map.removeSource(customLayer.sourceId);
					}

					// 清理 3D 模型
					if (customLayer.scene && mrtCars?.length) {
						for (const car of mrtCars) {
							if (car.model) {
								car.model.traverse((child) => {
									if (child.isMesh) {
										// 釋放 geometry
										if (child.geometry)
											child.geometry.dispose();

										// 釋放材質和貼圖
										if (child.material) {
											const disposeMaterial = (mat) => {
												if (mat.map) mat.map.dispose();
												if (mat.normalMap)
													mat.normalMap.dispose();
												if (mat.roughnessMap)
													mat.roughnessMap.dispose();
												if (mat.metalnessMap)
													mat.metalnessMap.dispose();
												mat.dispose();
											};

											if (Array.isArray(child.material)) {
												child.material.forEach(
													disposeMaterial,
												);
											} else {
												disposeMaterial(child.material);
											}
										}
									}
								});

								// 從 scene 移除
								customLayer.scene.remove(car.model);
								car.model = null;
							}
						}

						// 清空 mrtCars 陣列，避免舊引用被再次使用
						mrtCars.length = 0;
					}

					// 清理 scene / camera
					if (customLayer.scene) {
						// 移除剩餘 children
						while (customLayer.scene.children.length) {
							customLayer.scene.remove(
								customLayer.scene.children[0],
							);
						}
					}
					customLayer.scene = null;
					customLayer.camera = null;

					// 清理 selectedCar
					customLayer.selectedCar = null;
				},

				render: (gl, matrix) => {
					// 取得當下的 zoom
					const zoom = customLayer.map.getZoom();
					const now = performance.now();

					let allFinished = true;
					// 確認當下各列車是否都跑完動畫
					for (const car of mrtCars) {
						if (car.progress < 1) allFinished = false;
					}

					if (zoom < 13) {
						// 2D 模式
						for (const car of mrtCars)
							if (car.model) car.model.visible = false;
						if (!allFinished) {
							if (now - customLayer.lastUpdateTime >= 200) {
								const features = updateCarsPosition(mrtCars);
								customLayer.map
									.getSource(customLayer.sourceId)
									.setData({
										type: "FeatureCollection",
										features,
									});
								customLayer.lastUpdateTime = now;
							}
						} else if (allFinished && !customLayer.updated2D) {
							const features = updateCarsPosition(mrtCars);
							customLayer.map
								.getSource(customLayer.sourceId)
								.setData({
									type: "FeatureCollection",
									features,
								});
							customLayer.updated2D = true; // 標記已經更新過一次
						}

						// 更新 2D tooltip
						if (
							customLayer.selectedCar?.currentLngLat &&
							customLayer.selectedCar?.lastDir
						) {
							const dir = customLayer.selectedCar.lastDir;
							const pos = customLayer.selectedCar.currentLngLat;
							const side = new THREE.Vector3(
								-dir.y,
								dir.x,
								0,
							).normalize();
							const offsetMeters = -30;
							const lngOffset = side.x * offsetMeters * 0.00001;
							const latOffset = side.y * offsetMeters * 0.00001;
							const offsetLngLat = [
								pos[0] + lngOffset,
								pos[1] + latOffset,
							];
							const screenPos =
								customLayer.map.project(offsetLngLat);
							customLayer.carTooltip.style.transform = `translate(${screenPos.x + customLayer.tooltipOffsetX}px, ${screenPos.y + customLayer.tooltipOffsetY}px)`;
						}

						// 顯示 2D layer
						if (
							customLayer.map.getLayoutProperty(
								customLayer.layerId2D,
								"visibility",
							) !== "visible"
						) {
							customLayer.map.setLayoutProperty(
								customLayer.layerId2D,
								"visibility",
								"visible",
							);
						}
					} else {
						// 3D 模式
						for (const car of mrtCars)
							if (car.model) car.model.visible = true;

						// 隱藏 2D layer
						if (
							customLayer.map.getLayoutProperty(
								customLayer.layerId2D,
								"visibility",
							) === "visible"
						) {
							customLayer.map.setLayoutProperty(
								customLayer.layerId2D,
								"visibility",
								"none",
							);
						}

						const { scene } = customLayer;
						const { camera } = customLayer;
						const { renderer } = customLayer;
						const rotationX = new THREE.Matrix4().makeRotationAxis(
							new THREE.Vector3(1, 0, 0),
							Math.PI / 2,
						);

						if (now - customLayer.lastUpdateTime >= 200) {
							updateCarsPosition(mrtCars);
							customLayer.lastUpdateTime = now;
						}

						for (const car of mrtCars) {
							// updateCarsPosition([car]); // 單台車也用同一個計算

							const pos = car.currentLngLat;
							const dir = car.lastDir;

							const merc = mapboxGl.MercatorCoordinate.fromLngLat(
								pos,
								pos[2],
							);
							const scale =
								merc.meterInMercatorCoordinateUnits() * 1.25;
							const fromDir = new THREE.Vector3(1, 0, 0);

							const quaternion =
								new THREE.Quaternion().setFromUnitVectors(
									fromDir,
									dir,
								);
							const extraRot = new THREE.Matrix4().makeRotationZ(
								Math.PI / 2,
							);
							const rotationMatrix = new THREE.Matrix4()
								.makeRotationFromQuaternion(quaternion)
								.multiply(extraRot);

							const translation =
								new THREE.Matrix4().makeTranslation(
									merc.x,
									merc.y,
									merc.z,
								);
							const scaleMatrix = new THREE.Matrix4().makeScale(
								scale,
								-scale,
								scale,
							);

							const modelMatrix = new THREE.Matrix4()
								.multiply(translation)
								.multiply(scaleMatrix)
								.multiply(rotationMatrix)
								.multiply(rotationX);

							camera.projectionMatrix = new THREE.Matrix4()
								.fromArray(matrix)
								.multiply(modelMatrix);

							renderer.resetState();
							renderer.render(scene, camera);

							// 更新 tooltip
							if (
								customLayer.selectedCar?.currentLngLat &&
								customLayer.selectedCar?.lastDir
							) {
								const dir = customLayer.selectedCar.lastDir;
								const pos =
									customLayer.selectedCar.currentLngLat;
								const side = new THREE.Vector3(
									-dir.y,
									dir.x,
									0,
								).normalize();
								const offsetMeters = -30;
								const lngOffset =
									side.x * offsetMeters * 0.00001;
								const latOffset =
									side.y * offsetMeters * 0.00001;
								const offsetLngLat = [
									pos[0] + lngOffset,
									pos[1] + latOffset,
								];
								const screenPos =
									customLayer.map.project(offsetLngLat);
								customLayer.carTooltip.style.transform = `translate(${screenPos.x + customLayer.tooltipOffsetX}px, ${screenPos.y + customLayer.tooltipOffsetY}px)`;
							}
						}
					}
					// 下一幀
					customLayer.map.triggerRepaint();
				},
			};

			if (!this.customLayers) this.customLayers = {};
			this.customLayers[map_config.layerId] = customLayer;

			// === 加入圖層 ===
			this.map.addLayer(customLayer);

			// loading 結束
			this.loadingLayers = this.loadingLayers.filter(
				(el) => el !== map_config.layerId,
			);
			return;
		},
		//  5. Turn on the visibility for a exisiting map layer
		turnOnMapLayerVisibility(mapLayerId) {
			if (mapLayerId.indexOf("-arc") !== -1) {
				this.deckGlLayer[mapLayerId].config.visible = true;
				this.step = 1;
				this.currentVisibleLayers.push(mapLayerId);
				this.renderDeckGLLayer();
			} else {
				this.setRainAnimationLayerVisibility(mapLayerId, true);
				if (
					mapLayerId ===
						"wee_hazard_water-fill-extrusion-metrotaipei" ||
					mapLayerId === "wee_hazard_water_tp-fill-extrusion-taipei"
				) {
					const filterClass = [
						["6h150r", "6h250r", "6h350r"],
						["12h200r", "12h300r", "12h400r"],
						["24h200r", "24h350r", "24h500r", "24h650r"],
					];

					// 初始 filter 設定為第一組 (6 小時降雨)
					const initialFilter = [
						"in",
						"hazard_class",
						...filterClass[0],
					];
					this.map.setFilter(mapLayerId, initialFilter);
					this.map.setLayoutProperty(
						mapLayerId,
						"visibility",
						"visible",
					);
					this.animateFilter(mapLayerId);
				} else {
					this.map.setLayoutProperty(
						mapLayerId,
						"visibility",
						"visible",
					);
				}
			}
		},
		// 6. Turn off the visibility of an exisiting map layer but don't remove it completely
		turnOffMapLayerVisibility(map_config) {
			this.stopAnimation();
			map_config.forEach((element) => {
				let mapLayerId = `${element.index}-${element.type}-${element.city}`;
				this.loadingLayers = this.loadingLayers.filter(
					(el) => el !== mapLayerId,
				);
				this.setRainAnimationLayerVisibility(mapLayerId, false);
				if (mapLayerId.indexOf("-arc") !== -1) {
					this.deckGlLayer[mapLayerId].config.visible = false;
					this.renderDeckGLLayer();
				} else if (this.map.getLayer(mapLayerId)) {
					this.map.setFilter(mapLayerId, null);
					this.map.setLayoutProperty(
						mapLayerId,
						"visibility",
						"none",
					);
				}
				this.currentVisibleLayers = this.currentVisibleLayers.filter(
					(element) => element !== mapLayerId,
				);
			});
			this.removePopup();

			// 如果3D捷運地圖 popup 存在把它清除
			// 關閉 popup + reset
			map_config.forEach((item) => {
				if (item.type === "symbol-3d") {
					const customLayer =
						this.customLayers[
							`${item.index}-${item.type}-${item.city}`
						];
					if (customLayer?.carTooltip) {
						customLayer.carTooltip.style.display = "none";
						customLayer.selectedCar = null;
					}
					if (
						customLayer?.layerId2D &&
						this.map.getLayer(customLayer.layerId2D)
					) {
						customLayer.map.setLayoutProperty(
							customLayer.layerId2D,
							"visibility",
							"none",
						);
					}
				}
			});
		},

		/* Popup Related Functions */
		// 1. Adds a popup when the user clicks on a item. The event will be passed in.
		addPopup(event) {
			const formatValue = (value, key) => {
				if (key === "occupied_rate") {
					return value === -99 ? "-" : value;
				}
				return value;
			};

			const hitSize = 6;

			const bbox = [
				[event.point.x - hitSize, event.point.y - hitSize],
				[event.point.x + hitSize, event.point.y + hitSize],
			];

			// Gets the info that is contained in the coordinates that the user clicked on (only visible layers)
			const clickFeatureDatas = this.map.queryRenderedFeatures(bbox, {
				layers: this.currentVisibleLayers.filter(
					(layer) => layer.indexOf("-arc") === -1,
				),
			});

			// Return if there is no info in the click
			if (!clickFeatureDatas || clickFeatureDatas.length === 0) {
				return;
			}
			// Parse clickFeatureDatas to get the first 3 unique layer datas, skip over already included layers
			const mapConfigs = [];
			const parsedPopupContent = [];
			const layerClosestFeature = {}; // key: layerId, value: { feature, distance }
			const clickPoint = [event.lngLat.lng, event.lngLat.lat];

			// 計算每個圖層最近的 feature
			for (const rawFeature of clickFeatureDatas) {
				const layerId = rawFeature.layer.id;

				// 計算距離最近的點
				const featureCenter =
					rawFeature.geometry?.type === "Point"
						? rawFeature.geometry.coordinates
						: getPopupCoordinates(rawFeature, event.lngLat);

				const dx = featureCenter[0] - clickPoint[0];
				const dy = featureCenter[1] - clickPoint[1];
				const dist2 = dx * dx + dy * dy;

				// 如果是該圖層第一次或更近，就存
				if (
					!layerClosestFeature[layerId] ||
					dist2 < layerClosestFeature[layerId].distance
				) {
					// 格式化 properties
					const feature = { ...rawFeature };
					feature.geometry =
						rawFeature.geometry || rawFeature._geometry;
					feature.properties = { ...rawFeature.properties };
					Object.keys(feature.properties).forEach((key) => {
						feature.properties[key] = formatValue(
							feature.properties[key],
							key,
						);
					});

					layerClosestFeature[layerId] = { feature, distance: dist2 };
				}
			}

			// 取前 3 個不同圖層最近的 feature
			const closestLayers = Object.keys(layerClosestFeature).slice(0, 3);
			for (const layerId of closestLayers) {
				const { feature } = layerClosestFeature[layerId];
				parsedPopupContent.push(feature);
				mapConfigs.push(this.mapConfigs[layerId]);
			}

			if (!parsedPopupContent.length) return;

			// Create a new mapbox popup
			const popupCoords = getPopupCoordinates(
				parsedPopupContent[0],
				event.lngLat,
			);

			this.popup = new mapboxGl.Popup()
				.setLngLat(popupCoords)
				.setHTML('<div id="vue-popup-content"></div>')
				.addTo(this.map);

			// 定義 popup 給 PopupComponent 內使用
			const { popup } = this;

			// Mount a vue component (MapPopup) to the id "vue-popup-content" and pass in data
			const PopupComponent = defineComponent({
				extends: MapPopup,
				setup() {
					const hls = ref(null);
					const activeTab = ref(0);
					const videoRef = ref(null);

					const isHlsUrl = (url) => {
						return (
							url &&
							(url.includes(".m3u8") || url.includes("hls"))
						);
					};

					const initHlsPlayer = (videoElement, src) => {
						if (Hls.isSupported()) {
							const hlsInstance = new Hls();

							// 添加錯誤監聽
							hlsInstance.on(Hls.Events.ERROR, (event, data) => {
								if (data.fatal) {
									hlsInstance.destroy();
								}
							});

							hlsInstance.loadSource(src);
							hlsInstance.attachMedia(videoElement);
							return hlsInstance;
						} else if (
							videoElement.canPlayType(
								"application/vnd.apple.mpegurl",
							)
						) {
							videoElement.src = src;
							return null;
						}

						return null;
					};

					const handleVideoLoad = () => {
						const activeTabValue = activeTab.value;
						let videoElement = videoRef.value;

						// 如果 videoRef 是數組，取第一個元素
						if (Array.isArray(videoElement)) {
							videoElement = videoElement[0];
						}

						if (
							!videoElement ||
							!parsedPopupContent[activeTabValue]
						) {
							return;
						}

						// 找到 video 模式的 property
						const videoProperty = mapConfigs[
							activeTabValue
						].property.find((item) => item.mode === "video");
						if (!videoProperty) {
							return;
						}

						const videoUrl =
							parsedPopupContent[activeTabValue].properties[
								videoProperty.key
							];
						if (!videoUrl) {
							return;
						}

						// 如果是 HLS URL，使用 HLS 播放器
						if (isHlsUrl(videoUrl)) {
							if (hls.value) {
								hls.value.destroy();
							}
							hls.value = initHlsPlayer(videoElement, videoUrl);
						} else {
							videoElement.src = videoUrl;
						}
					};

					// 初始化影像
					nextTick(() => {
						handleVideoLoad();
					});

					// 監聽 activeTab 變化，重新載入影片
					watch(activeTab, () => {
						nextTick(() => {
							handleVideoLoad();
							const feature = parsedPopupContent[activeTab.value];
							if (feature && popup) {
								const newCoords = getPopupCoordinates(
									feature,
									event.lngLat,
								);
								popup.setLngLat(newCoords);
							}
						});
					});

					// Only show the data of the topmost layer
					return {
						popupContent: parsedPopupContent,
						mapConfigs: mapConfigs,
						activeTab,
						videoRef,
					};
				},
			});
			// This helps vue determine the most optimal time to mount the component
			nextTick(() => {
				const app = createApp(PopupComponent);
				app.mount("#vue-popup-content");
			});

			// 使用者點擊圖徵時觸發GA自訂事件
			if (
				mapConfigs[0].city &&
				mapConfigs[0].title &&
				mapConfigs[0].source &&
				mapConfigs[0].type
			) {
				gtag("event", "popular_feature_click", {
					dashboard_city: mapConfigs[0].city,
					layer_name: mapConfigs[0].title,
					city_layer: `${mapConfigs[0].city}-${mapConfigs[0].title}`,
					data_type: mapConfigs[0].source,
					feature_type: mapConfigs[0].type,
					time: Date.now(),
				});
			}
		},
		// 2. Remove the current popup
		removePopup() {
			if (this.popup) {
				this.popup.remove();
			}
			this.popup = null;
		},
		// 3. programmatically trigger the popup, instead of user click
		manualTriggerPopup() {
			const center = this.map.getCenter();
			const point = this.map.project(center);

			this.addPopup({
				point: point,
				lngLat: center,
			});

			this.loadingLayers.pop();
		},

		/* Viewpoint / Marker Functions */
		// 1. Add a viewpoint
		async addViewPoint(name) {
			const { lng, lat } = this.map.getCenter();
			const zoom = this.map.getZoom();
			const pitch = this.map.getPitch();
			const bearing = this.map.getBearing();

			const authStore = useAuthStore();
			const res = await http.post(
				`user/${authStore.user.user_id}/viewpoint`,
				{
					center_x: lng,
					center_y: lat,
					zoom,
					pitch,
					bearing,
					name,
					point_type: "view",
				},
			);
			this.viewPoints.push(res.data.data);
		},
		// 2. Add a marker
		async addMarker(name) {
			const authStore = useAuthStore();
			const res = await http.post(
				`user/${authStore.user.user_id}/viewpoint`,
				{
					center_x: this.tempMarkerCoordinates.lng,
					center_y: this.tempMarkerCoordinates.lat,
					zoom: 0,
					pitch: 0,
					bearing: 0,
					name: name,
					point_type: "pin",
				},
			);

			this.viewPoints.push(res.data.data);

			const { lng, lat } = this.tempMarkerCoordinates;
			this.createMarkerAndPopupOnMap(
				{ color: "#5a9cf8" },
				name,
				res.data.data.id,
				{ lng, lat },
			);
			this.tempMarkerCoordinates = null;
		},
		// 3. Create a marker and popup on the map
		createMarkerAndPopupOnMap(
			colorSetting,
			markerName,
			markerId,
			{ lng, lat },
		) {
			const authStore = useAuthStore();
			const dialogStore = useDialogStore();
			const marker = new mapboxGl.Marker(colorSetting);
			const popup = new mapboxGl.Popup({ closeButton: false }).setHTML(
				`<div class="popup-for-pin"><div>${markerName}</div> <button id="delete-${markerId}" class="delete-pin"}">
						<span>delete</span>
					  </button></div>`,
			);

			popup.on("open", () => {
				const el = document.getElementById(`delete-${markerId}`);
				el.addEventListener("click", async () => {
					await http.delete(
						`user/${authStore.user.user_id}/viewpoint/${markerId}`,
					);
					dialogStore.showNotification("success", "地標刪除成功");
					this.viewPoints = this.viewPoints.filter(
						(viewPoint) => viewPoint.id !== markerId,
					);

					marker.remove();
					this.marker.remove();
				});
			});

			marker.setLngLat({ lng, lat }).setPopup(popup).addTo(this.map);
		},
		// 4. Remove a viewpoint
		async removeViewPoint(item) {
			const authStore = useAuthStore();
			await http.delete(
				`user/${authStore.user.user_id}/viewpoint/${item.id}`,
			);
			const dialogStore = useDialogStore();

			this.viewPoints = this.viewPoints.filter(
				(viewPoint) => viewPoint.id !== item.id,
			);
			dialogStore.showNotification("success", "視角刪除成功");
		},
		// 5. Fetch all view points
		async fetchViewPoints() {
			const authStore = useAuthStore();

			const res = await http.get(
				`user/${authStore.user.user_id}/viewpoint`,
			);
			this.viewPoints = res.data;
			if (this.map) this.renderMarkers();
		},
		// 6. Render all markers
		renderMarkers() {
			if (!this.viewPoints.length) return;

			this.viewPoints.forEach((item) => {
				if (item.point_type === "pin") {
					this.createMarkerAndPopupOnMap(
						{ color: "#5a9cf8" },
						item.name,
						item.id,
						{ lng: item.center_x, lat: item.center_y },
					);
				}
			});
		},

		/* Simple Navigation */
		getSimpleRouteProfile(profile) {
			return SIMPLE_ROUTE_PROFILES.includes(profile)
				? profile
				: "mapbox/driving";
		},
		estimateSimpleRouteDuration(distanceMeters, profile) {
			const speeds = {
				"mapbox/driving": 9.5,
				"mapbox/walking": 1.35,
				"mapbox/cycling": 4.2,
			};
			const safeProfile = this.getSimpleRouteProfile(profile);
			return (distanceMeters * 1.25) / speeds[safeProfile];
		},
		async geocodeSimpleRouteAddress(searchText) {
			const token = import.meta.env.VITE_MAPBOXTOKEN;
			const query = String(searchText || "").trim();
			if (!query) {
				throw new Error("請輸入完整的起點與終點");
			}
			if (!token) {
				throw new Error("缺少 Mapbox Token，無法查詢路線");
			}

			const res = await axios.get(
				"https://api.mapbox.com/search/searchbox/v1/forward",
				{
					params: {
						q: query,
						access_token: token,
						language: "zh-TW",
						country: "TW",
						bbox: SIMPLE_ROUTE_SEARCH_BBOX,
						limit: 1,
						proximity: SIMPLE_ROUTE_SEARCH_PROXIMITY,
						types: SIMPLE_ROUTE_SEARCH_TYPES,
					},
				},
			);
			const feature = res.data?.features?.[0];
			const coordinates = getSimpleRouteFeatureCoordinates(feature);

			if (!coordinates) {
				throw new Error(`找不到「${query}」的位置`);
			}

			return {
				name: getSimpleRouteFeatureName(feature, query),
				coordinates,
			};
		},
		async fetchSimpleRoute(startCoordinates, endCoordinates, profile) {
			const token = import.meta.env.VITE_MAPBOXTOKEN;
			const safeProfile = this.getSimpleRouteProfile(profile);
			const coordinateText = `${startCoordinates.join(
				",",
			)};${endCoordinates.join(",")}`;
			const res = await axios.get(
				`https://api.mapbox.com/directions/v5/${safeProfile}/${coordinateText}`,
				{
					params: {
						alternatives: false,
						geometries: "geojson",
						overview: "full",
						steps: false,
						access_token: token,
					},
				},
			);
			const route = res.data?.routes?.[0];

			if (!route?.geometry?.coordinates?.length) {
				throw new Error("找不到可用路線");
			}

			return route;
		},
		async findSimpleRoute({ startText, endText, profile }) {
			if (!this.map) {
				throw new Error("地圖尚未載入完成");
			}
			const safeProfile = this.getSimpleRouteProfile(profile);
			const [start, end] = await Promise.all([
				this.geocodeSimpleRouteAddress(startText),
				this.geocodeSimpleRouteAddress(endText),
			]);
			let route = null;
			let isApproximate = false;

			try {
				route = await this.fetchSimpleRoute(
					start.coordinates,
					end.coordinates,
					safeProfile,
				);
			} catch {
				const straightDistance =
					distance(point(start.coordinates), point(end.coordinates), {
						units: "kilometers",
					}) * 1000;
				route = {
					distance: straightDistance,
					duration: this.estimateSimpleRouteDuration(
						straightDistance,
						safeProfile,
					),
					geometry: {
						type: "LineString",
						coordinates: [start.coordinates, end.coordinates],
					},
				};
				isApproximate = true;
			}

			this.renderSimpleRoute({
				geometry: route.geometry,
				start,
				end,
				distance: route.distance,
				duration: route.duration,
				profile: safeProfile,
				isApproximate,
			});

			return this.navigationRouteSummary;
		},
		createSimpleRouteMarker(label, coordinates, variant) {
			if (!this.map) return null;
			const markerElement = document.createElement("div");
			markerElement.className = `simple-navigation-marker simple-navigation-marker--${variant}`;
			markerElement.textContent = label;

			return markRaw(
				new mapboxGl.Marker({
					element: markerElement,
					anchor: "center",
				})
					.setLngLat(coordinates)
					.addTo(this.map),
			);
		},
		resetCurrentRoadSpeedLimit() {
			if (this.roadSpeedLimitLookupTimer) {
				window.clearTimeout(this.roadSpeedLimitLookupTimer);
			}
			this.currentRoadSpeedLimit = createInitialRoadSpeedLimitState();
			this.lastRoadSpeedLimitLookupAt = 0;
			this.lastRoadSpeedLimitLookupKey = "";
			this.pendingRoadSpeedLimitCoordinate = null;
			this.roadSpeedLimitLookupTimer = null;
			this.roadSpeedLimitRequestId += 1;
		},
		scheduleCurrentRoadSpeedLimitLookup(coordinate, options = {}) {
			if (
				!options.force &&
				!this.isSimpleRouteFirstPersonCamera
			) {
				return;
			}
			if (!Array.isArray(coordinate)) return;

			const normalizedCoordinate = [
				Number(coordinate[0]),
				Number(coordinate[1]),
			];
			if (
				!Number.isFinite(normalizedCoordinate[0]) ||
				!Number.isFinite(normalizedCoordinate[1])
			) {
				return;
			}

			this.pendingRoadSpeedLimitCoordinate = normalizedCoordinate;
			const now = Date.now();
			const elapsed = now - this.lastRoadSpeedLimitLookupAt;

			if (
				options.force ||
				elapsed >= SIMPLE_ROUTE_SPEED_LIMIT_LOOKUP_THROTTLE_MS
			) {
				if (this.roadSpeedLimitLookupTimer) {
					window.clearTimeout(this.roadSpeedLimitLookupTimer);
					this.roadSpeedLimitLookupTimer = null;
				}
				this.fetchCurrentRoadSpeedLimit(normalizedCoordinate);
				return;
			}

			if (this.roadSpeedLimitLookupTimer) return;

			this.roadSpeedLimitLookupTimer = window.setTimeout(() => {
				const pendingCoordinate =
					this.pendingRoadSpeedLimitCoordinate;
				this.pendingRoadSpeedLimitCoordinate = null;
				this.roadSpeedLimitLookupTimer = null;
				this.fetchCurrentRoadSpeedLimit(pendingCoordinate);
			}, SIMPLE_ROUTE_SPEED_LIMIT_LOOKUP_THROTTLE_MS - elapsed);
		},
		async fetchCurrentRoadSpeedLimit(coordinate) {
			if (!Array.isArray(coordinate)) return;
			const coordinateKey = getCoordinateLookupKey(coordinate);
			if (
				coordinateKey === this.lastRoadSpeedLimitLookupKey &&
				["loading", "success"].includes(
					this.currentRoadSpeedLimit.status,
				)
			) {
				return;
			}

			const requestId = this.roadSpeedLimitRequestId + 1;
			this.roadSpeedLimitRequestId = requestId;
			this.lastRoadSpeedLimitLookupAt = Date.now();
			this.lastRoadSpeedLimitLookupKey = coordinateKey;
			this.currentRoadSpeedLimit = {
				...this.currentRoadSpeedLimit,
				status: "loading",
				error: "",
			};

			try {
				const res = await axios.get(ROAD_NAME_LOOKUP_API_URL, {
					params: {
						searchType: "latLng",
						x: Number(coordinate[0]).toFixed(6),
						y: Number(coordinate[1]).toFixed(6),
					},
					transformResponse: [(data) => data],
				});
				const address = getRoadNameLookupAddress(res.data);
				const roadName = extractRoadNameFromAddress(address);
				const speedLimit = findTaipeiRoadSpeedLimit({
					roadName,
					address,
				});

				if (requestId !== this.roadSpeedLimitRequestId) return;

				this.currentRoadSpeedLimit = {
					...speedLimit,
					status: "success",
					address,
					roadName: speedLimit.roadName || roadName,
					updatedAt: Date.now(),
					error: "",
				};
			} catch {
				if (requestId !== this.roadSpeedLimitRequestId) return;

				this.currentRoadSpeedLimit = {
					...this.currentRoadSpeedLimit,
					status: "error",
					error: "無法取得道路資訊",
					updatedAt: Date.now(),
				};
			}
		},
		setSimpleRouteFirstPersonCamera(enabled) {
			const shouldEnable = Boolean(enabled);
			if (this.isSimpleRouteFirstPersonCamera === shouldEnable) return;

			if (shouldEnable) {
				if (this.map && !this.simpleRouteCameraSnapshot) {
					const center = this.map.getCenter();
					this.simpleRouteCameraSnapshot = {
						center: [center.lng, center.lat],
						zoom: this.map.getZoom(),
						pitch: this.map.getPitch(),
						bearing: this.map.getBearing(),
					};
				}
				this.isSimpleRouteFirstPersonCamera = true;
				this.cinematicPitch = SIMPLE_ROUTE_FIRST_PERSON_PITCH;
				this.navigationRouteCarLayer?.applyFirstPersonCamera?.(true);
				this.scheduleCurrentRoadSpeedLimitLookup(
					this.navigationRouteCarLayer?.currentSample?.coordinate ||
						this.navigationRouteCarSample?.coordinate,
					{ force: true },
				);
				return;
			}

			this.isSimpleRouteFirstPersonCamera = false;
			this.resetCurrentRoadSpeedLimit();
			const snapshot = this.simpleRouteCameraSnapshot;
			this.simpleRouteCameraSnapshot = null;
			if (this.map && snapshot) {
				this.cinematicPitch = Math.round(snapshot.pitch);
				this.map.easeTo({
					...snapshot,
					duration: 550,
					essential: true,
				});
			}
		},
		toggleSimpleRouteFirstPersonCamera() {
			this.setSimpleRouteFirstPersonCamera(
				!this.isSimpleRouteFirstPersonCamera,
			);
		},
		renderSimpleRouteCar(routeData) {
			if (!this.map || !routeData?.geometry?.coordinates?.length) {
				return;
			}
			const routePath = createSimpleRoutePath(
				routeData.geometry.coordinates,
			);
			if (!routePath) return;

			const firstSample = interpolateSimpleRoutePath(routePath, 0);
			const animationDuration = getSimpleRouteCarDuration(
				routeData.distance,
			);
			const modelConfig = getSimpleRouteVehicleModel(routeData.profile);
			this.navigationRouteCarSample = firstSample;

			SIMPLE_ROUTE_CAR_LAYER_IDS.slice()
				.reverse()
				.forEach((layerId) => {
					if (this.map.getLayer(layerId)) {
						this.map.removeLayer(layerId);
					}
				});
			if (this.map.getSource(SIMPLE_ROUTE_CAR_SOURCE_ID)) {
				this.map.removeSource(SIMPLE_ROUTE_CAR_SOURCE_ID);
			}

			if (this.navigationRouteCarAnimationFrame) {
				window.cancelAnimationFrame(
					this.navigationRouteCarAnimationFrame,
				);
				this.navigationRouteCarAnimationFrame = null;
			}

			const carLayer = createSimpleRouteCarLayer(
				routePath,
				animationDuration,
				firstSample,
				modelConfig,
				{
					shouldUseFirstPersonCamera: () =>
						this.isSimpleRouteFirstPersonCamera,
					onRouteSample: (routeSample) => {
						this.scheduleCurrentRoadSpeedLimitLookup(
							routeSample.coordinate,
						);
					},
				},
			);
			this.navigationRouteCarLayer = markRaw(carLayer);
			this.map.addLayer(carLayer);
			if (this.isSimpleRouteFirstPersonCamera) {
				this.scheduleCurrentRoadSpeedLimitLookup(firstSample.coordinate, {
					force: true,
				});
			}
		},
		renderSimpleRoute(routeData) {
			if (!this.map || !routeData?.geometry?.coordinates?.length) {
				return;
			}
			this.clearSimpleRoute({ preserveFirstPersonCamera: true });

			this.map.addSource(SIMPLE_ROUTE_SOURCE_ID, {
				type: "geojson",
				data: {
					type: "Feature",
					properties: {
						isApproximate: routeData.isApproximate,
					},
					geometry: routeData.geometry,
				},
			});
			this.map.addLayer({
				id: SIMPLE_ROUTE_LAYER_IDS[0],
				type: "line",
				source: SIMPLE_ROUTE_SOURCE_ID,
				layout: {
					"line-cap": "round",
					"line-join": "round",
				},
				paint: {
					"line-color": "#050506",
					"line-width": [
						"interpolate",
						["linear"],
						["zoom"],
						10,
						9,
						15,
						15,
					],
					"line-opacity": 0.9,
					"line-blur": 1.2,
				},
			});
			this.map.addLayer({
				id: SIMPLE_ROUTE_LAYER_IDS[1],
				type: "line",
				source: SIMPLE_ROUTE_SOURCE_ID,
				layout: {
					"line-cap": "round",
					"line-join": "round",
				},
				paint: {
					"line-color": [
						"case",
						["boolean", ["get", "isApproximate"], false],
						"#f4f2eb",
						"#ff4ecb",
					],
					"line-width": [
						"interpolate",
						["linear"],
						["zoom"],
						10,
						15,
						15,
						24,
					],
					"line-opacity": 0.24,
					"line-blur": 8,
				},
			});
			this.map.addLayer({
				id: SIMPLE_ROUTE_LAYER_IDS[2],
				type: "line",
				source: SIMPLE_ROUTE_SOURCE_ID,
				layout: {
					"line-cap": "round",
					"line-join": "round",
				},
				paint: {
					"line-color": [
						"case",
						["boolean", ["get", "isApproximate"], false],
						"#f4f2eb",
						"#ff4ecb",
					],
					"line-width": [
						"interpolate",
						["linear"],
						["zoom"],
						10,
						4,
						15,
						7,
					],
					"line-opacity": 0.96,
				},
			});

			this.navigationRouteMarkers = [
				this.createSimpleRouteMarker(
					"起",
					routeData.start.coordinates,
					"start",
				),
				this.createSimpleRouteMarker(
					"迄",
					routeData.end.coordinates,
					"end",
				),
			].filter(Boolean);
			this.navigationRouteSummary = {
				startName: routeData.start.name,
				endName: routeData.end.name,
				distance: routeData.distance,
				duration: routeData.duration,
				profile: routeData.profile,
				isApproximate: routeData.isApproximate,
			};
			this.renderSimpleRouteCar(routeData);
			if (this.isSimpleRouteFirstPersonCamera) {
				this.navigationRouteCarLayer?.applyFirstPersonCamera?.(true);
				return;
			}
			this.fitSimpleRouteBounds(routeData.geometry.coordinates);
		},
		fitSimpleRouteBounds(coordinates) {
			if (!this.map || !coordinates?.length) return;
			const bounds = new mapboxGl.LngLatBounds();
			coordinates.forEach((coordinate) => bounds.extend(coordinate));
			if (bounds.isEmpty()) return;

			const { clientWidth, clientHeight } = this.map.getContainer();
			const leftPadding =
				clientWidth > 1000 ? Math.min(440, clientWidth * 0.3) : 60;
			const rightPadding =
				clientWidth > 1000 ? Math.min(360, clientWidth * 0.24) : 60;
			const verticalPadding =
				clientHeight > 680 ? 150 : Math.max(60, clientHeight * 0.12);

			this.map.fitBounds(bounds, {
				padding: {
					top: verticalPadding,
					bottom: verticalPadding,
					left: leftPadding,
					right: rightPadding,
				},
				maxZoom: 15.5,
				duration: 950,
				pitch: Math.max(54, Math.min(this.map.getPitch(), 62)),
				bearing: this.map.getBearing(),
				essential: true,
			});
		},
		clearSimpleRoute(options = {}) {
			const preserveFirstPersonCamera =
				options.preserveFirstPersonCamera === true;
			if (!preserveFirstPersonCamera) {
				this.setSimpleRouteFirstPersonCamera(false);
			}
			this.resetCurrentRoadSpeedLimit();
			if (this.navigationRouteCarAnimationFrame) {
				window.cancelAnimationFrame(
					this.navigationRouteCarAnimationFrame,
				);
				this.navigationRouteCarAnimationFrame = null;
			}
			if (this.navigationRouteCarUpdateFrame) {
				window.cancelAnimationFrame(
					this.navigationRouteCarUpdateFrame,
				);
				this.navigationRouteCarUpdateFrame = null;
			}
			if (this.map && this.navigationRouteCarZoomHandler) {
				this.map.off("zoom", this.navigationRouteCarZoomHandler);
			}
			this.navigationRouteCarZoomHandler = null;
			this.navigationRouteCarSample = null;
			this.navigationRouteCarLayer = null;
			if (this.navigationRouteMarkers?.length) {
				this.navigationRouteMarkers.forEach((marker) => {
					marker.remove();
				});
			}
			this.navigationRouteMarkers = [];
			if (this.map) {
				SIMPLE_ROUTE_CAR_LAYER_IDS.slice()
					.reverse()
					.forEach((layerId) => {
						if (this.map.getLayer(layerId)) {
							this.map.removeLayer(layerId);
						}
					});
				if (this.map.getSource(SIMPLE_ROUTE_CAR_SOURCE_ID)) {
					this.map.removeSource(SIMPLE_ROUTE_CAR_SOURCE_ID);
				}
				SIMPLE_ROUTE_LAYER_IDS.slice()
					.reverse()
					.forEach((layerId) => {
						if (this.map.getLayer(layerId)) {
							this.map.removeLayer(layerId);
						}
					});
				if (this.map.getSource(SIMPLE_ROUTE_SOURCE_ID)) {
					this.map.removeSource(SIMPLE_ROUTE_SOURCE_ID);
				}
			}
			this.navigationRouteSummary = null;
			if (!preserveFirstPersonCamera) {
				this.isSimpleRouteFirstPersonCamera = false;
				this.simpleRouteCameraSnapshot = null;
			}
		},

		/* Functions that change the viewing experience of the map */
		// 1. Zoom to a location
		// [[lng, lat], zoom, pitch, bearing, savedLocationName]
		easeToLocation(location_array, options = {}) {
			if (!this.map) return;
			const preserveCamera = options.preserveCamera === true;
			const duration = Number.isFinite(Number(options.duration))
				? Number(options.duration)
				: 4000;
			const currentPitch = this.map.getPitch();
			const currentBearing = this.map.getBearing();
			if (location_array?.zoom) {
				this.map.easeTo({
					center: [location_array.center_x, location_array.center_y],
					zoom: location_array.zoom,
					duration,
					pitch: preserveCamera
						? currentPitch
						: location_array.pitch,
					bearing: preserveCamera
						? currentBearing
						: location_array.bearing,
				});
			} else {
				this.map.easeTo({
					center: location_array[0],
					zoom: location_array[1],
					duration,
					pitch: preserveCamera ? currentPitch : location_array[2],
					bearing: preserveCamera
						? currentBearing
						: location_array[3],
				});
			}
		},
		// 2. Fly to a location
		flyToLocation(location_array) {
			this.map.flyTo({
				center: location_array,
				duration: 1000,
			});
		},
		zoomCinematicMap(delta) {
			if (!this.map) return;
			const minZoom =
				typeof this.map.getMinZoom === "function"
					? this.map.getMinZoom()
					: MapObjectConfig.minZoom;
			const maxZoom =
				typeof this.map.getMaxZoom === "function"
					? this.map.getMaxZoom()
					: MapObjectConfig.maxZoom;
			const nextZoom = Math.min(
				maxZoom,
				Math.max(minZoom, this.map.getZoom() + delta),
			);

			this.map.easeTo({
				zoom: nextZoom,
				duration: 520,
				essential: true,
			});
		},
		rotateCinematicMap(delta) {
			if (!this.map) return;
			this.map.easeTo({
				bearing: this.map.getBearing() + delta,
				duration: 620,
				essential: true,
			});
		},
		setCinematicMapPitch(pitch) {
			const numericPitch = Number(pitch);
			const maxPitch = MapObjectConfig.maxPitch || 78;
			const fallbackPitch =
				CityMapView[this.pendingMapViewCity]?.pitch ||
				MapObjectConfig.pitch;
			const nextPitch = Number.isFinite(numericPitch)
				? Math.min(maxPitch, Math.max(0, numericPitch))
				: fallbackPitch;

			this.cinematicPitch = Math.round(nextPitch);
			if (!this.map) return;
			this.map.easeTo({
				pitch: nextPitch,
				duration: 420,
				essential: true,
			});
		},
		panCinematicMap(direction) {
			if (!this.map) return;
			const centerPoint = this.map.project(this.map.getCenter());
			const distance = 180;
			const offsets = {
				up: [0, -distance],
				down: [0, distance],
				left: [-distance, 0],
				right: [distance, 0],
			};
			const offset = offsets[direction] || [0, 0];
			const nextCenter = this.map.unproject([
				centerPoint.x + offset[0],
				centerPoint.y + offset[1],
			]);

			this.map.easeTo({
				center: nextCenter,
				duration: 520,
				essential: true,
			});
		},
		resetCinematicMapView() {
			this.updateMapViewForCity(this.pendingMapViewCity || "default");
		},
		// 3. Force map to resize after sidebar collapses
		resizeMap() {
			if (this.map) {
				setTimeout(() => {
					this.map.resize();
				}, 200);
			}
		},
		// 4. Update the zoom and center of the map
		updateMapViewForCity(city) {
			this.pendingMapViewCity = city || "default";
			if (!this.map) return;
			const mapView = CityMapView[city] || CityMapView.default;
			if (!this.map.loaded()) {
				return;
			}
			if (!this.hasPlayedInitialReveal) {
				this.playInitialMapReveal(city);
				return;
			}
			this.map.easeTo({
				center: mapView.center,
				zoom: mapView.zoom,
				pitch: mapView.pitch,
				bearing: mapView.bearing,
				duration: 1200,
				essential: true,
			});
			this.cinematicPitch = mapView.pitch;
		},

		/* Map Filtering */
		// 1. Add a filter based on a each map layer's properties (byParam)
		filterByParam(map_filter, map_configs, xParam, yParam) {
			// If there are layers loading, don't filter
			if (this.loadingLayers.length > 0) return;
			const dialogStore = useDialogStore();
			if (!this.map || dialogStore.dialogs.moreInfo) {
				return;
			}
			map_configs.map((map_config) => {
				let mapLayerId = `${map_config.index}-${map_config.type}-${map_config.city}`;
				if (map_config && map_config.type === "arc") {
					this.deckGlLayer[mapLayerId].config.data = this.deckGlLayer[
						mapLayerId
					].data.filter((d) => {
						if (
							map_filter.byParam.xParam &&
							map_filter.byParam.yParam &&
							xParam &&
							yParam
						) {
							return (
								d.properties[map_filter.byParam.xParam] ===
									xParam &&
								d.properties[map_filter.byParam.yParam] ===
									yParam
							);
						} else if (map_filter.byParam.yParam && yParam) {
							return (
								d.properties[map_filter.byParam.yParam] ===
								yParam
							);
						} else if (map_filter.byParam.xParam && xParam) {
							return (
								d.properties[map_filter.byParam.xParam] ===
								xParam
							);
						}
					});
					this.renderDeckGLLayer();
					return;
				}
				// If x and y both exist, filter by both
				if (
					map_filter.byParam.xParam &&
					map_filter.byParam.yParam &&
					xParam &&
					yParam
				) {
					this.map.setFilter(mapLayerId, [
						"all",
						["==", ["get", map_filter.byParam.xParam], xParam],
						["==", ["get", map_filter.byParam.yParam], yParam],
					]);
				}
				// If only y exists, filter by y
				else if (map_filter.byParam.yParam && yParam) {
					this.map.setFilter(mapLayerId, [
						"==",
						["get", map_filter.byParam.yParam],
						yParam,
					]);
				}
				// default to filter by x
				else if (map_filter.byParam.xParam && xParam) {
					this.map.setFilter(mapLayerId, [
						"==",
						["get", map_filter.byParam.xParam],
						xParam,
					]);
				}
			});
		},
		// 2. filter by layer name (byLayer)
		filterByLayer(map_configs, xParam) {
			const dialogStore = useDialogStore();
			// If there are layers loading, don't filter
			if (this.loadingLayers.length > 0) return;
			if (!this.map || dialogStore.dialogs.moreInfo) {
				return;
			}
			map_configs.map((map_config) => {
				let mapLayerId = `${map_config.index}-${map_config.type}-${map_config.city}`;
				if (map_config.title !== xParam) {
					this.map.setLayoutProperty(
						mapLayerId,
						"visibility",
						"none",
					);
				} else {
					this.map.setLayoutProperty(
						mapLayerId,
						"visibility",
						"visible",
					);
				}
			});
		},
		// 3. Remove any property filters on a map layer
		clearByParamFilter(map_configs) {
			const dialogStore = useDialogStore();
			if (!this.map || dialogStore.dialogs.moreInfo) {
				return;
			}
			map_configs.map((map_config) => {
				let mapLayerId = `${map_config.index}-${map_config.type}-${map_config.city}`;
				if (map_config && map_config.type === "arc") {
					this.deckGlLayer[mapLayerId].config.data =
						this.deckGlLayer[mapLayerId].data;
					this.renderDeckGLLayer();
					return;
				}
				this.map.setFilter(mapLayerId, null);
			});
		},
		// 4. Remove any layer filters on a map layer.
		clearByLayerFilter(map_configs) {
			const dialogStore = useDialogStore();
			if (!this.map || dialogStore.dialogs.moreInfo) {
				return;
			}
			map_configs.map((map_config) => {
				let mapLayerId = `${map_config.index}-${map_config.type}-${map_config.city}`;
				this.map.setLayoutProperty(mapLayerId, "visibility", "visible");
			});
		},

		/* Find Closest Data Point */
		// 1. Calculate the Haversine distance between two points
		findClosestLocation(userCoords, locations) {
			// Check if userCoords has valid latitude and longitude
			if (
				!userCoords ||
				typeof userCoords.latitude !== "number" ||
				typeof userCoords.longitude !== "number"
			) {
				throw new Error("Invalid user coordinates");
			}

			let minDistance = Infinity;
			let closestLocation = null;

			for (let location of locations) {
				try {
					// Check if location, location.geometry, and location.geometry.coordinates are valid
					if (
						!location ||
						!location.geometry ||
						!Array.isArray(location.geometry.coordinates)
					) {
						continue; // Skip this location if any of these are invalid
					}
					const [lon, lat] = location.geometry.coordinates;

					// Check if longitude and latitude are valid numbers
					if (typeof lon !== "number" || typeof lat !== "number") {
						continue; // Skip this location if coordinates are not numbers
					}

					// Calculate the Haversine distance
					const distance = calculateHaversineDistance(
						{
							latitude: userCoords.latitude,
							longitude: userCoords.longitude,
						},
						{ latitude: lat, longitude: lon },
					);

					// Update the closest location if the current distance is smaller
					if (distance < minDistance) {
						minDistance = distance;
						closestLocation = location;
					}
				} catch (e) {
					// Catch and log any errors during processing
					console.error(
						`Error processing location: ${JSON.stringify(
							location,
						)}`,
						e,
					);
				}
			}
			return closestLocation;
		},
		// 2. Fly to the closest location and trigger a popup
		async flyToClosestLocationAndTriggerPopup(lng, lat) {
			if (this.loadingLayers.length !== 0) return;
			this.loadingLayers.push("rendering");

			let targetLayer = -1;
			this.currentVisibleLayers.forEach((layer, index) => {
				if (["circle", "symbol"].includes(layer.split("-")[1])) {
					targetLayer = index;
				}
			});

			if (targetLayer === -1) {
				this.loadingLayers.pop();
				return;
			}

			this.removePopup();
			const layerSourceType =
				this.mapConfigs[this.currentVisibleLayers[targetLayer]].source;

			const features = [];

			if (layerSourceType === "geojson") {
				features.push(
					...this.map.getSource(
						`${this.currentVisibleLayers[targetLayer]}-source`,
					)._data.features,
				);
			} else {
				const res = await axios.get(
					`${
						location.origin
					}/geo_server/taipei_vioc/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=taipei_vioc%3A${
						this.mapConfigs[this.currentVisibleLayers[targetLayer]]
							.index
					}&maxFeatures=1000000&outputFormat=application%2Fjson`,
				);

				features.push(...res.data.features);
			}

			if (!features || features.length === 0) {
				this.loadingLayers.pop();
				return;
			}

			const res = this.findClosestLocation(
				{
					longitude: lng,
					latitude: lat,
				},
				features,
			);

			this.map.once("moveend", () => {
				setTimeout(
					() => {
						this.manualTriggerPopup();
					},
					layerSourceType === "geojson" ? 0 : 500,
				);
			});

			this.flyToLocation(res.geometry.coordinates);
		},

		/* Clearing the map */
		// 1. Called when the user is switching between maps
		clearOnlyLayers() {
			this.currentLayers.forEach((element) => {
				this.removeRainAnimationLayer(element);
				if (this.map.getLayer(element)) {
					this.map.removeLayer(element);
				}
				if (this.map.getSource(`${element}-source`)) {
					this.map.removeSource(`${element}-source`);
				}
			});
			this.currentLayers = [];
			this.mapConfigs = {};
			this.currentVisibleLayers = [];
			this.removePopup();
		},
		// 2. Called when user navigates away from the map
		clearEntireMap() {
			this.clearSimpleRoute();
			this.stopAnimation();
			if (this.labelRestoreTimer) {
				window.clearTimeout(this.labelRestoreTimer);
				this.labelRestoreTimer = null;
			}
			this.removeAllRainAnimationLayers();
			this.currentLayers = [];
			this.mapConfigs = {};
			this.map = null;
			this.currentVisibleLayers = [];
			this.overlay = null;
			this.deckGlLayer = {};
			this.rainAnimationLayers = {};
			this.removePopup();
			this.tempMarkerCoordinates = null;
		},
	},
});
