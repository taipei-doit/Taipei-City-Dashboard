#!/usr/bin/env python3
"""
從民生公共物聯網空品 STA 拉取 Things（含 PM2.5 最新觀測與座標），篩選雙北後輸出 GeoJSON，
供 Mapbox heatmap 或其他圖層使用。

GeoJSON 不必手動編：本腳本把 API 的 JSON 轉成標準 FeatureCollection 寫成檔案即可；
持續更新可交給 cron／systemd timer 定期執行，並將產出放到前端可讀的靜態路徑（例如
Taipei-City-Dashboard-FE 的 public/mapData/）或由後端提供下載。
"""

from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
import time
import urllib.parse
import urllib.request
from typing import Any

try:
    import certifi
except ImportError:
    certifi = None

BASE = "https://sta.colife.org.tw/STA_AirQuality_EPAIoT/v1.0/Things"

# 雙北常見寫法（依 API 實際字串增刪）
DEFAULT_CITIES = frozenset({"臺北市", "台北市", "新北市"})

EXPAND = (
    "Locations,"
    "Datastreams($filter=name eq 'PM2.5';"
    "$expand=Observations($top=1;$orderby=phenomenonTime desc))"
)


def _ssl_context(insecure: bool) -> ssl.SSLContext | None:
    if insecure:
        return ssl._create_unverified_context()
    if certifi is not None:
        return ssl.create_default_context(cafile=certifi.where())
    return None


def _http_get_json(url: str, ctx: ssl.SSLContext | None, timeout: int) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        return json.loads(resp.read().decode("utf-8"))


def thing_to_feature(
    thing: dict[str, Any],
    *,
    pm25_min: float,
    pm25_max: float,
) -> dict[str, Any] | None:
    """單一 Thing 轉成 GeoJSON Feature；資料不完整或超過閾值則略過。"""
    props = thing.get("properties") or {}
    city = props.get("city") or ""

    locs = thing.get("Locations") or []
    if not locs:
        return None
    loc0 = locs[0]
    geom = loc0.get("location") or {}
    coords = geom.get("coordinates")
    if not coords or len(coords) < 2:
        return None

    streams = thing.get("Datastreams") or []
    if not streams:
        return None
    ds0 = streams[0]
    if ds0.get("name") != "PM2.5":
        return None
    obs_list = ds0.get("Observations") or []
    if not obs_list:
        return None
    obs0 = obs_list[0]
    raw_result = obs0.get("result")
    try:
        pm25 = float(raw_result)
    except (TypeError, ValueError):
        return None
    if pm25 < pm25_min or pm25 > pm25_max:
        return None

    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [float(coords[0]), float(coords[1])]},
        "properties": {
            "weight": pm25,
            "city": city,
            "station": thing.get("name") or "",
            "stationID": props.get("stationID"),
            "phenomenonTime": obs0.get("phenomenonTime"),
        },
    }


def fetch_all_features(
    *,
    cities: frozenset[str],
    page_size: int,
    max_things: int,
    ctx: ssl.SSLContext | None,
    timeout: int,
    sleep_s: float,
    pm25_min: float,
    pm25_max: float,
) -> tuple[list[dict[str, Any]], int, int]:
    """
    分頁抓取 Things，回傳 (features, 已處理 Thing 筆數, API 宣告總筆數)。
    """
    features: list[dict[str, Any]] = []
    skip = 0
    total_reported: int | None = None
    processed = 0

    while True:
        if max_things and processed >= max_things:
            break
        top = page_size
        if max_things:
            top = min(page_size, max_things - processed)
            if top <= 0:
                break

        params: dict[str, str] = {
            "$top": str(top),
            "$skip": str(skip),
            "$orderby": "@iot.id asc",
            "$select": "name,properties",
            "$expand": EXPAND,
        }
        url = f"{BASE}?{urllib.parse.urlencode(params)}"
        data = _http_get_json(url, ctx, timeout)
        if total_reported is None:
            total_reported = int(data.get("@iot.count", 0))

        batch = data.get("value") or []
        if not batch:
            break

        for thing in batch:
            if max_things and processed >= max_things:
                break
            processed += 1
            city = (thing.get("properties") or {}).get("city") or ""
            if city not in cities:
                continue
            feat = thing_to_feature(thing, pm25_min=pm25_min, pm25_max=pm25_max)
            if feat:
                features.append(feat)

        skip += len(batch)
        if len(batch) < int(params["$top"]):
            break
        if sleep_s > 0:
            time.sleep(sleep_s)

    return features, processed, total_reported or 0


