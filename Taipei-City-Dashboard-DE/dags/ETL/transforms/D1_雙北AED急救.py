"""
transforms/D1_雙北AED急救.py
==============================
合併台北市與新北市 AED 設備清單，輸出地圖定位用的整合表。

欄位說明：
  台北（RID: cd050577）：已含標準化欄位 latitude/longitude（raw 階段已轉換）
  新北（PAGE_ID: 61B29F27）：無座標 → 用 hosp_addr 呼叫 nominatim geocoding 補齊
"""

import re
import time
import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from geopy.geocoders import ArcGIS


_geolocator = ArcGIS(timeout=8)

def _geocode_one(addr: str) -> tuple[str, float | None, float | None]:
    try:
        loc = _geolocator.geocode(addr)
        if loc:
            return addr, loc.latitude, loc.longitude
    except Exception as e:
        print(f"[geocode] 失敗 '{addr}': {e}")
    return addr, None, None


def build_geocache(addresses: list[str], max_workers: int = 8) -> dict:
    """並行 geocoding，對所有唯一地址嘗試轉換，失敗的由呼叫端 fallback 行政區"""
    unique = list({str(a).strip() for a in addresses if not pd.isna(a) and str(a).strip()})
    cache: dict = {}
    if not unique:
        return cache
    print(f"[geocode] 並行送出 {len(unique)} 筆地址（max_workers={max_workers}）")
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        for addr, lat, lng in ex.map(_geocode_one, unique):
            cache[addr] = (lat, lng)
    hit = sum(1 for v in cache.values() if v[0] is not None)
    print(f"[geocode] 完成：{hit}/{len(unique)} 筆成功，{len(unique)-hit} 筆將 fallback 行政區中心")
    return cache

# ── 工具函式 ────────────────────────────────────────────────────
def extract_district(text) -> str | None:
    """從地址字串萃取行政區名稱"""
    if pd.isna(text):
        return None
    m = re.search(r'([^\s市縣]+[區鄉鎮市])', str(text))
    return m.group(1) if m else str(text).strip()


def _to_float(val) -> float | None:
    try:
        result = float(val)
        return result if result == result else None  # NaN check
    except (TypeError, ValueError):
        return None


def _pick(df: pd.DataFrame, candidates: list) -> str | None:
    """不分大小寫，找第一個存在的欄位名"""
    col_map = {c.lower(): c for c in df.columns}
    for c in candidates:
        if c.lower() in col_map:
            return col_map[c.lower()]
    return None


# ── 台北解析（raw 已標準化，直接重新命名即可）──────────────────
def _parse_taipei(df: pd.DataFrame) -> pd.DataFrame:
    print(f"[台北AED] 欄位：{df.columns.tolist()}")

    # raw 存為已標準化欄位時直接用；原始 API 欄位作為 fallback
    name_col    = _pick(df, ["place_name", "場所名稱"])
    addr_col    = _pick(df, ["address", "場所地址"])
    lat_col     = _pick(df, ["latitude", "緯度"])
    lng_col     = _pick(df, ["longitude", "經度"])
    cat_col     = _pick(df, ["place_category", "場所分類", "場所類別"])
    type_col    = _pick(df, ["place_type", "場所類型"])
    aed_loc_col = _pick(df, ["aed_location", "AED放置地點", "aed放置地點"])
    dist_col    = _pick(df, ["district"])

    rows = []
    for _, r in df.iterrows():
        rows.append({
            "city_scope":     "Taipei",
            "city":           "臺北市",
            "place_name":     r[name_col] if name_col else None,
            "address":        r[addr_col] if addr_col else None,
            "district":       r[dist_col] if dist_col else None,
            "latitude":       _to_float(r[lat_col]) if lat_col else None,
            "longitude":      _to_float(r[lng_col]) if lng_col else None,
            "place_category": r[cat_col] if cat_col else None,
            "place_type":     r[type_col] if type_col else None,
            "aed_location":   r[aed_loc_col] if aed_loc_col else None,
            "source_trace":   "data.taipei（衛生局 AED 設置地點）",
        })
    return pd.DataFrame(rows)


# ── 新北解析（原始 API 欄位 + geocoding 補座標）──────────────
NTPC_DIST_MAP = {
    "八里區": (25.147, 121.398), "板橋區": (25.011, 121.461),
    "新莊區": (25.035, 121.445), "三重區": (25.063, 121.488),
    "中和區": (24.998, 121.501), "永和區": (25.009, 121.516),
    "土城區": (24.971, 121.443), "樹林區": (24.991, 121.424),
    "汐止區": (25.062, 121.640), "新店區": (24.968, 121.541),
}

def _parse_ntpc(df: pd.DataFrame, cache: dict):
    rows = []
    for _, r in df.iterrows():
        addr = str(r.get("hosp_addr", "") or "").strip()
        dist = str(r.get("district", "") or "").strip()

        lat, lng = cache.get(addr, (None, None))

        if lat is None or lng is None:
            lat, lng = NTPC_DIST_MAP.get(dist, (25.011, 121.461))

        rows.append({
            "city_scope":     "NewTaipei",
            "city":           "新北市",
            "place_name":     r.get("organizer"),
            "address":        addr,
            "district":       dist,
            "latitude":       lat,
            "longitude":      lng,
            "place_category": r.get("type"),
            "place_type":     None,
            "aed_location":   r.get("location"),
            "source_trace":   "data.ntpc（新北市 AED）",
        })
    return pd.DataFrame(rows)
# ── 主 transform 入口 ──────────────────────────────────────────
def transform(
    raw: dict[str, pd.DataFrame],
    data_time: str,
    config: dict,
    dataset_configs: dict,
) -> pd.DataFrame:

    ntpc_raw = raw["D1_新北AED"]
    addrs = ntpc_raw["hosp_addr"].tolist() if "hosp_addr" in ntpc_raw.columns else []
    geo_cache = build_geocache(addrs)

    tp_df   = _parse_taipei(raw["D1_台北AED"])
    ntpc_df = _parse_ntpc(ntpc_raw, geo_cache)

    final = pd.concat([tp_df, ntpc_df], ignore_index=True)

    # district 補齊：優先用已有值，否則從 address 萃取
    final["district"] = final.apply(
        lambda r: r["district"] if pd.notna(r["district"]) and str(r["district"]).strip()
                  else extract_district(r["address"]),
        axis=1,
    )

    final["data_time"] = data_time
    final["data_mode"] = "real"

    # 移除座標為 None 的列（geocoding 也失敗的才會到這）
    before = len(final)
    final = final.dropna(subset=["latitude", "longitude"])
    dropped = before - len(final)
    if dropped:
        print(f"[Transform] 移除 {dropped} 筆無座標資料")

    # 統一欄位順序
    final = final[[
        "data_time", "city_scope", "city", "district",
        "place_name", "address", "latitude", "longitude",
        "place_category", "place_type", "aed_location",
        "source_trace", "data_mode",
    ]].reset_index(drop=True)

    by_city = final.groupby("city_scope").size().to_dict()
    print(f"[Transform] D1 雙北AED 完成，共 {len(final)} 筆，分布：{by_city}")
    return final