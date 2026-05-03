#!/usr/bin/env python3
"""從民生公共物聯網空品 STA 抓取 PM2.5 並輸出 GeoJSON。

特色：
- 分頁抓取 Things，避免單次回傳上限問題
- 雙北以「關鍵字」模糊比對（臺北 / 台北 / 新北）
- PM2.5（μg/m³）依台灣環保署 24h breakpoint 換算 AQI 與分類顏色
- 觀測時間附加 UTC+8 在地時間
- 輸出標準 GeoJSON FeatureCollection（含 weight 給 Mapbox heatmap 用）
- 可選同時輸出 API 對應欄位之原始 CSV（扁平化 + properties JSON）

可定時執行（cron / systemd timer / Airflow）；產物可直接放在儀表板前端的
public/mapData/ 下，再以 source: "geojson" 的 map_config 載入。
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import ssl
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

try:
    import certifi
except ImportError:
    certifi = None

# ---------------------------------------------------------------------------
# 常數
# ---------------------------------------------------------------------------

STA_BASE = "https://sta.colife.org.tw/STA_AirQuality_EPAIoT/v1.0/Things"

DEFAULT_CITY_KEYWORDS: tuple[str, ...] = ("臺北", "台北", "新北")

# Datastreams 過濾出 PM2.5，並只取最新一筆 Observation
EXPAND_CLAUSE = (
    "Locations,"
    "Datastreams($filter=name eq 'PM2.5';"
    "$expand=Observations($top=1;$orderby=phenomenonTime desc))"
)

# 台灣環保署 PM2.5 → AQI 24h breakpoint
# (PM2.5_low, PM2.5_high, AQI_low, AQI_high)
PM25_AQI_BREAKPOINTS: list[tuple[float, float, int, int]] = [
    (0.0, 15.4, 0, 50),
    (15.5, 35.4, 51, 100),
    (35.5, 54.4, 101, 150),
    (54.5, 150.4, 151, 200),
    (150.5, 250.4, 201, 300),
    (250.5, 500.4, 301, 500),
]

# (AQI 上限, 英文等級, 中文等級, 顏色)；對應提供的色塊
AQI_LEVELS: list[tuple[int, str, str, str]] = [
    (50, "Good", "良好", "#00E400"),
    (100, "Moderate", "普通", "#FFFF00"),
    (150, "Unhealthy for Sensitive Groups", "對敏感族群不健康", "#FF7E00"),
    (200, "Unhealthy", "對所有族群不健康", "#FF0000"),
    (300, "Very Unhealthy", "非常不健康", "#8F3F97"),
    (500, "Hazardous", "危害", "#7E0023"),
]

TPE_TZ = timezone(timedelta(hours=8))

logger = logging.getLogger("fetch_pm25")


# ---------------------------------------------------------------------------
# 工具函式
# ---------------------------------------------------------------------------


def build_ssl_context(insecure: bool) -> ssl.SSLContext | None:
    if insecure:
        # 僅供本機除錯
        return ssl._create_unverified_context()
    if certifi is not None:
        return ssl.create_default_context(cafile=certifi.where())
    return None


def http_get_json(
    url: str,
    *,
    ctx: ssl.SSLContext | None,
    timeout: int,
    retries: int = 3,
    backoff_s: float = 1.0,
) -> dict[str, Any]:
    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            last_err = exc
            if attempt == retries:
                break
            wait = backoff_s * (2 ** (attempt - 1))
            logger.warning("HTTP 失敗（第 %d 次），%s；%.1fs 後重試", attempt, exc, wait)
            time.sleep(wait)
    raise RuntimeError(f"GET 失敗：{url}") from last_err


def is_target_city(city: str | None, keywords: tuple[str, ...]) -> bool:
    if not city:
        return False
    return any(kw in city for kw in keywords)


def pm25_to_aqi(pm25: float) -> int | None:
    """台灣環保署 PM2.5 → AQI 線性內插。輸入 < 0 視為缺值；> 500.4 鎖在 500。"""
    if pm25 < 0:
        return None
    p = round(pm25, 1)
    if p > 500.4:
        return 500
    for c_lo, c_hi, i_lo, i_hi in PM25_AQI_BREAKPOINTS:
        if c_lo <= p <= c_hi:
            return round((i_hi - i_lo) / (c_hi - c_lo) * (p - c_lo) + i_lo)
    return None


def classify_aqi(aqi: int | None) -> tuple[str, str, str]:
    if aqi is None:
        return ("Unknown", "未知", "#999999")
    for upper, en, zh, color in AQI_LEVELS:
        if aqi <= upper:
            return en, zh, color
    return AQI_LEVELS[-1][1], AQI_LEVELS[-1][2], AQI_LEVELS[-1][3]


def to_local_iso(utc_iso: str | None) -> str | None:
    if not utc_iso:
        return None
    try:
        dt = datetime.fromisoformat(utc_iso.replace("Z", "+00:00"))
    except ValueError:
        return utc_iso
    return dt.astimezone(TPE_TZ).isoformat(timespec="seconds")


def _json_cell(obj: Any) -> str:
    if obj is None:
        return ""
    try:
        return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    except (TypeError, ValueError):
        return str(obj)


def _cell(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v)


# CSV 欄位順序（含 STA 扁平欄位 + 腳本衍生欄位，便於對照 GeoJSON）
RAW_CSV_FIELDNAMES: tuple[str, ...] = (
    "fetchedAt",
    "thing_iot_id",
    "thing_name",
    "thing_selfLink",
    "location_iot_id",
    "location_name",
    "location_encodingType",
    "longitude",
    "latitude",
    "city",
    "township",
    "area",
    "areaType",
    "authority",
    "stationID",
    "deviceName",
    "stationName",
    "datastream_iot_id",
    "datastream_name",
    "datastream_description",
    "unitOfMeasurement_json",
    "observation_iot_id",
    "result",
    "phenomenonTime",
    "resultTime",
    "properties_json",
    "computed_aqi",
    "computed_aqi_level",
    "computed_aqi_label_zh",
    "computed_aqi_color",
    "computed_localTime",
)


def thing_to_raw_csv_row(
    thing: dict[str, Any],
    *,
    feature_props: dict[str, Any],
    fetched_at: str,
) -> dict[str, str]:
    """將單一 Thing（已通過雙北篩選且可轉成 Feature）扁平成 CSV 一列。"""
    props = thing.get("properties") or {}
    locs = thing.get("Locations") or []
    loc0 = locs[0] if locs else {}
    geom = (loc0 or {}).get("location") or {}
    coords = geom.get("coordinates") or []
    lng = coords[0] if len(coords) > 0 else ""
    lat = coords[1] if len(coords) > 1 else ""

    streams = thing.get("Datastreams") or []
    ds0 = streams[0] if streams else {}
    obs_list = (ds0 or {}).get("Observations") or []
    obs0 = obs_list[0] if obs_list else {}

    row: dict[str, str] = {k: "" for k in RAW_CSV_FIELDNAMES}
    row["fetchedAt"] = fetched_at
    row["thing_iot_id"] = _cell(thing.get("@iot.id"))
    row["thing_name"] = _cell(thing.get("name"))
    row["thing_selfLink"] = _cell(thing.get("@iot.selfLink"))
    row["location_iot_id"] = _cell(loc0.get("@iot.id"))
    row["location_name"] = _cell(loc0.get("name"))
    row["location_encodingType"] = _cell(loc0.get("encodingType"))
    row["longitude"] = _cell(lng)
    row["latitude"] = _cell(lat)
    row["city"] = _cell(props.get("city"))
    row["township"] = _cell(props.get("township"))
    row["area"] = _cell(props.get("area"))
    row["areaType"] = _cell(props.get("areaType"))
    row["authority"] = _cell(props.get("authority"))
    row["stationID"] = _cell(props.get("stationID"))
    row["deviceName"] = _cell(props.get("deviceName"))
    row["stationName"] = _cell(props.get("stationName"))
    row["datastream_iot_id"] = _cell(ds0.get("@iot.id"))
    row["datastream_name"] = _cell(ds0.get("name"))
    row["datastream_description"] = _cell(ds0.get("description"))
    row["unitOfMeasurement_json"] = _json_cell(ds0.get("unitOfMeasurement"))
    row["observation_iot_id"] = _cell(obs0.get("@iot.id"))
    row["result"] = _cell(obs0.get("result"))
    row["phenomenonTime"] = _cell(obs0.get("phenomenonTime"))
    row["resultTime"] = _cell(obs0.get("resultTime"))
    row["properties_json"] = _json_cell(props)
    row["computed_aqi"] = _cell(feature_props.get("aqi"))
    row["computed_aqi_level"] = _cell(feature_props.get("aqi_level"))
    row["computed_aqi_label_zh"] = _cell(feature_props.get("aqi_label_zh"))
    row["computed_aqi_color"] = _cell(feature_props.get("aqi_color"))
    row["computed_localTime"] = _cell(feature_props.get("localTime"))
    return row


# ---------------------------------------------------------------------------
# Thing → GeoJSON Feature
# ---------------------------------------------------------------------------


def thing_to_feature(
    thing: dict[str, Any],
    *,
    pm25_min: float,
    pm25_max: float,
) -> dict[str, Any] | None:
    """單一 Thing 轉 GeoJSON Feature；缺值或超界回傳 None。"""
    props = thing.get("properties") or {}
    city = props.get("city") or ""

    locs = thing.get("Locations") or []
    if not locs:
        return None
    geom = (locs[0] or {}).get("location") or {}
    coords = geom.get("coordinates")
    if not coords or len(coords) < 2:
        return None
    try:
        lng, lat = float(coords[0]), float(coords[1])
    except (TypeError, ValueError):
        return None

    streams = thing.get("Datastreams") or []
    if not streams:
        return None
    ds0 = streams[0]
    if (ds0.get("name") or "") != "PM2.5":
        return None
    obs_list = ds0.get("Observations") or []
    if not obs_list:
        return None
    obs0 = obs_list[0]
    try:
        pm25 = float(obs0.get("result"))
    except (TypeError, ValueError):
        return None
    if pm25 < pm25_min or pm25 > pm25_max:
        return None

    aqi = pm25_to_aqi(pm25)
    level_en, level_zh, color = classify_aqi(aqi)

    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lng, lat]},
        "properties": {
            # heatmap 用
            "weight": pm25,
            # 顯示與分類
            "pm25": pm25,
            "aqi": aqi,
            "aqi_level": level_en,
            "aqi_label_zh": level_zh,
            "aqi_color": color,
            # 站點 / 行政
            "city": city,
            "township": props.get("township"),
            "area": props.get("area"),
            "station": thing.get("name") or "",
            "stationID": props.get("stationID"),
            "authority": props.get("authority"),
            # 時間
            "phenomenonTime": obs0.get("phenomenonTime"),
            "localTime": to_local_iso(obs0.get("phenomenonTime")),
        },
    }


# ---------------------------------------------------------------------------
# 分頁抓取
# ---------------------------------------------------------------------------


def fetch_features(
    *,
    keywords: tuple[str, ...],
    page_size: int,
    max_things: int,
    ctx: ssl.SSLContext | None,
    timeout: int,
    sleep_s: float,
    pm25_min: float,
    pm25_max: float,
    collect_csv: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, str]], int, int]:
    """以 $skip 分頁掃過 Things；回傳 (features, csv_rows, 已處理 Thing 數, API 宣告總數)。"""
    features: list[dict[str, Any]] = []
    csv_rows: list[dict[str, str]] = []
    skip = 0
    processed = 0
    total_reported: int | None = None
    fetched_at = datetime.now(TPE_TZ).isoformat(timespec="seconds")

    while True:
        if max_things and processed >= max_things:
            break
        top = page_size
        if max_things:
            top = min(page_size, max_things - processed)
            if top <= 0:
                break

        params = {
            "$top": str(top),
            "$skip": str(skip),
            "$orderby": "@iot.id asc",
            "$select": "name,properties",
            "$expand": EXPAND_CLAUSE,
        }
        url = f"{STA_BASE}?{urllib.parse.urlencode(params)}"
        logger.info("GET top=%s skip=%s", top, skip)
        data = http_get_json(url, ctx=ctx, timeout=timeout)
        if total_reported is None:
            total_reported = int(data.get("@iot.count", 0))

        batch = data.get("value") or []
        if not batch:
            break

        for thing in batch:
            if max_things and processed >= max_things:
                break
            processed += 1
            city = (thing.get("properties") or {}).get("city")
            if not is_target_city(city, keywords):
                continue
            feat = thing_to_feature(thing, pm25_min=pm25_min, pm25_max=pm25_max)
            if feat:
                features.append(feat)
                if collect_csv:
                    csv_rows.append(
                        thing_to_raw_csv_row(
                            thing,
                            feature_props=feat["properties"],
                            fetched_at=fetched_at,
                        )
                    )

        skip += len(batch)
        if len(batch) < int(params["$top"]):
            break
        if sleep_s > 0:
            time.sleep(sleep_s)

    return features, csv_rows, processed, total_reported or 0


# ---------------------------------------------------------------------------
# 寫檔（含 atomic rename，避免前端讀到半寫入的檔）
# ---------------------------------------------------------------------------


def write_geojson_atomic(path: Path, payload: dict[str, Any], *, pretty: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    indent = 2 if pretty else None
    text = json.dumps(payload, ensure_ascii=False, indent=indent)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
        if not text.endswith("\n"):
            f.write("\n")
    os.replace(tmp, path)


def write_csv_atomic(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(RAW_CSV_FIELDNAMES), extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow(row)
    os.replace(tmp, path)


def build_collection(features: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "type": "FeatureCollection",
        "generatedAt": datetime.now(TPE_TZ).isoformat(timespec="seconds"),
        "source": "民生公共物聯網 STA Air Quality (EPA IoT)",
        "count": len(features),
        "features": features,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-o",
        "--output",
        default="pm25_realtime.geojson",
        help="輸出 GeoJSON 路徑（- 寫到 stdout）",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=200,
        help="STA 每頁 $top（建議 100–500）",
    )
    parser.add_argument(
        "--max-things",
        type=int,
        default=0,
        help="最多處理幾筆 Thing（0 不限制；雙北子集仍會篩）",
    )
    parser.add_argument(
        "--city-keywords",
        default=",".join(DEFAULT_CITY_KEYWORDS),
        help="目標縣市關鍵字（逗號分隔，模糊比對 properties.city）",
    )
    parser.add_argument("--pm25-min", type=float, default=0.0)
    parser.add_argument("--pm25-max", type=float, default=500.0)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.05,
        help="每頁之間禮貌延遲秒數（建議 0–0.2）",
    )
    parser.add_argument("--pretty", action="store_true", help="GeoJSON 縮排（檔案較大）")
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="略過 TLS 憑證驗證（僅本機除錯，預設用 certifi）",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="詳細日誌（INFO）",
    )
    parser.add_argument(
        "--csv",
        dest="csv_output",
        metavar="PATH",
        nargs="?",
        const="AUTO",
        default="AUTO",
        help=(
            "另存原始 CSV 路徑；不帶參數或 AUTO 表示與 GeoJSON 同路徑、副檔名改為 .csv"
        ),
    )
    parser.add_argument(
        "--no-csv",
        action="store_true",
        help="不要輸出 CSV（僅 GeoJSON）",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    insecure = args.insecure or os.environ.get("STA_TLS_INSECURE", "") == "1"
    ctx = build_ssl_context(insecure)

    keywords = tuple(k.strip() for k in args.city_keywords.split(",") if k.strip())
    if not keywords:
        print("錯誤：--city-keywords 不可為空", file=sys.stderr)
        return 2

    if args.no_csv:
        csv_target: Path | None = None
        collect_csv = False
    elif args.csv_output != "AUTO":
        csv_target = Path(args.csv_output).expanduser()
        collect_csv = True
    elif args.output != "-":
        csv_target = Path(args.output).expanduser().with_suffix(".csv")
        collect_csv = True
    else:
        csv_target = None
        collect_csv = False

    started = time.monotonic()
    features, csv_rows, processed, total = fetch_features(
        keywords=keywords,
        page_size=max(1, args.page_size),
        max_things=max(0, args.max_things),
        ctx=ctx,
        timeout=args.timeout,
        sleep_s=max(0.0, args.sleep),
        pm25_min=args.pm25_min,
        pm25_max=args.pm25_max,
        collect_csv=collect_csv,
    )
    elapsed = time.monotonic() - started
    collection = build_collection(features)

    if args.output == "-":
        text = json.dumps(collection, ensure_ascii=False, indent=2 if args.pretty else None)
        sys.stdout.write(text + ("\n" if not text.endswith("\n") else ""))
    else:
        out_path = Path(args.output).expanduser()
        write_geojson_atomic(out_path, collection, pretty=args.pretty)
        print(
            (
                f"已寫入 {out_path}：{len(features)} 個 Feature "
                f"（處理 {processed} / API 宣告總數 {total}，{elapsed:.1f}s）"
            ),
            file=sys.stderr,
        )

    if csv_target is not None:
        write_csv_atomic(csv_target, csv_rows)
        print(
            f"已寫入 CSV {csv_target}：{len(csv_rows)} 列",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