def run_sample(ctx: ssl.SSLContext | None, timeout: int) -> None:
    params = {
        "$top": "1",
        "$orderby": "@iot.id asc",
        "$select": "name,properties",
        "$expand": EXPAND,
    }
    url = f"{BASE}?{urllib.parse.urlencode(params)}"
    data = _http_get_json(url, ctx, timeout)
    print("=== 請求 URL ===\n", url, "\n")
    print("=== @iot.count ===\n", data.get("@iot.count"), "\n")
    items = data.get("value") or []
    if not items:
        print("value 為空")
        return
    thing = items[0]
    print("=== 第一筆 Thing ===\n")
    print(json.dumps(thing, ensure_ascii=False, indent=2))
    feat = thing_to_feature(thing, pm25_min=-1.0, pm25_max=500.0)
    print("\n=== 若納入 GeoJSON 會長這樣（不篩縣市）===\n")
    print(json.dumps(feat, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sample",
        action="store_true",
        help="只打一筆樣本並印出 JSON（與先前測試相同用途）",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="heatmap_pm25.geojson",
        help="輸出 GeoJSON 路徑；設為 - 則寫到 stdout",
    )
    parser.add_argument("--page-size", type=int, default=150, help="每頁 $top（建議 100–300）")
    parser.add_argument(
        "--max-things",
        type=int,
        default=0,
        help="最多處理幾筆 Thing（0 表示不限制；雙北子集仍會篩）",
    )
    parser.add_argument(
        "--cities",
        default=",".join(sorted(DEFAULT_CITIES)),
        help="要保留的縣市名稱，逗號分隔（需與 API properties.city 完全一致）",
    )
    parser.add_argument("--pm25-min", type=float, default=0.0)
    parser.add_argument("--pm25-max", type=float, default=500.0)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.0,
        help="每頁之間暫停秒數（禮貌爬蟲；全量一萬多筆時可設 0.05–0.2）",
    )
    parser.add_argument("--pretty", action="store_true", help="GeoJSON 縮排（檔案較大）")
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="略過 TLS 憑證驗證（僅本機除錯；預設使用 certifi）",
    )
    args = parser.parse_args()
    insecure = args.insecure or os.environ.get("STA_TLS_INSECURE", "") == "1"
    ctx = _ssl_context(insecure)

    if args.sample:
        run_sample(ctx, args.timeout)
        return

    cities = frozenset(c.strip() for c in args.cities.split(",") if c.strip())
    features, processed, total = fetch_all_features(
        cities=cities,
        page_size=max(1, args.page_size),
        max_things=max(0, args.max_things),
        ctx=ctx,
        timeout=args.timeout,
        sleep_s=max(0.0, args.sleep),
        pm25_min=args.pm25_min,
        pm25_max=args.pm25_max,
    )
    collection = {"type": "FeatureCollection", "features": features}
    indent = 2 if args.pretty else None
    text = json.dumps(collection, ensure_ascii=False, indent=indent)

    if args.output == "-":
        sys.stdout.write(text)
        if not text.endswith("\n"):
            sys.stdout.write("\n")
    else:
        out_path = args.output
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(
            f"已寫入 {out_path}：{len(features)} 個點（處理 Thing {processed} 筆／API 宣告共 {total} 筆）",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
