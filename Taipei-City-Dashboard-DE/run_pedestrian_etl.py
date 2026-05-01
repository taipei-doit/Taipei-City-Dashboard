"""
Standalone ETL runner for pedestrian accident dashboard.
Runs all 4 ETL pipelines WITHOUT Airflow.

Prerequisites:
  pip install pandas requests geopandas sqlalchemy psycopg2-binary geoalchemy2 shapely

Usage A – from host machine (postgres-data exposed on 5433):
  cd Taipei-City-Dashboard-DE
  python run_pedestrian_etl.py [--step taipei|ntpc|hotspot|trend|all]

Usage B – inside Docker container (on br_dashboard network):
  docker run --rm -it --network br_dashboard \
    -v "$PWD/../Taipei-City-Dashboard-DE:/etl" \
    -v "$PWD/../docker:/docker_env" \
    -w /etl python:3.12-slim bash -c \
    "pip install -q pandas requests geopandas sqlalchemy psycopg2-binary geoalchemy2 shapely && \
     DB_HOST=postgres-data DB_PORT=5432 python run_pedestrian_etl.py --step taipei"

Environment variable overrides (highest priority):
  DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
"""

import argparse
import io
import os
import re
import sys
import zipfile
from pathlib import Path

import pandas as pd
import requests
from sqlalchemy import create_engine, text


# ---------------------------------------------------------------------------
# 1. Config helpers
# ---------------------------------------------------------------------------

def load_env(env_path: Path) -> dict:
    env = {}
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, _, v = line.partition("=")
                v = v.split("#")[0].strip()
                env[k.strip()] = v
    return env


def get_db_uri(env: dict) -> str:
    # Env-var overrides take highest priority (useful when running in Docker)
    host   = os.environ.get("DB_HOST")   or env.get("DB_DASHBOARD_HOST", "localhost")
    port   = os.environ.get("DB_PORT")   or "5432"
    user   = os.environ.get("DB_USER")   or env.get("DB_DASHBOARD_USER", "postgres")
    pw     = os.environ.get("DB_PASSWORD") or env.get("DB_DASHBOARD_PASSWORD", "")
    dbname = os.environ.get("DB_NAME")   or env.get("DB_DASHBOARD_DBNAME", "dashboard")
    # When running from host, use localhost:5433 (postgres-data mapped port)
    if host in ("localhost", "127.0.0.1") and not os.environ.get("DB_PORT"):
        port = "5433"
    return f"postgresql://{user}:{pw}@{host}:{port}/{dbname}"


# ---------------------------------------------------------------------------
# 2. Table creation
# ---------------------------------------------------------------------------

CREATE_TABLES_SQL = """
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS public.traffic_pedestrian_accident_taipei (
    id SERIAL PRIMARY KEY,
    data_time TIMESTAMP WITH TIME ZONE,
    year INTEGER,
    month INTEGER,
    hour INTEGER,
    district VARCHAR(30),
    location TEXT,
    death_count INTEGER DEFAULT 0,
    injury_count INTEGER DEFAULT 0,
    age INTEGER,
    cause_code VARCHAR(20),
    cause_name VARCHAR(100),
    lng DOUBLE PRECISION,
    lat DOUBLE PRECISION,
    wkb_geometry geometry(Point, 4326)
);
CREATE INDEX IF NOT EXISTS idx_ped_acc_tpe_year ON public.traffic_pedestrian_accident_taipei(year);
CREATE INDEX IF NOT EXISTS idx_ped_acc_tpe_geom ON public.traffic_pedestrian_accident_taipei USING GIST(wkb_geometry);

CREATE TABLE IF NOT EXISTS public.traffic_pedestrian_accident_ntpc (
    id SERIAL PRIMARY KEY,
    data_time TIMESTAMP WITH TIME ZONE,
    year INTEGER,
    month INTEGER,
    hour INTEGER,
    death_count INTEGER DEFAULT 0,
    injury_count INTEGER DEFAULT 0,
    age INTEGER,
    cause_name VARCHAR(200),
    pedestrian_action VARCHAR(100),
    lng DOUBLE PRECISION,
    lat DOUBLE PRECISION,
    wkb_geometry geometry(Point, 4326)
);
CREATE INDEX IF NOT EXISTS idx_ped_acc_ntpc_year ON public.traffic_pedestrian_accident_ntpc(year);
CREATE INDEX IF NOT EXISTS idx_ped_acc_ntpc_geom ON public.traffic_pedestrian_accident_ntpc USING GIST(wkb_geometry);

CREATE TABLE IF NOT EXISTS public.traffic_pedestrian_hotspot (
    id SERIAL PRIMARY KEY,
    data_time TIMESTAMP WITH TIME ZONE,
    city VARCHAR(20),
    h3_index VARCHAR(20),
    center_lng DOUBLE PRECISION,
    center_lat DOUBLE PRECISION,
    accident_count INTEGER,
    death_count INTEGER,
    injury_count INTEGER,
    top_cause VARCHAR(200),
    top_hour INTEGER,
    near_location VARCHAR(200),
    wkb_geometry geometry(Point, 4326)
);
CREATE INDEX IF NOT EXISTS idx_ped_hotspot_geom ON public.traffic_pedestrian_hotspot USING GIST(wkb_geometry);

CREATE TABLE IF NOT EXISTS public.traffic_pedestrian_yearly_trend (
    id SERIAL PRIMARY KEY,
    data_time TIMESTAMP WITH TIME ZONE,
    city VARCHAR(20),
    year INTEGER,
    accident_count INTEGER,
    death_count INTEGER,
    injury_count INTEGER
);
"""

