"""
C6_雙北宗教場所與社會服務分布 — transform.py（整合版）
=======================================================

整合說明：
  - 原 transform.py 的臺北市部分輸出「每宗教一行聚合行（無座標）」
  - 原 patch_tp_coordinates.py 將臺北市聚合行展開為 35 個個別廟點位
  - 本版本直接在 transform 階段輸出個別廟點位，省去後處理步驟

最終輸出 Schema（全部 row 皆為個別廟點位）：
  data_time, city, religion, color,
  temple_id, name, address, district,
  lng, lat, temple_count,
  clergy_count, believer_count,
  social_medical, social_edu, social_charity, social_total
"""

import pandas as pd
import re
import time
import requests
from typing import Dict


# ══════════════════════════════════════════════════════════
# 常數
# ══════════════════════════════════════════════════════════
RELIGION_COLORS = {
    "道教":     "#E8A838",
    "佛教":     "#C0392B",
    "基督教":   "#2980B9",
    "天主教":   "#8E44AD",
    "一貫道":   "#27AE60",
    "伊斯蘭教": "#1ABC9C",
    "天理教":   "#F39C12",
    "巴哈伊教": "#95A5A6",
    "其他":     "#BDC3C7",
}

NTPC_RELIGION_NORM = {
    "道教": "道教", "佛教": "佛教", "基督教": "基督教",
    "天主教": "天主教", "回教": "伊斯蘭教", "伊斯蘭教": "伊斯蘭教",
    "一貫道": "一貫道", "天理教": "天理教", "巴哈伊教": "巴哈伊教",
}

# 新北市各區中心座標（geocoding 失敗時的備用座標）
NTPC_DIST_CENTER = {
    "新莊區": (25.035, 121.445), "蘆洲區": (25.087, 121.460),
    "三重區": (25.063, 121.488), "中和區": (24.998, 121.501),
    "永和區": (25.009, 121.516), "板橋區": (25.011, 121.461),
    "土城區": (24.971, 121.443), "樹林區": (24.991, 121.424),
    "汐止區": (25.062, 121.640), "新店區": (24.968, 121.541),
    "淡水區": (25.174, 121.443), "五股區": (25.078, 121.433),
    "泰山區": (25.112, 121.437), "林口區": (25.110, 121.362),
    "八里區": (25.147, 121.398), "瑞芳區": (25.105, 121.805),
    "平溪區": (25.015, 121.693), "雙溪區": (25.088, 121.833),
    "貢寮區": (25.140, 121.810), "三芝區": (25.256, 121.500),
    "烏來區": (24.866, 121.550),
}

