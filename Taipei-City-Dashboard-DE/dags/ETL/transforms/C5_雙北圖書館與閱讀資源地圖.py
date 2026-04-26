import pandas as pd
import re
import time
import requests
from typing import Dict


def _pick(df: pd.DataFrame, candidates: list) -> str | None:
    """不分大小寫,找第一個存在的欄位名"""
    col_map = {c.lower(): c for c in df.columns}
    for c in candidates:
        if c.lower() in col_map:
            return col_map[c.lower()]
    return None


def _to_float(val) -> float | None:
    """安全地轉換為浮點數"""
    try:
        result = float(val)
        return result if result == result else None
    except (TypeError, ValueError):
        return None


def _extract_district(text) -> str | None:
    """從地址字串萃取行政區名稱"""
    if pd.isna(text):
        return None
    m = re.search(r'([^\s市縣]+[區鄉鎮市])', str(text))
    return m.group(1) if m else str(text).strip()


def _parse_taipei_branches(branches_df: pd.DataFrame) -> pd.DataFrame:
    """處理臺北市圖書館分館資料"""
    name_col = _pick(branches_df, ["name", "分館名稱", "圖書館名稱"])
    addr_col = _pick(branches_df, ["address", "地址", "館舍地址"])
    phone_col = _pick(branches_df, ["phone", "電話", "聯絡電話", "tel"])
    lat_col = _pick(branches_df, ["latitude", "緯度", "lat"])
    lng_col = _pick(branches_df, ["longitude", "經度", "lng"])

    rows = []
    for _, r in branches_df.iterrows():
        rows.append({
            "city": "臺北市",
            "city_scope": "Taipei",
            "name": r[name_col] if name_col else None,
            "address": r[addr_col] if addr_col else None,
            "phone": r[phone_col] if phone_col else None,
            "lat": _to_float(r[lat_col]) if lat_col else None,
            "lng": _to_float(r[lng_col]) if lng_col else None,
            "district": _extract_district(r[addr_col]) if addr_col else None,
        })
    return pd.DataFrame(rows)


def _aggregate_seat_status(seats_df: pd.DataFrame) -> pd.DataFrame:
    """聚合座位狀況資料(按分館名稱)"""
    if seats_df.empty:
        return pd.DataFrame()

    lib_col = _pick(seats_df, ["library_name", "分館名稱", "name"])
    avail_col = _pick(seats_df, ["available_seats", "可用座位", "available"])
    total_col = _pick(seats_df, ["total_seats", "總座位", "total"])
    time_col = _pick(seats_df, ["update_time", "更新時間", "time"])

    if not lib_col:
        return pd.DataFrame()

    if time_col:
        seats_df = seats_df.sort_values(time_col, ascending=False)

    seats_agg = []
    for lib_name in seats_df[lib_col].unique():
        lib_data = seats_df[seats_df[lib_col] == lib_name].iloc[0]
        seats_agg.append({
            "name": lib_name,
            "available_seats": _to_float(lib_data[avail_col]) if avail_col else None,
            "total_seats": _to_float(lib_data[total_col]) if total_col else None,
            "seat_update_time": lib_data[time_col] if time_col else None,
        })
    return pd.DataFrame(seats_agg)


def _merge_seat_info(branches: pd.DataFrame, seats: pd.DataFrame) -> pd.DataFrame:
    if seats.empty:
        for col in ["available_seats", "total_seats", "seat_update_time"]:
            branches[col] = None
        return branches
    return branches.merge(seats, on="name", how="left")


def _parse_taipei_libraries(branches_df: pd.DataFrame, seats_df: pd.DataFrame) -> pd.DataFrame:
    taipei = _parse_taipei_branches(branches_df)
    seats_agg = _aggregate_seat_status(seats_df)
    return _merge_seat_info(taipei, seats_agg)


