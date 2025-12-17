// utils/cars.js
import * as THREE from "three";
import { interpolateAlongSegment } from "../utilityFunctions/geometryUtils";

/**
 * 更新車子進度、方向、位置，並生成 Mapbox FeatureCollection features
 * @param {Array} cars - 每台車的資料陣列
 * @param {Object} options - 選項
 * @param {number} [options.offsetMeters=-30] - 2D 偏移距離
 * @returns {Array} features - Mapbox GeoJSON features
 */
export function updateCarsPosition(cars, options = {}) {
    const offsetMeters = options.offsetMeters ?? -30;

    return cars.map(car => {
        // 更新進度
        car.progress = Math.min(car.progress + car.speed, 1);

        // 取得當前位置
        const pos = interpolateAlongSegment(car.coords, car.progress);

        // 計算方向向量
        let dir = null;
        if (car.progress >= 1) {
            dir = car.lastDir;
        } else {
            const nextProgress = Math.min(car.progress + 0.01, 1);
            const nextPos = interpolateAlongSegment(car.coords, nextProgress);
            dir = new THREE.Vector3(
                nextPos[0] - pos[0],
                nextPos[1] - pos[1],
                nextPos[2] - pos[2]
            ).normalize();
            car.lastDir = dir;
        }

        // 記錄當前經緯度
        car.currentLngLat = pos;

        // 計算 2D 偏移經緯度
        let offsetLngLat = pos;
        if (dir) {
            const side = new THREE.Vector3(-dir.y, dir.x, 0).normalize();
            const lngOffset = side.x * offsetMeters * 0.00001;
            const latOffset = side.y * offsetMeters * 0.00001;
            offsetLngLat = [pos[0] + lngOffset, pos[1] + latOffset];
        }

        return {
            type: "Feature",
            geometry: { type: "Point", coordinates: offsetLngLat },
            properties: { trainnumber: car.trainnumber }
        };
    });
}