# ── 臺北市宗教建築靜態座標表（35 筆代表點）───────────────
# 來源：data.taipei「臺北市宗教建築3D模型庫」廟名 + 行政區查表
TP_TEMPLE_COORDS = [
    # (廟名, 行政區, lat, lng, 宗教別)
    # 松山區
    ("臺北府城隍廟",           "松山區", 25.0474, 121.5543, "道教"),
    ("松山霞海城隍廟",         "松山區", 25.0500, 121.5672, "道教"),
    ("慈祐宮",                 "松山區", 25.0515, 121.5679, "道教"),
    # 信義區
    ("奉天宮",                 "信義區", 25.0366, 121.5649, "道教"),
    ("慈惠堂",                 "信義區", 25.0284, 121.5777, "道教"),
    # 大安區
    ("清真寺",                 "大安區", 25.0412, 121.5356, "伊斯蘭教"),
    ("福佑宮",                 "大安區", 25.0330, 121.5427, "道教"),
    # 中山區
    ("行天宮",                 "中山區", 25.0630, 121.5353, "道教"),
    ("劍潭古寺",               "中山區", 25.0794, 121.5245, "佛教"),
    ("臨濟護國禪寺",           "中山區", 25.0628, 121.5245, "佛教"),
    ("文昌宮",                 "中山區", 25.0559, 121.5208, "道教"),
    ("中山基督長老教會",       "中山區", 25.0607, 121.5241, "基督教"),
    # 中正區
    ("臺灣省城隍廟",           "中正區", 25.0433, 121.5073, "道教"),
    ("淨土宗善導寺",           "中正區", 25.0436, 121.5175, "佛教"),
    ("東和禪寺",               "中正區", 25.0427, 121.5197, "佛教"),
    ("聖靈寺",                 "中正區", 25.0310, 121.5128, "佛教"),
    ("濟南基督長老教會",       "中正區", 25.0430, 121.5208, "基督教"),
    # 大同區
    ("保安宮",                 "大同區", 25.0640, 121.5133, "道教"),
    ("台北霞海城隍廟",         "大同區", 25.0567, 121.5099, "道教"),
    ("覺修宮",                 "大同區", 25.0535, 121.5064, "道教"),
    ("李春生紀念基督長老教會", "大同區", 25.0540, 121.5102, "基督教"),
    # 萬華區
    ("天后宮",                 "萬華區", 25.0397, 121.4992, "道教"),
    ("青山宮",                 "萬華區", 25.0387, 121.5004, "道教"),
    ("龍山寺",                 "萬華區", 25.0368, 121.4999, "佛教"),
    ("清水巖祖師廟",           "萬華區", 25.0378, 121.4961, "道教"),
    # 文山區
    ("指南宮",                 "文山區", 24.9856, 121.5806, "道教"),
    ("樟山寺",                 "文山區", 24.9750, 121.5700, "佛教"),
    # 內湖區
    ("護國延平宮",             "內湖區", 25.0736, 121.5864, "道教"),
    ("開漳聖王廟",             "內湖區", 25.0781, 121.5987, "道教"),
    # 士林區
    ("慈諴宮",                 "士林區", 25.0874, 121.5248, "道教"),
    ("葫蘆寺",                 "士林區", 25.0825, 121.5301, "佛教"),
    ("惠濟宮",                 "士林區", 25.1117, 121.4756, "道教"),
    # 北投區
    ("福星宮",                 "北投區", 25.1356, 121.4970, "道教"),
    ("關渡宮",                 "北投區", 25.1259, 121.4633, "道教"),
    ("慈生宮",                 "北投區", 25.1500, 121.4890, "道教"),
]


# ══════════════════════════════════════════════════════════
# 工具函式
# ══════════════════════════════════════════════════════════
def _pick_col(df: pd.DataFrame, candidates: list) -> str | None:
    """候選欄位名，回傳第一個存在的（不分大小寫）"""
    if df.empty:
        return None
    col_lower = {c.lower(): c for c in df.columns}
    for c in candidates:
        if c.lower() in col_lower:
            return col_lower[c.lower()]
    return None


def _to_float(val) -> float | None:
    """安全轉換為浮點數"""
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


def _geocode_address(address: str) -> Dict[str, any]:
    """使用 ArcGIS REST API 進行地理編碼（對台灣地址辨識率高）"""
    if not address:
        return {'lat': None, 'lng': None}

    # 清洗地址：移除樓層與括號資訊
    clean_address = re.sub(r'[\(\uff08].*?[\)\uff09]', '', str(address))
    clean_address = re.sub(r'(\d+樓|B\d+).*', '', clean_address, flags=re.IGNORECASE)

    if '新北市' not in clean_address and '臺北市' not in clean_address:
        clean_address = f"新北市{clean_address}"

    url = "https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates"
    params = {
        'f': 'json',
        'singleLine': clean_address,
        'maxLocations': 1,
        'outFields': 'Addr_type'
    }
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    try:
        time.sleep(0.2)  # 避免 API 限流
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get('candidates'):
            loc = data['candidates'][0]['location']
            return {'lat': loc['y'], 'lng': loc['x']}
    except Exception as e:
        print(f"    [geocode 失敗] {e}")

    return {'lat': None, 'lng': None}


