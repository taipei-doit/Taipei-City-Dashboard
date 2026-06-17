// composables/useWindEngine.js
import { watch, onUnmounted, ref } from "vue";
import { useMapStore } from "../store/mapStore";
import { storeToRefs } from "pinia";

// ── 效能參數 ──────────────────────────────────────────────
const MAX_PARTICLES = 1000;
const PARTICLE_STEP = 0.0012;
const COMFORT_STEP = 0.0008;
const SPATIAL_STEP = 0.008;
const GRID_DECAY = 0.985;
const HIDE_SEC_PER_M = 1 / 40;
const MIN_HIDE_MS = 1500;
const MAX_HIDE_MS = 12000;
const COMFORT_UPDATE_INTERVAL = 25;
const DT = 2;
const MAX_SPAN = 0.03;
const MAX_CELLS = 3500;

// ── 氣象站 IDW 參數 ───────────────────────────────────────
const WEATHER_PATH = "./mapData/weather_station_metrotaipei.geojson";
// IDW 最大有效距離（度），超過此距離的站點不納入計算
const IDW_MAX_DIST = 0.08;
// 最小距離防除零
const IDW_MIN_DIST = 0.0005;

const EMPTY = { type: "FeatureCollection", features: [] };
const SRC_PARTICLES = "wind:particles";
const SRC_COMFORT = "wind:comfort-grid";
const LAYER_COMFORT = "wind:comfort-heat";
const LAYER_ARROWS = "wind:arrows";
const IMAGE_ARROW = "wind:arrow";

