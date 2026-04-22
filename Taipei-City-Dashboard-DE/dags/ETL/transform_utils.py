"""
transform_utils.py
==================
共用工具函式庫，供 transforms/ 模組使用。
對齊官方 Taipei City Dashboard 規範：
  - wkb_geometry 欄位（非 geometry）
  - 帶有時區的 data_time 格式
  - 移除 _id 等系統欄位
"""

import re
import pytz
import requests
import pandas as pd
from datetime import datetime

# ── 常數 ─────────────────────────────────────────────
TAIPEI_TZ = pytz.timezone("Asia/Taipei")

# 官方規定移除的系統欄位
_SYSTEM_COLS = {"_id", "_importdate", "geometry"}


# ── 時間處理 ──────────────────────────────────────────
def convert_str_to_time_format(series: pd.Series, from_format: str = None) -> pd.Series:
    """
    將字串時間轉換成帶時區的 datetime（對齊官方 convert_str_to_time_format）。
    支援：
      - 一般格式："2024-03-01 14:46:51"
      - 民國年（%TY）：from_format="%TY/%m/%d" → 自動換算西元年
    輸出格式：2024-02-15 16:40:54+08:00
    """
    def _parse_one(val):
        if pd.isna(val) or val == "":
            return None
        val = str(val).strip()

        # 處理民國年（%TY 佔位符）
        if from_format and "%TY" in from_format:
            try:
                match = re.match(r"(\d+)", val)
                if match:
                    roc_year = int(match.group(1))
                    ad_year = roc_year + 1911
                    val = re.sub(r"^\d+", str(ad_year), val)
                    fmt = from_format.replace("%TY", "%Y")
                    dt = datetime.strptime(val, fmt)
                    return TAIPEI_TZ.localize(dt)
            except Exception:
                return None

        # 常見格式自動解析
        for fmt in (
            "%Y-%m-%d %H:%M:%S",
            "%Y/%m/%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d",
            "%Y/%m/%d",
        ):
            try:
                dt = datetime.strptime(val, fmt)
                return TAIPEI_TZ.localize(dt)
            except ValueError:
                continue
        return None

    return series.apply(_parse_one)


def get_source_last_modified(page_id: str) -> str:
    """
    取得 data.taipei 資料集最後更新時間（PAGE_ID）。
    失敗時回傳當下台北時間。
    """
    if not page_id:
        return datetime.now(tz=TAIPEI_TZ).isoformat()
    try:
        url = f"https://data.taipei/api/frontstage/tpeod/dataset/{page_id}"
        resp = requests.get(url, timeout=10, verify=False)
        resp.raise_for_status()
        data = resp.json()
        t = (
            data.get("result", {}).get("lastModified")
            or data.get("lastModified")
            or data.get("result", {}).get("updatedAt")
        )
        if t:
            return t
    except Exception:
        pass
    return datetime.now(tz=TAIPEI_TZ).isoformat()


# ── 地空空間處理 ──────────────────────────────────────
def add_point_wkbgeometry_column_to_df(
    data: pd.DataFrame,
    x: pd.Series,
    y: pd.Series,
    from_crs: int = 4326,
):
    """
    對齊官方 add_point_wkbgeometry_column_to_df。
    將 x（經度）、y（緯度）合併為 Point，加入：
      - geometry     : shapely Point（CRS 轉換後 EPSG:4326）
      - wkb_geometry : WKB hex 格式（官方要求的 DB 儲存格式）
      - lng / lat    : 轉換後的 WGS84 座標

    注意：呼叫後請 drop(columns=["geometry"])，只保留 wkb_geometry 寫入 DB。
    """
    import geopandas as gpd  # 懶載入，避免未安裝時影響其他模組

    # 無效值轉 NaN
    x_f = pd.to_numeric(x, errors="coerce")
    y_f = pd.to_numeric(y, errors="coerce")

    gdf = gpd.GeoDataFrame(
        data.copy(),
        geometry=gpd.points_from_xy(x_f, y_f),
        crs=f"EPSG:{from_crs}",
    )

    # 若非 WGS84，轉換至 EPSG:4326
    if from_crs != 4326:
        gdf = gdf.to_crs(epsg=4326)

    # 加入 WKB hex 欄位（官方儲存格式）
    gdf["wkb_geometry"] = gdf["geometry"].apply(
        lambda geom: geom.wkb_hex if geom and not geom.is_empty else None
    )

    # 更新 lng/lat 為轉換後 WGS84 座標
    gdf["lng"] = gdf["geometry"].x
    gdf["lat"] = gdf["geometry"].y

    # 移除幾何無效的列
    gdf = gdf.dropna(subset=["wkb_geometry"])

    return gdf


# ── 通用清洗 ──────────────────────────────────────────
def transform_single(
    df: pd.DataFrame,
    data_time: str,
    config: dict,
) -> pd.DataFrame:
    """
    通用資料清洗流程（無客製化 transforms/{dag_id}.py 時的 fallback）。

    步驟：
      1. 加入 data_time（帶時區）
      2. 移除系統欄位（_id, _importdate, geometry）
      3. 若有 lng/lat 欄位 → 產生 wkb_geometry、移除 geometry
      4. 套用 keep_cols 篩選（自動保護 data_time / wkb_geometry）
    """
    data = df.copy()

    # 1. data_time（帶時區）
    dt_series = pd.Series([data_time] * len(data))
    data["data_time"] = convert_str_to_time_format(dt_series)

    # 2. 移除系統欄位
    drop_cols = [c for c in data.columns if c in _SYSTEM_COLS]
    data = data.drop(columns=drop_cols, errors="ignore")

    # 3. 座標欄位 → wkb_geometry
    lng_col = _find_col(data, ["lng", "longitude", "x", "經度", "lon"])
    lat_col = _find_col(data, ["lat", "latitude", "y", "緯度"])

    if lng_col and lat_col:
        from_crs = config.get("from_crs", 4326)
        gdf = add_point_wkbgeometry_column_to_df(
            data, x=data[lng_col], y=data[lat_col], from_crs=from_crs
        )
        # 官方警告：geometry 與 wkb_geometry 只能保留其中一個
        gdf = gdf.drop(columns=["geometry"], errors="ignore")
        data = pd.DataFrame(gdf)

    # 4. keep_cols 篩選（保護必要欄位）
    keep = config.get("keep_cols", [])
    if keep:
        must_keep = ["data_time"]
        if "wkb_geometry" in data.columns:
            must_keep.append("wkb_geometry")
        keep_final = must_keep + [
            c for c in keep if c in data.columns and c not in must_keep
        ]
        data = data[keep_final]

    return data.reset_index(drop=True)


# ── 輔助函式 ──────────────────────────────────────────
def _find_col(df: pd.DataFrame, candidates: list) -> str | None:
    """從候選清單找出 DataFrame 實際存在的欄位名（不分大小寫）。"""
    lower_map = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in lower_map:
            return lower_map[cand.lower()]
    return None