def _batch_geocode_addresses(df: pd.DataFrame, address_col: str) -> pd.DataFrame:
    """批量地理編碼"""
    results = []
    total = len(df)
    print(f"  開始地理編碼 {total} 筆地址...")
    for idx, row in df.iterrows():
        addr = str(row[address_col])
        coords = _geocode_address(addr)
        print(f"    [{idx+1}/{total}] {addr[:30]} {'✓' if coords['lat'] else '✗'}")
        results.append(coords)
    return pd.DataFrame(results)


# ══════════════════════════════════════════════════════════
# 臺北市：社會服務解析（用於對應個別廟的社會服務欄位）
# ══════════════════════════════════════════════════════════
def _tp_social_services(tp_social: pd.DataFrame) -> pd.DataFrame:
    """臺北市社會服務：long 格式 → 按宗教聚合，供個別廟對應"""
    if tp_social.empty:
        return pd.DataFrame()

    df = tp_social.copy()
    religion_col = _pick_col(df, ["宗教別", "religion"])
    if not religion_col:
        return pd.DataFrame()

    # 排除「總計」列
    df = df[df[religion_col].astype(str).str.strip() != "總計"]

    value_cols = [c for c in df.columns if c not in (religion_col, "data_time")]
    for c in value_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    agg = df.groupby(religion_col)[value_cols].max().reset_index()
    agg = agg.rename(columns={religion_col: "religion"})

    # 分類彙總
    medical_cols  = [c for c in agg.columns if "醫" in c]
    edu_cols      = [c for c in agg.columns if "教育" in c]
    charity_cols  = [c for c in agg.columns if "社會" in c or "公益" in c]

    agg["social_medical"] = agg[medical_cols].sum(axis=1) if medical_cols else 0
    agg["social_edu"]     = agg[edu_cols].sum(axis=1)     if edu_cols     else 0
    agg["social_charity"] = agg[charity_cols].sum(axis=1) if charity_cols else 0
    agg["social_total"]   = agg["social_medical"] + agg["social_edu"] + agg["social_charity"]

    return agg[["religion", "social_medical", "social_edu", "social_charity", "social_total"]]


# ══════════════════════════════════════════════════════════
# 臺北市：個別廟點位建立（整合自 patch_tp_coordinates.py）
# ══════════════════════════════════════════════════════════
def _build_tp_individual_temples(tp_social: pd.DataFrame, data_time: str) -> pd.DataFrame:
    """
    直接輸出臺北市 35 個個別廟點位（含座標）。
    社會服務欄位依宗教別對應（同宗教廟共享同一宗教的統計值）。
    取代原本「每宗教一行聚合行（無座標）」的做法。
    """
    print("  [臺北個別廟] 建立點位...")

    # 解析社會服務，以 religion 為 key
    svc_df = _tp_social_services(tp_social)
    svc_map = {}
    if not svc_df.empty:
        svc_map = svc_df.set_index("religion").to_dict(orient="index")

    rows = []
    for name, district, lat, lng, religion in TP_TEMPLE_COORDS:
        svc = svc_map.get(religion, {})
        rows.append({
            "data_time":      data_time,
            "city":           "臺北市",
            "religion":       religion,
            "color":          RELIGION_COLORS.get(religion, "#BDC3C7"),
            "temple_id":      None,
            "name":           name,
            "address":        f"臺北市{district}{name}",
            "district":       district,
            "lng":            lng,
            "lat":            lat,
            "temple_count":   1,   # 個別廟點位，數量 = 1
            "clergy_count":   None,
            "believer_count": None,
            "social_medical": svc.get("social_medical"),
            "social_edu":     svc.get("social_edu"),
            "social_charity": svc.get("social_charity"),
            "social_total":   svc.get("social_total"),
        })

    df = pd.DataFrame(rows)
    print(f"  [臺北個別廟] 完成 {len(df)} 筆")
    return df


