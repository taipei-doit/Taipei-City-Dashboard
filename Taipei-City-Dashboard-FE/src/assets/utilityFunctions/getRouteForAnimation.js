// src/utils/cutRoute.js
import { point, nearestPointOnLine, lineSlice, distance } from "@turf/turf";

/**
 * 將多段 LineString 按頭尾接成一條 LineString
 */
function mergeSegmentsFallback(segments) {
  if (!segments || !segments.length) return [];
  if (segments.length === 1) return segments[0].slice();

  const idx = new Map();
  const keyOf = (pt) => `${pt[0]},${pt[1]}`;
  segments.forEach((coords, i) => {
    const startK = keyOf(coords[0]);
    const endK = keyOf(coords[coords.length - 1]);
    if (!idx.has(startK)) idx.set(startK, []);
    if (!idx.has(endK)) idx.set(endK, []);
    idx.get(startK).push({ i, atStart: true });
    idx.get(endK).push({ i, atStart: false });
  });

  let startKey = null;
  for (const [k, list] of idx.entries()) if (list.length === 1) { startKey = k; break; }
  if (!startKey) startKey = keyOf(segments[0][0]);

  const visited = new Array(segments.length).fill(false);
  const merged = [];
  let currentKey = startKey;

  // eslint-disable-next-line no-constant-condition
  while (true) {
    const candidates = idx.get(currentKey) || [];
    let chosen = null;
    for (const c of candidates) if (!visited[c.i]) { chosen = c; break; }
    if (!chosen) break;

    const seg = segments[chosen.i].slice();
    visited[chosen.i] = true;
    const segStartKey = keyOf(seg[0]);
    if (segStartKey !== currentKey) seg.reverse();
    if (merged.length === 0) merged.push(...seg);
    else merged.push(...seg.slice(1));
    const last = merged[merged.length - 1];
    currentKey = keyOf(last);
  }

  for (let i = 0; i < segments.length; i++) {
    if (!visited[i]) {
      const seg = segments[i];
      const lastMerged = merged[merged.length - 1];
      const segStartKey = keyOf(seg[0]);
      const lastKey = lastMerged ? keyOf(lastMerged) : null;
      if (lastKey && lastKey === segStartKey) merged.push(...seg.slice(1));
      else merged.push(...seg);
      visited[i] = true;
    }
  }

  return merged;
}

/**
 * 切割線段並保證順序從 start 到 end
 */
export function cutRouteSegment(geojson, startCoord, endCoord) {
  let feature = geojson;
  if (!feature) throw new Error("沒有輸入 geojson");
  if (feature.type === "FeatureCollection") feature = feature.features[0];
  if (feature.type !== "Feature") throw new Error("輸入必須是 Feature 或 FeatureCollection");

  const geom = feature.geometry;
  let mergedCoords;
  if (geom.type === "LineString") mergedCoords = geom.coordinates.slice();
  else if (geom.type === "MultiLineString") mergedCoords = mergeSegmentsFallback(geom.coordinates);
  else throw new Error("只支援 LineString 或 MultiLineString");

  const lineFeature = { type: "Feature", properties: {}, geometry: { type: "LineString", coordinates: mergedCoords } };

  const startPt = point(startCoord);
  const endPt = point(endCoord);
  const snappedStart = nearestPointOnLine(lineFeature, startPt);
  const snappedEnd = nearestPointOnLine(lineFeature, endPt);

  let sliced = lineSlice(snappedStart, snappedEnd, lineFeature);

  const firstPt = sliced.geometry.coordinates[0];
  const lastPt = sliced.geometry.coordinates[sliced.geometry.coordinates.length - 1];

  const distToStartFirst = distance(startPt, point(firstPt));
  const distToStartLast = distance(startPt, point(lastPt));

  if (distToStartLast < distToStartFirst) sliced.geometry.coordinates.reverse();

  return sliced;
}