CAUSE_MAP = {
    "A1": "未依規定讓行人優先通行",
    "A2": "行人未依規定行走行人穿越道",
    "A3": "未注意車前狀況",
    "A4": "右轉彎未先禮讓行人",
    "A5": "酒後駕車",
    "B1": "未保持安全距離",
    "C1": "未遵守號誌",
}


# ---------------------------------------------------------------------------
# 3. Geometry helper (no Airflow utils dependency)
# ---------------------------------------------------------------------------

def add_wkb_geometry(df: pd.DataFrame, lng_col="lng", lat_col="lat"):
    """Add wkb_geometry column as WKTElement for PostGIS Point insertion."""
    from geoalchemy2 import WKTElement
    from shapely.geometry import Point

    def make_wkb(row):
        lng, lat = row[lng_col], row[lat_col]
        if pd.isna(lng) or pd.isna(lat):
            return None
        return WKTElement(Point(lng, lat).wkt, srid=4326)

    df["wkb_geometry"] = df.apply(make_wkb, axis=1)
    return df


# ---------------------------------------------------------------------------
# 4. ETL: Taipei pedestrian accidents
# ---------------------------------------------------------------------------

YEAR_RIDS = {
    2025: "83d6d29c-6801-41a2-95c6-47d551646db3",
    2024: "1a08afea-6b2e-4c07-a7a2-17dfba7541f5",
    2023: "abf81068-1bb7-414f-868e-29dffd7561bf",
    2022: "2b92f718-bc87-4260-9b38-68d48bf01658",
}
BASE_DOWNLOAD_URL = (
    "https://data.taipei/api/frontstage/tpeod/dataset/resource.download?rid={rid}"
)