def _geocode_address(address: str) -> Dict[str, any]:
    """
    使用 ArcGIS REST API 進行地理編碼。
    對台灣地址辨識率極高，且不易發生 403 封鎖。
    """
    if not address:
        return {'lat': None, 'lng': None}

    # 1. 地址清洗：移除樓層與括號資訊
    clean_address = re.sub(r'[\(\uff08].*?[\)\uff09]', '', str(address))
    clean_address = re.sub(r'(\d+樓|B\d+).*', '', clean_address, flags=re.IGNORECASE)
    
    # 確保地址包含縣市資訊以利定位
    if '新北市' not in clean_address and '台北市' not in clean_address and '臺北市' not in clean_address:
        clean_address = f"新北市{clean_address}"

    url = "https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates"
    params = {
        'f': 'json',
        'singleLine': clean_address,
        'maxLocations': 1,
        'outFields': 'Addr_type'
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        # ArcGIS 限制較寬鬆，但維持良好習慣加入微小延遲
        time.sleep(0.3) 
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('candidates'):
            loc = data['candidates'][0]['location']
            return {'lat': loc['y'], 'lng': loc['x']}
    except Exception as e:
        print(f" ✗ API 錯誤: {e}")

    return {'lat': None, 'lng': None}


def _batch_geocode_addresses(df: pd.DataFrame, address_col: str) -> pd.DataFrame:
    results = []
    total = len(df)
    for idx, row in df.iterrows():
        addr = str(row[address_col])
        print(f"  [{idx+1}/{total}] {addr}", end=" ")
        coords = _geocode_address(addr)
        if coords['lat']:
            print(f"✓ ({coords['lat']:.4f})")
        else:
            print("✗")
        results.append(coords)
    return pd.DataFrame(results)


NTPC_DIST_MAP = {
    "八里區": (25.147, 121.398), "板橋區": (25.011, 121.461), "新莊區": (25.035, 121.445),
    "三重區": (25.063, 121.488), "中和區": (24.998, 121.501), "永和區": (25.009, 121.516),
    "土城區": (24.971, 121.443), "樹林區": (24.991, 121.424), "汐止區": (25.062, 121.640),
    "新店區": (24.968, 121.541), "淡水區": (25.174, 121.443), "蘆洲區": (25.087, 121.460),
    "五股區": (25.078, 121.433), "泰山區": (25.112, 121.437), "林口區": (25.110, 121.362),
    "平溪區": (25.015, 121.693), "雙溪區": (25.088, 121.833), "貢寮區": (25.140, 121.810),
    "瑞芳區": (25.105, 121.805), "三芝區": (25.256, 121.500), "烏來區": (24.866, 121.550),
}


def _parse_ntpc_libraries(ntpc_df: pd.DataFrame) -> pd.DataFrame:
    print(f"[新北分館] 原始欄位：{ntpc_df.columns.tolist()}")

    name_col = _pick(ntpc_df, ["name", "圖書館名稱"])
    addr_col = _pick(ntpc_df, ["address", "地址", "館舍地址"])
    phone_col = _pick(ntpc_df, ["phone", "電話", "聯絡電話", "tel"])
    lat_col = _pick(ntpc_df, ["latitude", "緯度", "lat"])
    lng_col = _pick(ntpc_df, ["longitude", "經度", "lng"])

    has_coords = lat_col and lng_col and ntpc_df[lat_col].notna().any()
    geocoded_data = None
    if not has_coords and addr_col:
        print("[新北分館] 啟動地理編碼定位...")
        geocoded_data = _batch_geocode_addresses(ntpc_df, addr_col)

    rows = []
    for idx, r in ntpc_df.iterrows():
        addr = r[addr_col] if addr_col else None
        dist = _extract_district(addr)
        lat = _to_float(r[lat_col]) if lat_col else None
        lng = _to_float(r[lng_col]) if lng_col else None

        if (lat is None or lng is None) and geocoded_data is not None:
            lat, lng = geocoded_data.iloc[idx]['lat'], geocoded_data.iloc[idx]['lng']

        if lat is None or lng is None:
            lat, lng = NTPC_DIST_MAP.get(dist, (25.011, 121.461))

        rows.append({
            "city": "新北市", "city_scope": "NewTaipei",
            "name": r[name_col] if name_col else None,
            "address": addr, "phone": r[phone_col] if phone_col else None,
            "lat": lat, "lng": lng, "district": dist,
            "available_seats": None, "total_seats": None, "seat_update_time": None,
        })
    return pd.DataFrame(rows)


def transform(raw: dict[str, pd.DataFrame], data_time: str, **kwargs) -> pd.DataFrame:
    print("[C5 轉換開始] 雙北圖書館整合")
    taipei_branches = raw.get("臺北市立圖書館各分館暨民眾閱覽室", pd.DataFrame())
    taipei_seats = raw.get("臺北市立圖書館查詢座位狀況API", pd.DataFrame())
    ntpc_libraries = raw.get("新北市立圖書館地址電話一覽表", pd.DataFrame())

    taipei = _parse_taipei_libraries(taipei_branches, taipei_seats) if not taipei_branches.empty else pd.DataFrame()
    ntpc = _parse_ntpc_libraries(ntpc_libraries) if not ntpc_libraries.empty else pd.DataFrame()

    combined = pd.concat([taipei, ntpc], ignore_index=True)
    combined["data_time"] = data_time
    combined["data_mode"] = "real"

    cols = ["data_time", "city", "city_scope", "district", "name", "address", "phone", "lat", "lng", "data_mode"]
    return combined[[c for c in cols if c in combined.columns]].reset_index(drop=True)