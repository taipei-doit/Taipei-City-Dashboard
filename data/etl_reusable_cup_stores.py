"""
ETL: 循環杯服務門市 → reusable_cup_stores (dashboard DB)

Geocoding: Mapbox Geocoding API v5 (WGS84 output)
Target DB: postgres-data container (hostname: postgres-data:5432)
"""

import time
import os
import requests
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from sqlalchemy import create_engine, text
from geoalchemy2 import Geometry

# ── 設定 ──────────────────────────────────────────────────────────────────────
MAPBOX_TOKEN = os.environ.get("MAPBOX_TOKEN")
ODS_PATH = "/data/提供循環杯服務之業者門市清單_20260502133217.ods"
CHECKPOINT_PATH = "/data/reusable_cup_geocoded_checkpoint.csv"
TARGET_CITIES = {"臺北市", "新北市"}

# DB 連線資訊 (優先讀取環境變數)
DB_USER = os.environ.get("DB_DASHBOARD_USER", "postgres")
DB_PASS = os.environ.get("DB_DASHBOARD_PASSWORD", "postgres")
DB_HOST = os.environ.get("DB_DASHBOARD_HOST", "postgres-data")
DB_PORT = os.environ.get("DB_DASHBOARD_PORT", "5432")
DB_NAME = os.environ.get("DB_DASHBOARD_DBNAME", "dashboard")

DB_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
TABLE_NAME = "reusable_cup_stores"

# ── Geocoding ─────────────────────────────────────────────────────────────────

def geocode_address(address: str, retries: int = 3) -> tuple:
    """呼叫 Mapbox v5 forward geocoding，回傳 (lng, lat) 或 (None, None)。"""
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{requests.utils.quote(address)}.json"
    params = {
        "access_token": MAPBOX_TOKEN,
        "language": "zh",
        "country": "TW",
        "limit": 1,
    }
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            features = resp.json().get("features", [])
            if features:
                lng, lat = features[0]["center"]
                return lng, lat
            return None, None
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f"  [FAIL] {address} → {e}")
                return None, None

def geocode_batch(df: pd.DataFrame) -> pd.DataFrame:
    """對整個 DataFrame 的 門市地址 欄位做 geocoding，支援斷點續傳。"""
    # 讀取 checkpoint
    if os.path.exists(CHECKPOINT_PATH):
        done = pd.read_csv(CHECKPOINT_PATH)
        done_set = set(done["門市地址"].tolist())
        print(f"[checkpoint] 已有 {len(done)} 筆，繼續剩餘的部分。")
    else:
        done = pd.DataFrame()
        done_set = set()

    remaining = df[~df["門市地址"].isin(done_set)].copy()
    total = len(remaining)
    print(f"[geocode] 共需處理 {total} 筆（已完成 {len(done_set)} 筆）")

    results = []
    for i, (_, row) in enumerate(remaining.iterrows()):
        addr = row["門市地址"]
        lng, lat = geocode_address(addr)
        results.append({**row.to_dict(), "lng": lng, "lat": lat})

        if (i + 1) % 50 == 0 or (i + 1) == total:
            batch_df = pd.DataFrame(results)
            combined = pd.concat([done, batch_df], ignore_index=True)
            combined.to_csv(CHECKPOINT_PATH, index=False)
            success = batch_df[batch_df["lng"].notna()].shape[0]
            print(f"  [{i+1}/{total}] 成功 {success}/{len(results)} 筆，已存 checkpoint")
            done = combined
            results = []

        # Mapbox free tier: ≤600 req/min → 每 10 筆暫停 1 秒
        if (i + 1) % 10 == 0:
            time.sleep(1)

    return done

# ── 建立 GeoDataFrame ─────────────────────────────────────────────────────────

def build_geodataframe(df: pd.DataFrame) -> gpd.GeoDataFrame:
    df = df.dropna(subset=["lng", "lat"]).copy()
    df["lng"] = pd.to_numeric(df["lng"], errors="coerce")
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df = df.dropna(subset=["lng", "lat"])

    geometry = [Point(r.lng, r.lat) for _, r in df.iterrows()]
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")

    # 轉成 WKB (hex) 供 geoalchemy2 使用
    gdf["wkb_geometry"] = gdf["geometry"].apply(lambda g: g.wkb_hex)
    gdf = gdf.drop(columns=["geometry"])
    return gdf

# ── 寫入 DB ───────────────────────────────────────────────────────────────────

CREATE_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS public.{TABLE_NAME} (
    brand        VARCHAR(100),
    city         VARCHAR(50),
    store_name   VARCHAR(200),
    address      VARCHAR(300),
    phone        VARCHAR(50),
    lng          FLOAT,
    lat          FLOAT,
    wkb_geometry geometry(Point, 4326)
);
"""

def write_to_db(gdf: gpd.GeoDataFrame, engine):
    with engine.begin() as conn:
        conn.execute(text(CREATE_TABLE_SQL))
        conn.execute(text(f"TRUNCATE TABLE public.{TABLE_NAME}"))

    cols = ["brand", "city", "store_name", "address", "phone", "lng", "lat", "wkb_geometry"]
    out = gdf.rename(columns={
        "連鎖品牌": "brand",
        "縣市別":   "city",
        "門市名稱": "store_name",
        "門市地址": "address",
        "門市電話": "phone",
    })[cols]

    with engine.begin() as conn:
        out.to_sql(
            TABLE_NAME, conn,
            if_exists="append", index=False, schema="public",
            dtype={"wkb_geometry": Geometry("Point", srid=4326)},
        )
    print(f"[DB] 寫入 {len(out)} 筆到 public.{TABLE_NAME}")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=== Step 1: 讀取 ODS ===")
    df = pd.read_excel(ODS_PATH, engine="odf")
    df = df[df["縣市別"].isin(TARGET_CITIES)].reset_index(drop=True)
    print(f"  雙北門市共 {len(df)} 筆")
    print(df["縣市別"].value_counts().to_string())

    print("\n=== Step 2: Geocoding (Mapbox API) ===")
    geocoded = geocode_batch(df)

    success_count = geocoded["lng"].notna().sum()
    print(f"\n[結果] 成功 geocoding: {success_count}/{len(geocoded)} 筆")
    fail_count = geocoded["lng"].isna().sum()
    if fail_count > 0:
        print(f"[警告] 無法取得座標: {fail_count} 筆（已跳過）")

    print("\n=== Step 3: 建立 GeoDataFrame ===")
    gdf = build_geodataframe(geocoded)
    print(f"  最終有效資料: {len(gdf)} 筆")

    print("\n=== Step 4: 寫入資料庫 ===")
    engine = create_engine(DB_URL)
    write_to_db(gdf, engine)

    print("\n=== 完成 ===")
    # 清除 checkpoint
    if os.path.exists(CHECKPOINT_PATH):
        os.remove(CHECKPOINT_PATH)
        print("[checkpoint] 已清除暫存檔")

if __name__ == "__main__":
    main()