def run_taipei_etl(engine):
    """台北市 2022-2025 歷史資料：改用 NPA 警政署年度封存資料集（與新北同源），確保計算基準一致。"""
    print("\n=== ETL: 台北市行人事故（NPA 年度封存，與新北同源）===")

    all_dfs = []
    for ce_year, url in NTPC_YEAR_URLS.items():
        print(f"  Downloading {ce_year}...")
        try:
            resp = requests.get(url, timeout=300)
            resp.raise_for_status()
        except Exception as e:
            print(f"    Failed: {e}")
            continue
        try:
            z = zipfile.ZipFile(io.BytesIO(resp.content))
            csv_files = [f for f in z.namelist() if f.lower().endswith(".csv")]
            for csv_f in csv_files:
                for enc in ("utf-8-sig", "big5", "cp950", "utf-8"):
                    try:
                        df_part = pd.read_csv(z.open(csv_f), encoding=enc, low_memory=False)
                        df_part["_ce_year"] = ce_year
                        all_dfs.append(df_part)
                        print(f"    {csv_f}: {len(df_part)} rows")
                        break
                    except (UnicodeDecodeError, Exception):
                        continue
        except zipfile.BadZipFile:
            for enc in ("utf-8-sig", "big5", "utf-8"):
                try:
                    df_part = pd.read_csv(io.StringIO(resp.content.decode(enc)), low_memory=False)
                    df_part["_ce_year"] = ce_year
                    all_dfs.append(df_part)
                    break
                except Exception:
                    continue

    if not all_dfs:
        print("  No data downloaded. Skipping.")
        return

    raw = pd.concat(all_dfs, ignore_index=True)
    print(f"Total rows across all years: {len(raw)}")

    city_col = next((c for c in raw.columns if "警局層" in c or "處理單位" in c), None)
    if city_col:
        data = raw[raw[city_col].str.contains("臺北市|台北市", na=False)].copy()
    else:
        data = raw.copy()

    ped_col = next((c for c in data.columns if "行動狀態大類" in c), None)
    if ped_col:
        data = data[data[ped_col].str.contains("人的狀態|行人", na=False)].copy()

    print(f"Taipei pedestrian rows: {len(data)}")

    time_col = next((c for c in data.columns if "發生時間" in c), None)
    data["hour"] = (
        (pd.to_numeric(data[time_col], errors="coerce").fillna(0) // 10000)
        .clip(0, 23).astype(int) if time_col else 0
    )
    data["year"] = data["_ce_year"].astype(int)
    month_col = next((c for c in data.columns if "發生月份" in c), None)
    data["month"] = pd.to_numeric(data[month_col], errors="coerce").fillna(0).astype(int) if month_col else 0

    casualty_col = next((c for c in data.columns if "死亡受傷" in c), None)
    if casualty_col:
        data["death_count"] = data[casualty_col].astype(str).str.extract(r"(\d+)死")[0].fillna(0).astype(int)
        data["injury_count"] = data[casualty_col].astype(str).str.extract(r"(\d+)傷")[0].fillna(0).astype(int)
    else:
        data["death_count"] = 0
        data["injury_count"] = 0

    age_col = next((c for c in data.columns if "年齡" in c), None)
    cause_col = next((c for c in data.columns if "肇因" in c and "個別" in c), None)
    data["age"] = pd.to_numeric(data[age_col], errors="coerce").fillna(0).astype(int) if age_col else 0
    data["cause_name"] = data[cause_col].fillna("其他") if cause_col else "其他"
    data["cause_code"] = ""
    data["district"] = ""
    data["location"] = ""

    lng_col = next((c for c in data.columns if "經度" in c), None)
    lat_col = next((c for c in data.columns if "緯度" in c), None)
    data["lng"] = pd.to_numeric(data[lng_col], errors="coerce") if lng_col else None
    data["lat"] = pd.to_numeric(data[lat_col], errors="coerce") if lat_col else None

    data = data[
        data["lng"].notna() & data["lat"].notna() &
        data["lng"].between(121.4, 121.8) &
        data["lat"].between(24.9, 25.25)
    ].copy()
    print(f"After coordinate filter: {len(data)}")

    data["data_time"] = pd.Timestamp.now(tz="Asia/Taipei")
    data = add_wkb_geometry(data)

    cols = ["data_time", "year", "month", "hour", "district", "location",
            "death_count", "injury_count", "age", "cause_code", "cause_name", "lng", "lat"]
    present = [c for c in cols if c in data.columns]
    ready = data[present + ["wkb_geometry"]]

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE public.traffic_pedestrian_accident_taipei RESTART IDENTITY"))

    from geoalchemy2 import Geometry
    ready.to_sql(
        "traffic_pedestrian_accident_taipei",
        engine,
        if_exists="append",
        index=False,
        dtype={"wkb_geometry": Geometry("POINT", srid=4326)},
        method="multi",
        chunksize=500,
    )
    print(f"Loaded {len(ready)} rows into traffic_pedestrian_accident_taipei")


# ---------------------------------------------------------------------------
# 5. ETL: New Taipei pedestrian accidents
# ---------------------------------------------------------------------------

# 警政署每年封存的傷亡道路交通事故資料（全國，含新北市）
# ROC 111-114 年 → CE 2022-2025
NTPC_YEAR_URLS = {
    2022: "https://opdadm.moi.gov.tw/api/v1/no-auth/resource/api/dataset/E52FB959-55BD-4D31-892C-21C87041FC87/resource/28128A43-4F80-4670-8F61-30F959477218/download",
    2023: "https://opdadm.moi.gov.tw/api/v1/no-auth/resource/api/dataset/E68DFD97-92B3-4A78-A447-87F1390B54B0/resource/C0876EEB-9468-4B23-8E67-AB57E3563A1B/download",
    2024: "https://opdadm.moi.gov.tw/api/v1/no-auth/resource/api/dataset/CCAD7AA8-5139-4066-8BE3-D6CC3154C137/resource/36C1D864-51F8-4A78-9D68-8298E00B0732/download",
    2025: "https://opdadm.moi.gov.tw/api/v1/no-auth/resource/api/dataset/FCD9C2D4-CB71-4EAA-AA4C-B088E5FE3157/resource/90BFBDAC-BA7E-4255-B557-EED2ED77AA93/download",
}


def run_ntpc_etl(engine):
    print("\n=== ETL: 新北市行人事故（年度封存資料集）===")

    all_dfs = []
    for ce_year, url in NTPC_YEAR_URLS.items():
        print(f"  Downloading {ce_year}...")
        try:
            resp = requests.get(url, timeout=300)
            resp.raise_for_status()
        except Exception as e:
            print(f"    Failed: {e}")
            continue

        try:
            z = zipfile.ZipFile(io.BytesIO(resp.content))
            csv_files = [f for f in z.namelist() if f.lower().endswith(".csv")]
            for csv_f in csv_files:
                for enc in ("utf-8-sig", "big5", "cp950", "utf-8"):
                    try:
                        df_part = pd.read_csv(z.open(csv_f), encoding=enc, low_memory=False)
                        df_part["_ce_year"] = ce_year
                        all_dfs.append(df_part)
                        print(f"    {csv_f}: {len(df_part)} rows")
                        break
                    except (UnicodeDecodeError, Exception):
                        continue
        except zipfile.BadZipFile:
            for enc in ("utf-8-sig", "big5", "utf-8"):
                try:
                    df_part = pd.read_csv(io.StringIO(resp.content.decode(enc)), low_memory=False)
                    df_part["_ce_year"] = ce_year
                    all_dfs.append(df_part)
                    break
                except Exception:
                    continue

    if not all_dfs:
        print("  No data downloaded. Skipping.")
        return

    raw = pd.concat(all_dfs, ignore_index=True)
    print(f"Total rows across all years: {len(raw)}")

    city_col = next((c for c in raw.columns if "警局層" in c or "處理單位" in c), None)
    if city_col:
        data = raw[raw[city_col].str.contains("新北市", na=False)].copy()
    else:
        data = raw.copy()

    ped_col = next((c for c in data.columns if "行動狀態大類" in c), None)
    if ped_col:
        data = data[data[ped_col].str.contains("人的狀態|行人", na=False)].copy()

    print(f"NTPC pedestrian rows: {len(data)}")

    time_col = next((c for c in data.columns if "發生時間" in c), None)
    data["hour"] = (
        (pd.to_numeric(data[time_col], errors="coerce").fillna(0) // 10000)
        .clip(0, 23).astype(int) if time_col else 0
    )

    # 直接用 URL 對應的西元年，不依賴 CSV 的民國年欄位
    data["year"] = data["_ce_year"].astype(int)
    month_col = next((c for c in data.columns if "發生月份" in c), None)
    data["month"] = pd.to_numeric(data[month_col], errors="coerce").fillna(0).astype(int) if month_col else 0

    casualty_col = next((c for c in data.columns if "死亡受傷" in c), None)
    if casualty_col:
        data["death_count"] = data[casualty_col].astype(str).str.extract(r"(\d+)死")[0].fillna(0).astype(int)
        data["injury_count"] = data[casualty_col].astype(str).str.extract(r"(\d+)傷")[0].fillna(0).astype(int)
    else:
        data["death_count"] = 0
        data["injury_count"] = 0

    age_col = next((c for c in data.columns if "年齡" in c), None)
    cause_col = next((c for c in data.columns if "肇因" in c and "個別" in c), None)
    ped_sub_col = next((c for c in data.columns if "行動狀態子" in c), None)

    data["age"] = pd.to_numeric(data[age_col], errors="coerce").fillna(0).astype(int) if age_col else 0
    data["cause_name"] = data[cause_col].fillna("其他") if cause_col else "其他"
    data["pedestrian_action"] = data[ped_sub_col].fillna("") if ped_sub_col else ""

    lng_col = next((c for c in data.columns if "經度" in c), None)
    lat_col = next((c for c in data.columns if "緯度" in c), None)
    data["lng"] = pd.to_numeric(data[lng_col], errors="coerce") if lng_col else None
    data["lat"] = pd.to_numeric(data[lat_col], errors="coerce") if lat_col else None

    data = data[
        data["lng"].notna() & data["lat"].notna() &
        data["lng"].between(121.3, 122.0) &
        data["lat"].between(24.8, 25.3)
    ].copy()
    data = data[
        ~(data["lng"].between(121.455, 121.475) & data["lat"].between(25.005, 25.020))
    ]
    print(f"After coordinate filter: {len(data)}")

    data["data_time"] = pd.Timestamp.now(tz="Asia/Taipei")
    data = add_wkb_geometry(data)

    ready = data[["data_time", "year", "month", "hour", "death_count", "injury_count",
                  "age", "cause_name", "pedestrian_action", "lng", "lat", "wkb_geometry"]]

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE public.traffic_pedestrian_accident_ntpc RESTART IDENTITY"))

    from geoalchemy2 import Geometry
    ready.to_sql(
        "traffic_pedestrian_accident_ntpc",
        engine,
        if_exists="append",
        index=False,
        dtype={"wkb_geometry": Geometry("POINT", srid=4326)},
        method="multi",
        chunksize=500,
    )
    print(f"Loaded {len(ready)} rows into traffic_pedestrian_accident_ntpc")


# ---------------------------------------------------------------------------
# 6. ETL: Hotspot aggregation
# ---------------------------------------------------------------------------

def run_hotspot_etl(engine):
    print("\n=== ETL: 行人事故熱點 ===")
    current_year = pd.Timestamp.now().year
    three_years_ago = current_year - 3

    tpe_sql = text(f"""
        SELECT
            'taipei' AS city,
            ROUND(lng::numeric, 3)::float AS center_lng,
            ROUND(lat::numeric, 3)::float AS center_lat,
            COUNT(*) AS accident_count,
            SUM(death_count) AS death_count,
            SUM(injury_count) AS injury_count,
            MODE() WITHIN GROUP (ORDER BY cause_name) AS top_cause,
            MODE() WITHIN GROUP (ORDER BY hour) AS top_hour
        FROM traffic_pedestrian_accident_taipei
        WHERE year >= {three_years_ago}
            AND lng IS NOT NULL AND lat IS NOT NULL
        GROUP BY center_lng, center_lat
        HAVING COUNT(*) >= 2
        ORDER BY accident_count DESC
        LIMIT 500
    """)

    ntpc_sql = text(f"""
        SELECT
            'ntpc' AS city,
            ROUND(lng::numeric, 3)::float AS center_lng,
            ROUND(lat::numeric, 3)::float AS center_lat,
            COUNT(*) AS accident_count,
            SUM(death_count) AS death_count,
            SUM(injury_count) AS injury_count,
            MODE() WITHIN GROUP (ORDER BY cause_name) AS top_cause,
            MODE() WITHIN GROUP (ORDER BY hour) AS top_hour
        FROM traffic_pedestrian_accident_ntpc
        WHERE year >= {three_years_ago}
            AND lng IS NOT NULL AND lat IS NOT NULL
        GROUP BY center_lng, center_lat
        HAVING COUNT(*) >= 2
        ORDER BY accident_count DESC
        LIMIT 500
    """)

    with engine.connect() as conn:
        try:
            tpe_df = pd.read_sql(tpe_sql, conn)
        except Exception as e:
            print(f"  taipei query failed: {e}")
            tpe_df = pd.DataFrame()
        try:
            ntpc_df = pd.read_sql(ntpc_sql, conn)
        except Exception as e:
            print(f"  ntpc query failed: {e}")
            ntpc_df = pd.DataFrame()

    data = pd.concat([tpe_df, ntpc_df], ignore_index=True)
    if data.empty:
        print("  No hotspot data (run taipei/ntpc ETL first)")
        return

    data["near_location"] = ""
    data["h3_index"] = ""
    data["data_time"] = pd.Timestamp.now(tz="Asia/Taipei")
    data = add_wkb_geometry(data, lng_col="center_lng", lat_col="center_lat")

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE public.traffic_pedestrian_hotspot RESTART IDENTITY"))

    from geoalchemy2 import Geometry
    data[["data_time", "city", "h3_index", "center_lng", "center_lat",
          "accident_count", "death_count", "injury_count",
          "top_cause", "top_hour", "near_location", "wkb_geometry"]].to_sql(
        "traffic_pedestrian_hotspot",
        engine,
        if_exists="append",
        index=False,
        dtype={"wkb_geometry": Geometry("POINT", srid=4326)},
        method="multi",
        chunksize=500,
    )
    print(f"Loaded {len(data)} hotspot rows")


# ---------------------------------------------------------------------------
# 7. ETL: Yearly trend
# ---------------------------------------------------------------------------

def run_trend_etl(engine):
    print("\n=== ETL: 年度趨勢 ===")

    tpe_sql = text("""
        SELECT 'taipei' AS city, year,
               COUNT(*) AS accident_count,
               SUM(death_count) AS death_count,
               SUM(injury_count) AS injury_count
        FROM traffic_pedestrian_accident_taipei
        WHERE year > 0
        GROUP BY year ORDER BY year
    """)
    ntpc_sql = text("""
        SELECT 'ntpc' AS city, year,
               COUNT(*) AS accident_count,
               SUM(death_count) AS death_count,
               SUM(injury_count) AS injury_count
        FROM traffic_pedestrian_accident_ntpc
        WHERE year > 0
        GROUP BY year ORDER BY year
    """)

    with engine.connect() as conn:
        try:
            tpe_df = pd.read_sql(tpe_sql, conn)
        except Exception as e:
            print(f"  taipei trend failed: {e}")
            tpe_df = pd.DataFrame()
        try:
            ntpc_df = pd.read_sql(ntpc_sql, conn)
        except Exception as e:
            print(f"  ntpc trend failed: {e}")
            ntpc_df = pd.DataFrame()

    data = pd.concat([tpe_df, ntpc_df], ignore_index=True)
    if data.empty:
        print("  No trend data (run taipei/ntpc ETL first)")
        return

    data["data_time"] = pd.Timestamp.now(tz="Asia/Taipei")
    data[["data_time", "city", "year", "accident_count", "death_count", "injury_count"]].to_sql(
        "traffic_pedestrian_yearly_trend",
        engine,
        if_exists="replace",
        index=False,
        method="multi",
    )
    print(f"Loaded {len(data)} trend rows")


# ---------------------------------------------------------------------------
# 8. ETL: 2026 current-year real-time (A1 + A2, both cities)
# ---------------------------------------------------------------------------

# A1 即時：https://data.gov.tw/dataset/12818
# A2 即時：https://data.gov.tw/dataset/13139
REALTIME_URLS = {
    "A1": "https://opdadm.moi.gov.tw/api/v1/no-auth/resource/api/dataset/02D40248-7CAA-4354-82EA-E27AB8DCAB39/resource/57DB8A87-7DFE-4361-8E6A-267F52AF394C/download",
    "A2_API": "https://data.gov.tw/api/v2/rest/dataset/13139?page=0&size=5&format=json",
}
CURRENT_YEAR = pd.Timestamp.now().year


def _download_zip_csvs(url: str, label: str, ce_year: int) -> list:
    """Download a ZIP and return list of DataFrames (all CSV files), tagged with _ce_year."""
    dfs = []
    try:
        resp = requests.get(url, timeout=300)
        resp.raise_for_status()
    except Exception as e:
        print(f"  [{label}] download failed: {e}")
        return dfs

    try:
        z = zipfile.ZipFile(io.BytesIO(resp.content))
        csv_files = [f for f in z.namelist() if f.lower().endswith(".csv")]
        for csv_f in csv_files:
            for enc in ("utf-8-sig", "big5", "cp950", "utf-8"):
                try:
                    df = pd.read_csv(z.open(csv_f), encoding=enc, low_memory=False)
                    df["_ce_year"] = ce_year
                    dfs.append(df)
                    print(f"    {csv_f}: {len(df)} rows")
                    break
                except (UnicodeDecodeError, Exception):
                    continue
    except zipfile.BadZipFile:
        for enc in ("utf-8-sig", "big5", "utf-8"):
            try:
                df = pd.read_csv(io.StringIO(resp.content.decode(enc)), low_memory=False)
                df["_ce_year"] = ce_year
                dfs.append(df)
                break
            except Exception:
                continue
    return dfs


def _filter_pedestrians(raw: pd.DataFrame, city_kw: str) -> pd.DataFrame:
    """Filter to given city and pedestrian rows; parse coordinates and time."""
    city_col = next((c for c in raw.columns if "警局層" in c or "處理單位" in c), None)
    if city_col:
        data = raw[raw[city_col].str.contains(city_kw, na=False)].copy()
    else:
        data = raw.copy()

    ped_col = next((c for c in data.columns if "行動狀態大類" in c or "行動狀態" in c), None)
    if ped_col:
        data = data[data[ped_col].astype(str).str.contains("人的狀態|行人|^4", na=False)].copy()

    time_col = next((c for c in data.columns if "發生時間" in c), None)
    data["hour"] = (
        (pd.to_numeric(data[time_col], errors="coerce").fillna(0) // 10000)
        .clip(0, 23).astype(int) if time_col else 0
    )
    month_col = next((c for c in data.columns if "發生月" in c), None)
    data["month"] = pd.to_numeric(data[month_col], errors="coerce").fillna(0).astype(int) if month_col else 0
    data["year"] = data["_ce_year"].astype(int)

    casualty_col = next((c for c in data.columns if "死亡受傷" in c), None)
    if casualty_col:
        data["death_count"] = data[casualty_col].astype(str).str.extract(r"(\d+)死")[0].fillna(0).astype(int)
        data["injury_count"] = data[casualty_col].astype(str).str.extract(r"(\d+)傷")[0].fillna(0).astype(int)
    else:
        data["death_count"] = 0
        data["injury_count"] = 0

    lng_col = next((c for c in data.columns if "經度" in c or c.lower() in ["lng", "lon", "x"]), None)
    lat_col = next((c for c in data.columns if "緯度" in c or c.lower() in ["lat", "y"]), None)
    data["lng"] = pd.to_numeric(data[lng_col], errors="coerce") if lng_col else None
    data["lat"] = pd.to_numeric(data[lat_col], errors="coerce") if lat_col else None
    return data


def run_current_year_etl(engine):
    print(f"\n=== ETL: {CURRENT_YEAR} 即時資料（A1+A2，台北市＋新北市）===")

    # A1 即時
    print(f"  Downloading A1...")
    all_dfs = _download_zip_csvs(REALTIME_URLS["A1"], "A1", CURRENT_YEAR)

    # A2 即時（動態取 distribution URLs）
    print(f"  Fetching A2 URLs...")
    try:
        meta = requests.get(REALTIME_URLS["A2_API"], timeout=30).json()
        a2_urls = [d["resourceDownloadUrl"] for d in meta["result"]["distribution"] if d.get("resourceDownloadUrl")]
        print(f"  Found {len(a2_urls)} A2 ZIPs")
        for i, url in enumerate(a2_urls, 1):
            print(f"  Downloading A2 ZIP {i}/{len(a2_urls)}...")
            all_dfs.extend(_download_zip_csvs(url, f"A2-{i}", CURRENT_YEAR))
    except Exception as e:
        print(f"  A2 fetch failed: {e}")

    if not all_dfs:
        print("  No data. Skipping.")
        return

    raw = pd.concat(all_dfs, ignore_index=True)
    print(f"  Total rows: {len(raw)}")

    from geoalchemy2 import Geometry

    for city_kw, table, lng_range, lat_range in [
        ("臺北市|台北市", "traffic_pedestrian_accident_taipei", (121.4, 121.8), (24.9, 25.25)),
        ("新北市",        "traffic_pedestrian_accident_ntpc",   (121.3, 122.0), (24.8, 25.3)),
    ]:
        city_data = _filter_pedestrians(raw, city_kw)
        city_data = city_data[
            city_data["lng"].notna() & city_data["lat"].notna() &
            city_data["lng"].between(*lng_range) &
            city_data["lat"].between(*lat_range)
        ].copy()
        print(f"  {city_kw}: {len(city_data)} pedestrian rows with valid coords")

        if city_data.empty:
            continue

        city_data["data_time"] = pd.Timestamp.now(tz="Asia/Taipei")
        city_data = add_wkb_geometry(city_data)

        # 決定共同欄位
        shared_cols = ["data_time", "year", "month", "hour", "death_count", "injury_count", "lng", "lat", "wkb_geometry"]
        if table == "traffic_pedestrian_accident_taipei":
            age_col = next((c for c in city_data.columns if "年齡" in c), None)
            cause_col = next((c for c in city_data.columns if "肇因" in c and "個別" in c), None)
            city_data["age"] = pd.to_numeric(city_data[age_col], errors="coerce").fillna(0).astype(int) if age_col else 0
            city_data["cause_name"] = city_data[cause_col].fillna("其他") if cause_col else "其他"
            city_data["cause_code"] = ""
            city_data["district"] = ""
            city_data["location"] = ""
            cols = ["data_time", "year", "month", "hour", "district", "location",
                    "death_count", "injury_count", "age", "cause_code", "cause_name", "lng", "lat", "wkb_geometry"]
        else:
            age_col = next((c for c in city_data.columns if "年齡" in c), None)
            cause_col = next((c for c in city_data.columns if "肇因" in c and "個別" in c), None)
            ped_sub_col = next((c for c in city_data.columns if "行動狀態子" in c), None)
            city_data["age"] = pd.to_numeric(city_data[age_col], errors="coerce").fillna(0).astype(int) if age_col else 0
            city_data["cause_name"] = city_data[cause_col].fillna("其他") if cause_col else "其他"
            city_data["pedestrian_action"] = city_data[ped_sub_col].fillna("") if ped_sub_col else ""
            cols = ["data_time", "year", "month", "hour", "death_count", "injury_count",
                    "age", "cause_name", "pedestrian_action", "lng", "lat", "wkb_geometry"]

        ready = city_data[[c for c in cols if c in city_data.columns] + (["wkb_geometry"] if "wkb_geometry" not in cols else [])]

        with engine.begin() as conn:
            conn.execute(text(f"DELETE FROM public.{table} WHERE year = {CURRENT_YEAR}"))

        ready.to_sql(
            table, engine,
            if_exists="append", index=False,
            dtype={"wkb_geometry": Geometry("POINT", srid=4326)},
            method="multi", chunksize=500,
        )
        print(f"  Loaded {len(ready)} rows into {table} (year={CURRENT_YEAR})")


# ---------------------------------------------------------------------------
# 9. Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--step", choices=["taipei", "ntpc", "current", "hotspot", "trend", "all"],
        default="all", help="Which ETL step to run"
    )
    args = parser.parse_args()

    # Load .env if it exists, otherwise rely on environment variables
    script_dir = Path(__file__).resolve().parent
    env_path = script_dir.parent / "docker" / ".env"
    env = {}
    if env_path.exists():
        env = load_env(env_path)
    elif not os.environ.get("DB_HOST"):
        print(f"WARNING: .env not found at {env_path} and DB_HOST not set.")
        print("Set DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME env vars, or run from repo root.")

    db_uri = get_db_uri(env)
    safe_uri = re.sub(r":([^:@]+)@", ":***@", db_uri)
    print(f"Connecting to: {safe_uri}")

    engine = create_engine(db_uri)

    # Create tables
    print("\nCreating tables if not exist...")
    with engine.begin() as conn:
        for stmt in CREATE_TABLES_SQL.split(";"):
            stmt = stmt.strip()
            if stmt:
                try:
                    conn.execute(text(stmt))
                except Exception as e:
                    print(f"  Warning: {e}")
    print("Tables ready.")

    step = args.step
    if step in ("taipei", "all"):
        run_taipei_etl(engine)
    if step in ("ntpc", "all"):
        run_ntpc_etl(engine)
    if step in ("current", "all"):
        run_current_year_etl(engine)
    if step in ("hotspot", "all"):
        run_hotspot_etl(engine)
    if step in ("trend", "all"):
        run_trend_etl(engine)

    print("\nDone.")


if __name__ == "__main__":
    main()