# ══════════════════════════════════════════════════════════
# 新北市：個別寺廟解析
# ══════════════════════════════════════════════════════════
def _parse_ntpc_temples(ntpc_temples: pd.DataFrame, data_time: str) -> pd.DataFrame:
    """新北市寺廟：逐間寺廟 + geocoding（座標缺失時）"""
    if ntpc_temples.empty:
        return pd.DataFrame()

    print("  [新北寺廟] 開始處理...")
    df = ntpc_temples.copy()

    id_col       = _pick_col(df, ["id", "temple_id", "tep_id", "_id"])
    name_col     = _pick_col(df, ["name", "temple_name", "tep_name", "寺廟名稱"])
    addr_col     = _pick_col(df, ["address", "temple_address", "tep_address", "地址"])
    district_col = _pick_col(df, ["district", "area", "tep_area", "行政區", "區域"])
    class_col    = _pick_col(df, ["class", "temple_class", "tep_class", "宗教別", "religion"])
    lng_col      = _pick_col(df, ["lng", "longitude", "wgs84ax_longitude", "經度", "x"])
    lat_col      = _pick_col(df, ["lat", "latitude",  "wgs84ay_latitude",  "緯度", "y"])

    # 宗教標準化
    if class_col:
        df["religion"] = df[class_col].map(NTPC_RELIGION_NORM).fillna("其他")
    else:
        df["religion"] = "其他"

    df["color"] = df["religion"].map(RELIGION_COLORS)

    # 座標處理：優先使用原始欄位
    df["lat"] = df[lat_col].apply(_to_float) if lat_col else None
    df["lng"] = df[lng_col].apply(_to_float) if lng_col else None

    has_coords = df["lat"].notna().any() and df["lng"].notna().any()

    # 座標缺失 → geocoding
    if not has_coords and addr_col:
        print("  [新北寺廟] 座標缺失，啟動 geocoding...")
        geocoded = _batch_geocode_addresses(df, addr_col)
        for idx in df.index:
            if pd.isna(df.loc[idx, "lat"]) or pd.isna(df.loc[idx, "lng"]):
                df.loc[idx, "lat"] = geocoded.loc[idx, "lat"]
                df.loc[idx, "lng"] = geocoded.loc[idx, "lng"]

    # 仍缺座標 → 用行政區中心座標補充
    df["district"] = df[district_col].apply(_extract_district) if district_col else None
    for idx in df.index:
        if pd.isna(df.loc[idx, "lat"]) or pd.isna(df.loc[idx, "lng"]):
            dist = df.loc[idx, "district"]
            if dist in NTPC_DIST_CENTER:
                lat, lng = NTPC_DIST_CENTER[dist]
                df.loc[idx, "lat"] = lat
                df.loc[idx, "lng"] = lng

    # 組裝輸出
    out = pd.DataFrame()
    out["data_time"]      = pd.to_datetime(data_time, utc=True, errors="coerce")
    out["city"]           = "新北市"
    out["religion"]       = df["religion"]
    out["color"]          = df["color"]
    out["temple_id"]      = df[id_col].astype(str) if id_col else None
    out["name"]           = df[name_col]            if name_col else None
    out["address"]        = df[addr_col]            if addr_col else None
    out["district"]       = df["district"]
    out["lng"]            = df["lng"]
    out["lat"]            = df["lat"]
    out["temple_count"]   = 1
    out["clergy_count"]   = None
    out["believer_count"] = None
    out["social_medical"] = None
    out["social_edu"]     = None
    out["social_charity"] = None
    out["social_total"]   = None

    print(f"  [新北寺廟] 完成 {len(out)} 筆")
    return out.reset_index(drop=True)