export const useWindEngine = (options = {}) => {
	const mapStore = useMapStore();
	const { map: mapRef } = storeToRefs(mapStore);
	const m = () => mapRef.value;

	const windDir = options.windDir ?? ref(45);
	const windSpeed = options.windSpeed ?? ref(3);

	// ── 氣象站狀態（內部管理） ────────────────────────────
	const useStationData = ref(false);
	let stations = []; // [{ lng, lat, dir, speed }]
	let stationsLoaded = false;

	// ── 載入天氣站 ────────────────────────────────────────
	const loadStations = async () => {
		if (stationsLoaded) return;
		try {
			const res = await fetch(WEATHER_PATH);
			if (!res.ok) throw new Error(`HTTP ${res.status}`);
			const geojson = await res.json();
			stations = geojson.features
				.filter((f) => {
					const { wind_speed, wind_direction } = f.properties;
					return wind_speed !== "NULL" && wind_direction !== "NULL";
				})
				.map((f) => {
					const spd = parseFloat(f.properties.wind_speed);
					const dir = parseFloat(f.properties.wind_direction);
					return {
						lng: f.geometry.coordinates[0],
						lat: f.geometry.coordinates[1],
						dir: isNaN(dir) ? 0 : dir,
						speed: isNaN(spd) ? 0 : spd,
					};
				})
				.filter((st) => st.speed > 0);
			stationsLoaded = true;
			// console.log(`[WindEngine] 載入 ${stations.length} 個有效氣象站`);
		} catch (e) {
			console.warn("[WindEngine] 天氣站載入失敗:", e);
		}
	};

	// ── IDW 插值：回傳指定位置的本地風向與風速 ──────────
	// 當附近找不到任何站點時，回退到全域設定值
	const getLocalWind = (lng, lat) => {
		const maxDistSq = IDW_MAX_DIST * IDW_MAX_DIST;
		let wSin = 0,
			wCos = 0,
			wSpeed = 0,
			totalW = 0;

		for (const st of stations) {
			const dx = lng - st.lng;
			const dy = lat - st.lat;
			const distSq = dx * dx + dy * dy;
			if (distSq > maxDistSq) continue;

			// 反距離加權 w = 1 / dist
			const w = 1 / Math.max(Math.sqrt(distSq), IDW_MIN_DIST);
			const rad = (st.dir * Math.PI) / 180;
			wSin += Math.sin(rad) * w;
			wCos += Math.cos(rad) * w;
			wSpeed += st.speed * w;
			totalW += w;
		}

		// 找不到鄰近站點，回退全域值
		if (totalW === 0) {
			return { dir: windDir.value, speed: windSpeed.value };
		}

		const dir =
			((Math.atan2(wSin / totalW, wCos / totalW) * 180) / Math.PI + 360) %
			360;
		// 用全域 windSpeed 作為倍率調整（讓 UI 滑桿仍有作用）
		const speed = Math.max(
			1,
			Math.min(15, (wSpeed / totalW) * (windSpeed.value / 5)),
		);
		return { dir, speed };
	};

	// ── 全域風向向量（非 station mode 使用） ─────────────
	let BASE_VX = 0,
		BASE_VY = 0;
	const updateWindVector = () => {
		const rad = (windDir.value * Math.PI) / 180;
		BASE_VX = Math.sin(rad) * 0.00001 * windSpeed.value;
		BASE_VY = Math.cos(rad) * 0.00001 * windSpeed.value;
	};
	updateWindVector();

	// ── 粒子向量計算（封裝，供 update 呼叫） ─────────────
	// 回傳 { vx, vy, angle }，已考慮 station mode
	const getParticleVector = (lng, lat) => {
		if (stations.length > 0) {
			const lw = getLocalWind(lng, lat);
			const rad = (lw.dir * Math.PI) / 180;
			return {
				vx: Math.sin(rad) * 0.00001 * lw.speed,
				vy: Math.cos(rad) * 0.00001 * lw.speed,
				angle: lw.dir,
			};
		}
		return { vx: BASE_VX, vy: BASE_VY, angle: windDir.value };
	};

	let animationFrameId = null;
	let buildingIndex = {};
	let comfortGrid = [];
	let comfortIndex = {};
	let comfortSkip = 1;
	let particles = [];
	let frameCount = 0;
	let isZooming = false;
	let isMoving = false;
	let layersMounted = false;
	let fetchController = null;

	// ── [修正] generation 計數器，防止舊批次污染新狀態 ──
	let fetchGen = 0;
	let rebuildGen = 0;

	const featurePool = Array.from({ length: MAX_PARTICLES }, () => ({
		type: "Feature",
		geometry: { type: "Point", coordinates: [0, 0] },
		properties: { angle: 0 },
	}));

	// ── 視窗邊界 ──────────────────────────────────────────
	const getSafeBounds = () => {
		const map = m();
		if (!map) return { s: 0, n: 0, w: 0, e: 0 };
		const b = map.getBounds(),
			c = map.getCenter();
		return {
			s: Math.max(b.getSouth(), c.lat - MAX_SPAN),
			n: Math.min(b.getNorth(), c.lat + MAX_SPAN),
			w: Math.max(b.getWest(), c.lng - MAX_SPAN),
			e: Math.min(b.getEast(), c.lng + MAX_SPAN),
		};
	};

	// ── 建物抓取 ──────────────────────────────────────────
	// [修正] 用 generation 確保只有最新一次 moveend/zoomend 的抓取會生效
	const fetchBuildings = () => {
		const map = m();
		if (!map) return;
		const gen = ++fetchGen;
		const tryFetch = () => {
			if (gen !== fetchGen) return; // 已被更新的事件取代，放棄
			const features = map.querySourceFeatures("taipei_building_3d_source", {
				sourceLayer: "tp_building_height84-18p8j0",
			});
			if (!features.length) {
				setTimeout(tryFetch, 300);
				return;
			}
			rebuildIndex(features);
		};
		tryFetch();
	};

	// ── 粒子 ──────────────────────────────────────────────
	const resetParticle = (p, b) => {
		const lR = b.e - b.w;
		const hR = b.n - b.s;
		const buf = 0.0001;

		// ▼ 用本地風向決定出生位置
		const { vx, vy } = getParticleVector((b.w + b.e) / 2, (b.s + b.n) / 2);

		// 水平風比較強
		if (Math.abs(vx) > Math.abs(vy)) {
			// 往東吹 → 從左邊出生
			if (vx > 0) {
				p.lng = b.w + buf;
				p.lat = b.s + Math.random() * hR;
			}
			// 往西吹 → 從右邊出生
			else {
				p.lng = b.e - buf;
				p.lat = b.s + Math.random() * hR;
			}
		}
		// 垂直風比較強
		else {
			// 往北吹 → 從下方出生
			if (vy > 0) {
				p.lng = b.w + Math.random() * lR;
				p.lat = b.s + buf;
			}
			// 往南吹 → 從上方出生
			else {
				p.lng = b.w + Math.random() * lR;
				p.lat = b.n - buf;
			}
		}

		p.hiddenUntil = performance.now() + Math.random() * 1200;
	};

	// [修正] 生成粒子後清除過長的 hiddenUntil，避免繼承舊區域的建築碰撞狀態
	const generateParticles = () => {
		const b = getSafeBounds();
		const now = performance.now();
		const raw = [];
		for (let lat = b.s; lat < b.n; lat += PARTICLE_STEP)
			for (let lng = b.w; lng < b.e; lng += PARTICLE_STEP)
				raw.push({ lng, lat, hiddenUntil: 0 });
		if (raw.length > MAX_PARTICLES) {
			raw.sort(() => Math.random() - 0.5);
			raw.length = MAX_PARTICLES;
		}
		particles = raw;

		// 清除任何殘留的過長 hiddenUntil（新區域不應繼承舊碰撞狀態）
		for (const p of particles) {
			if (p.hiddenUntil - now > 2000) {
				p.hiddenUntil = now + Math.random() * 1200;
			}
		}
	};

	// ── 熱力格 ────────────────────────────────────────────
	const buildComfortGrid = (b) => {
		comfortGrid = [];
		comfortIndex = {};

		const s = COMFORT_STEP;

		const x0Raw = Math.floor(b.w / s);
		const x1 = Math.floor(b.e / s);
		const y0Raw = Math.floor(b.s / s);
		const y1 = Math.floor(b.n / s);

		const total = (x1 - x0Raw + 1) * (y1 - y0Raw + 1);
		comfortSkip =
			total > MAX_CELLS ? Math.ceil(Math.sqrt(total / MAX_CELLS)) : 1;

		// ▼ 讓起點對齊 comfortSkip，與 update 裡的查詢邏輯一致
		const x0 = Math.floor(x0Raw / comfortSkip) * comfortSkip;
		const y0 = Math.floor(y0Raw / comfortSkip) * comfortSkip;

		for (let y = y0; y <= y1; y += comfortSkip) {
			for (let x = x0; x <= x1; x += comfortSkip) {
				const cs = s * comfortSkip;
				const id = `${x}:${y}`;

				const cell = {
					type: "Feature",
					geometry: {
						type: "Polygon",
						coordinates: [
							[
								[x * s, y * s],
								[x * s + cs, y * s],
								[x * s + cs, y * s + cs],
								[x * s, y * s + cs],
								[x * s, y * s],
							],
						],
					},
					properties: { id, count: 0, frequency: 0 },
				};

				comfortGrid.push(cell);
				comfortIndex[id] = cell;
			}
		}
	};

	const flushComfortGrid = () => {
		let max = 0;
		for (const c of comfortGrid) {
			c.properties.count *= GRID_DECAY;
			if (c.properties.count > max) max = c.properties.count;
		}
		const norm = Math.max(max, 5);
		for (const c of comfortGrid)
			c.properties.frequency = Math.pow(c.properties.count / norm, 0.7);
		m()
			?.getSource(SRC_COMFORT)
			?.setData({ type: "FeatureCollection", features: comfortGrid });
	};

	// ── 建築索引（分批不阻塞） ────────────────────────────
	const pointInRing = (lng, lat, ring) => {
		let inside = false;
		for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
			const [xi, yi] = ring[i],
				[xj, yj] = ring[j];
			if (
				yi > lat !== yj > lat &&
				lng < ((xj - xi) * (lat - yi)) / (yj - yi) + xi
			)
				inside = !inside;
		}
		return inside;
	};

	const pointInBuilding = (lng, lat, { geometry }) => {
		if (!geometry) return false;
		const rings =
			geometry.type === "Polygon"
				? geometry.coordinates
				: geometry.coordinates[0];
		for (const ring of rings) if (pointInRing(lng, lat, ring)) return true;
		return false;
	};

	// [修正] 用 generation 防止多次重疊的 rebuildIndex 互相污染
	const rebuildIndex = (features) => {
		buildingIndex = {};
		const gen = ++rebuildGen;
		let i = 0;
		const BATCH = 200;
		const process = () => {
			if (gen !== rebuildGen) return; // 已有更新的 rebuild，舊批次直接放棄
			const end = Math.min(i + BATCH, features.length);
			for (; i < end; i++) {
				const { geometry, properties } = features[i];
				if (!geometry) continue;
				let coords =
					geometry.type === "Polygon"
						? geometry.coordinates[0]
						: geometry.type === "MultiPolygon"
							? geometry.coordinates.flat(2)
							: [];
				if (!coords.length) continue;
				let mnLng = Infinity,
					mxLng = -Infinity,
					mnLat = Infinity,
					mxLat = -Infinity;
				for (const [ln, lt] of coords) {
					if (ln < mnLng) mnLng = ln;
					if (ln > mxLng) mxLng = ln;
					if (lt < mnLat) mnLat = lt;
					if (lt > mxLat) mxLat = lt;
				}
				const meta = {
					feature: features[i],
					bbox: { mnLng, mxLng, mnLat, mxLat },
					height:
						properties?.height || properties?.render_height || 20,
				};
				const sx = Math.floor(mnLng / SPATIAL_STEP),
					ex = Math.floor(mxLng / SPATIAL_STEP);
				const sy = Math.floor(mnLat / SPATIAL_STEP),
					ey = Math.floor(mxLat / SPATIAL_STEP);
				for (let x = sx; x <= ex; x++)
					for (let y = sy; y <= ey; y++)
						(buildingIndex[`${x}:${y}`] ??= []).push(meta);
			}
			if (i < features.length) setTimeout(process, 0);
		};
		process();
	};

	// ── 圖層掛載 / 卸載 ───────────────────────────────────
	const mountLayers = () => {
		const map = m();
		if (!map || layersMounted) return;
		if (!map.hasImage(IMAGE_ARROW)) {
			const c = Object.assign(document.createElement("canvas"), {
				width: 32,
				height: 32,
			});
			const ctx = c.getContext("2d");
			ctx.fillStyle = ctx.strokeStyle = "#00d4ff";
			ctx.lineWidth = 2;
			ctx.beginPath();
			ctx.moveTo(16, 6);
			ctx.lineTo(16, 26);
			ctx.stroke();
			ctx.beginPath();
			ctx.moveTo(16, 6);
			ctx.lineTo(10, 14);
			ctx.lineTo(22, 14);
			ctx.closePath();
			ctx.fill();
			map.addImage(IMAGE_ARROW, ctx.getImageData(0, 0, 32, 32));
		}
		if (!map.getSource(SRC_PARTICLES))
			map.addSource(SRC_PARTICLES, { type: "geojson", data: EMPTY });
		if (!map.getSource(SRC_COMFORT))
			map.addSource(SRC_COMFORT, { type: "geojson", data: EMPTY });
		if (!map.getLayer(LAYER_COMFORT))
			map.addLayer({
				id: LAYER_COMFORT,
				type: "fill",
				source: SRC_COMFORT,
				paint: {
					"fill-color": [
						"interpolate",
						["linear"],
						["get", "frequency"],
						0,
						"rgba(255,80,80,0.4)",
						0.15,
						"rgba(255,160,80,0.4)",
						0.35,
						"rgba(160,220,255,0.4)",
						0.7,
						"rgba(0,170,255,0.6)",
					],
					"fill-opacity": 0.8,
				},
			});
		if (!map.getLayer(LAYER_ARROWS))
			map.addLayer({
				id: LAYER_ARROWS,
				type: "symbol",
				source: SRC_PARTICLES,
				layout: {
					"icon-image": IMAGE_ARROW,
					"icon-size": [
						"interpolate",
						["linear"],
						["zoom"],
						12,
						0.2,
						16,
						0.5,
					],
					"icon-rotate": ["get", "angle"],
					"icon-allow-overlap": true,
					"icon-pitch-alignment": "map",
					"icon-rotation-alignment": "map",
				},
				paint: { "icon-opacity": 0.7 },
			});
		layersMounted = true;
	};

	const unmountLayers = () => {
		const map = m();
		if (!map) return;
		[LAYER_ARROWS, LAYER_COMFORT].forEach((id) => {
			if (map.getLayer(id)) map.removeLayer(id);
		});
		[SRC_PARTICLES, SRC_COMFORT].forEach((id) => {
			if (map.getSource(id)) map.removeSource(id);
		});
		if (map.hasImage(IMAGE_ARROW)) map.removeImage(IMAGE_ARROW);
		layersMounted = false;
	};

	// ── 地圖事件 ──────────────────────────────────────────
	const onZoomStart = () => {
		isZooming = true;
		m()?.getSource(SRC_PARTICLES)?.setData(EMPTY);
		m()?.getSource(SRC_COMFORT)?.setData(EMPTY);
	};
	const onZoomEnd = () => {
		isZooming = false;
		const b = getSafeBounds();
		generateParticles();
		buildComfortGrid(b);
		setTimeout(fetchBuildings, 300);
	};
	const onMoveStart = () => {
		isMoving = true;
		m()?.getSource(SRC_PARTICLES)?.setData(EMPTY);
	};
	const onMoveEnd = () => {
		isMoving = false;
		const b = getSafeBounds();
		setTimeout(() => {
			fetchBuildings();
			generateParticles();
			buildComfortGrid(b);
		}, 300);
	};

	const bindMapEvents = () => {
		const map = m();
		if (!map) return;
		map.on("zoomstart", onZoomStart);
		map.on("zoomend", onZoomEnd);
		map.on("movestart", onMoveStart);
		map.on("moveend", onMoveEnd);
	};

	const unbindMapEvents = () => {
		const map = m();
		if (!map) return;
		map.off("zoomstart", onZoomStart);
		map.off("zoomend", onZoomEnd);
		map.off("movestart", onMoveStart);
		map.off("moveend", onMoveEnd);
	};

	// ── 主動畫迴圈 ────────────────────────────────────────
	const update = () => {
		const map = m();
		if (!map?.getSource(SRC_PARTICLES) || isZooming || isMoving) {
			animationFrameId = requestAnimationFrame(update);
			return;
		}

		const now = performance.now();
		const b = getSafeBounds();
		let visCount = 0;

		for (const p of particles) {
			// ▼ 核心變更：每顆粒子取得本地（或全域）風向向量
			const { vx, vy, angle } = getParticleVector(p.lng, p.lat);

			const rawLng = p.lng + vx * DT;
			const rawLat = p.lat + vy * DT;

			// 建築斥力
			const near =
				buildingIndex[
					`${Math.floor(rawLng / SPATIAL_STEP)}:${Math.floor(rawLat / SPATIAL_STEP)}`
				];
			let rx = 0,
				ry = 0;
			if (near) {
				for (const bm of near) {
					const { mnLng, mxLng, mnLat, mxLat } = bm.bbox,
						mg = 0.00025;
					if (
						rawLng > mnLng - mg &&
						rawLng < mxLng + mg &&
						rawLat > mnLat - mg &&
						rawLat < mxLat + mg
					) {
						const dx = rawLng - (mnLng + mxLng) / 2;
						const dy = rawLat - (mnLat + mxLat) / 2;
						const dist = Math.sqrt(dx * dx + dy * dy);
						if (dist > 0) {
							const f = 0.00012 / (dist * 100);
							rx += (dx / dist) * f;
							ry += (dy / dist) * f;
						}
					}
				}
			}

			const s = 0.2;
			const nextLng = p.lng + (vx * (1 - s) + rx * s) * DT;
			const nextLat = p.lat + (vy * (1 - s) + ry * s) * DT;

			if (
				nextLng < b.w ||
				nextLng > b.e ||
				nextLat < b.s ||
				nextLat > b.n
			) {
				resetParticle(p, b);
				continue;
			}

			p.lng = nextLng;
			p.lat = nextLat;
			if (p.hiddenUntil > now) continue;

			// 建築碰撞
			const cands =
				buildingIndex[
					`${Math.floor(nextLng / SPATIAL_STEP)}:${Math.floor(nextLat / SPATIAL_STEP)}`
				];
			if (cands) {
				let hit = null;
				for (const bm of cands) {
					const { mnLng, mxLng, mnLat, mxLat } = bm.bbox;
					if (
						nextLng > mnLng &&
						nextLng < mxLng &&
						nextLat > mnLat &&
						nextLat < mxLat &&
						pointInBuilding(nextLng, nextLat, bm.feature)
					) {
						hit = bm;
						break;
					}
				}
				if (hit) {
					const { mnLng, mxLng, mnLat, mxLat } = hit.bbox;
					const dX =
						Math.abs(nextLng - (mnLng + mxLng) / 2) /
						((mxLng - mnLng) / 2);
					const dY =
						Math.abs(nextLat - (mnLat + mxLat) / 2) /
						((mxLat - mnLat) / 2);
					const W = 1 - Math.max(dX, dY) * 0.6;
					p.hiddenUntil =
						now +
						Math.min(
							MAX_HIDE_MS,
							Math.max(
								MIN_HIDE_MS,
								hit.height * HIDE_SEC_PER_M * 1000,
							),
						) *
							W;
					continue;
				}
			}

			const feat = featurePool[visCount++];
			feat.geometry.coordinates[0] = nextLng;
			feat.geometry.coordinates[1] = nextLat;
			feat.properties.angle = angle; // ▼ 核心變更：用本地角度渲染箭頭方向

			// ▼ 修正 comfort grid index mismatch
			const gx = Math.floor(nextLng / COMFORT_STEP);
			const gy = Math.floor(nextLat / COMFORT_STEP);

			// 對齊 skip
			const cx = Math.floor(gx / comfortSkip) * comfortSkip;
			const cy = Math.floor(gy / comfortSkip) * comfortSkip;

			const cell = comfortIndex[`${cx}:${cy}`];

			if (cell) {
				cell.properties.count += Math.max(1, windSpeed.value * 0.5);
			}
		}

		map.getSource(SRC_PARTICLES)?.setData({
			type: "FeatureCollection",
			features: featurePool.slice(0, visCount),
		});
		if (++frameCount % COMFORT_UPDATE_INTERVAL === 0) flushComfortGrid();
		animationFrameId = requestAnimationFrame(update);
	};

	// ── 對外介面 ──────────────────────────────────────────
	const start = async () => {
		await loadStations(); // 確保天氣站資料已載入再啟動
		mountLayers();
		fetchBuildings();
		generateParticles();
		buildComfortGrid(getSafeBounds());
		bindMapEvents();
		update();
	};

	const stop = () => {
		if (fetchController) fetchController.abort();
		if (animationFrameId) {
			cancelAnimationFrame(animationFrameId);
			animationFrameId = null;
		}
		unbindMapEvents();
		unmountLayers();
	};

	watch([windDir, windSpeed], updateWindVector);
	onUnmounted(stop);

	mapStore.registerWindEngine(start, stop);

	return {
		start,
		stop,
		useStationData, // ref(Boolean)，父元件可 v-model 綁定
		stationsLoaded: () => stationsLoaded, // 查詢載入狀態
	};
};