# ══════════════════════════════════════════════════════════
# 主函式
# ══════════════════════════════════════════════════════════
def transform(raw: dict, data_time: str, **_) -> pd.DataFrame:
    """
    輸出單一 DataFrame → hackathon_component_6_religion_ready

    每行皆為個別廟點位（均有 lat/lng）：
      - 臺北市：35 個代表性廟宇（靜態座標），社會服務欄位按宗教別對應
      - 新北市：個別寺廟（原始座標或 geocoding 補充）

    整合說明：
      取代原本「臺北市每宗教一行聚合行（無座標）+ 後續 patch 展開」的兩步驟流程。
    """
    print("[C6 轉換開始] 雙北宗教場所與社會服務分布（整合版）")

    # 取得各資料來源
    tp_social    = raw.get("臺北市宗教社會服務概況",  pd.DataFrame())
    ntpc_temples = raw.get("新北市寺廟資料",           pd.DataFrame())
    data_time    = data_time or str(pd.Timestamp.now(tz="UTC"))

    # ── 臺北市：35 個個別廟點位（整合 patch 邏輯）──────────
    tp_df = _build_tp_individual_temples(tp_social, data_time)

    # ── 新北市：個別寺廟行（原始 or geocoding 補充座標）────
    ntpc_df = _parse_ntpc_temples(ntpc_temples, data_time)

    # ── 合併 ────────────────────────────────────────────────
    df = pd.concat([tp_df, ntpc_df], ignore_index=True)

    if df.empty:
        print("[C6 轉換完成] ⚠️ 無資料")
        return df

    # 統一時間格式
    df["data_time"] = pd.to_datetime(df["data_time"], utc=True, errors="coerce")

    # 修正 city=NaN（新北市資料有時 city 為空）
    mask_ntpc = (
        df["city"].isna() &
        (
            df["address"].str.contains("新北市", na=False) |
            (df["name"].notna() & df["address"].notna())
        )
    )
    if mask_ntpc.sum() > 0:
        df.loc[mask_ntpc, "city"] = "新北市"
        print(f"  [修正] 新北市 city=NaN 修正：{mask_ntpc.sum()} 行")

    df["city"] = df["city"].fillna("新北市")

    # 整理欄位順序
    final_cols = [
        "data_time", "city", "religion", "color",
        "temple_id", "name", "address", "district",
        "lng", "lat", "temple_count",
        "clergy_count", "believer_count",
        "social_medical", "social_edu", "social_charity", "social_total",
    ]
    df = df[final_cols]

    print(f"[C6 轉換完成] ✓ 總筆數：{len(df)}")
    print(f"  city 分布：{df['city'].value_counts().to_dict()}")
    print(f"  臺北市有座標：{df[(df['city']=='臺北市') & df['lat'].notna()].shape[0]} / {(df['city']=='臺北市').sum()}")
    print(f"  新北市有座標：{df[(df['city']=='新北市') & df['lat'].notna()].shape[0]} / {(df['city']=='新北市').sum()}")

    return df


# ══════════════════════════════════════════════════════════
# 獨立執行（直接從 CSV 輸入，適用黑客松本機測試）
# ══════════════════════════════════════════════════════════
if __name__ == "__main__":
    import sys

    # ── 直接從已有的 ready CSV 讀入（跳過 API 抓取）──────
    input_csv = "component_6_religion_final.csv"  # 可改成你的 CSV 路徑

    try:
        df = pd.read_csv(input_csv, encoding="utf-8-sig")
        print(f"讀入既有 CSV：{len(df)} 行")
        print(df[["city", "religion", "lat", "lng", "social_total"]].head(10).to_string(index=False))
    except FileNotFoundError:
        print(f"找不到 {input_csv}，改為示範 transform() 呼叫方式：")
        print("""
  raw = {
      "臺北市宗教社會服務概況": tp_social_df,   # 從 data.taipei API 取得
      "新北市寺廟資料":         ntpc_temples_df, # 從 data.taipei API 取得
  }
  result = transform(raw, data_time="2026-04-28T00:00:00+00:00")
  result.to_csv("component_6_religion_final.csv", index=False, encoding="utf-8-sig")
        """)
        sys.exit(0)