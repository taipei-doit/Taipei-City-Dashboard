#!/usr/bin/env python3
"""
Local ETL script for eco_cup data.
Run this directly without Airflow. Uses GeoPy for geocoding.

Usage:
    # Default: ArcGIS (free tier, no API key needed, better address parsing)
    python3 run_local_etl.py

    # Optional: Use TGOS API (fastest & most accurate for Taiwan addresses)
    export TPGOS_API_KEY="your_api_key_here"
    python3 run_local_etl.py

Install dependencies if needed:
    pip install pandas sqlalchemy psycopg2-binary geopy
"""

import os
import time
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

import pandas as pd
from geopy.geocoders import ArcGIS
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from sqlalchemy import create_engine, text

# ============================================================
# Config - Modify these if needed
# ============================================================
TPGOS_API_KEY = os.environ.get("TPGOS_API_KEY", "")
POSTGRES_URI = os.environ.get(
    "POSTGRES_URI",
    "postgresql://postgres:postgres@localhost:5433/dashboard"
)
# Auto-detect project root relative to this script
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_PATH = os.environ.get(
    "DATA_PATH",
    str(SCRIPT_DIR / ".." / ".." / ".." / "..")
)

# ============================================================
# Excel Parser (OOXML namespace workaround)
# ============================================================


def _parse_ooxml_excel(file_path: str) -> pd.DataFrame:
    ns = "http://purl.oclc.org/ooxml/spreadsheetml/main"
    with zipfile.ZipFile(file_path) as z:
        with z.open("xl/sharedStrings.xml") as f:
            ss_root = ET.fromstring(f.read())
        strings = []
        for si in ss_root.iter(f"{{{ns}}}si"):
            t = si.find(f".//{{{ns}}}t")
            strings.append(t.text if t is not None else "")

        with z.open("xl/worksheets/sheet1.xml") as f:
            ws_root = ET.fromstring(f.read())

        rows = []
        for row in ws_root.iter(f"{{{ns}}}row"):
            row_data = []
            for cell in row.iter(f"{{{ns}}}c"):
                v = cell.find(f"{{{ns}}}v")
                if v is not None:
                    if cell.get("t") == "s":
                        row_data.append(strings[int(v.text)])
                    else:
                        row_data.append(v.text)
                else:
                    row_data.append("")
            rows.append(row_data)

    return pd.DataFrame(rows[1:], columns=rows[0])


# ============================================================
# Geocoding with GeoPy
# ============================================================


def _geocode_with_arcgis(addrs):
    """Geocode addresses using ArcGIS World Geocoding Service.
    Free tier available without API key. Generally more forgiving
    with address formats than Nominatim. Rate limit: ~50 req/sec.
    """
    geolocator = ArcGIS(timeout=10)
    x = []
    y = []

    for i, addr in enumerate(addrs, 1):
        try:
            location = geolocator.geocode(addr)
            if location:
                print(f"  [{i}/{len(addrs)}] [OK] {addr[:40]}... -> {location.latitude:.5f}, {location.longitude:.5f}")
                x.append(location.longitude)
                y.append(location.latitude)
            else:
                print(f"  [{i}/{len(addrs)}] [NOT FOUND] {addr[:40]}...")
                x.append(None)
                y.append(None)
        except (GeocoderTimedOut, GeocoderUnavailable) as e:
            print(f"  [{i}/{len(addrs)}] [TIMEOUT] {addr[:40]}... -> {e}")
            x.append(None)
            y.append(None)
        # Small delay to be polite to the free tier
        time.sleep(0.2)

    return x, y


def _geocode_with_tgos(addrs):
    """Geocode addresses using TGOS API (Taiwan-specific, faster, more accurate).
    Requires TPGOS_API_KEY environment variable.
    """
    import concurrent.futures
    import requests
    from requests.adapters import HTTPAdapter

    url = "https://map.tpgos.gov.taipei/embed/webapi.cfm"

    def _get_single(addr):
        params = {
            "SERVICE": "KEYWORDSEARCH",
            "KEYWORD": addr,
            "APIKEY": TPGOS_API_KEY,
            "ITEM_LIST": "TPGOS_CA_ADDR:30,TGOS_V2_ADDR,GMAPI_ADDR",
            "SRS_T": "WGS84",
        }
        x = None
        y = None
        s = requests.Session()
        s.mount("http://", HTTPAdapter(max_retries=5))
        s.mount("https://", HTTPAdapter(max_retries=5))

        try:
            response = s.get(url, params=params, timeout=30)
            res_json = response.json()
            if len(res_json) > 0:
                if res_json[0]["QUERYTYPE"] == "完全比對":
                    print(f"  [OK] {addr}")
                    x = res_json[0]["X"]
                    y = res_json[0]["Y"]
                else:
                    print(f"  [PARTIAL] {addr}")
            else:
                print(f"  [NOT FOUND] {addr}")
        except Exception as e:
            print(f"  [ERROR] {addr} -> {e}")

        return x, y

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        results = pool.map(_get_single, addrs)
        x = []
        y = []
        for lon, lat in results:
            x.append(lon)
            y.append(lat)
        time.sleep(0.5)

    return x, y


# ============================================================
# Main ETL
# ============================================================


def main():
    # Choose geocoder
    if TPGOS_API_KEY:
        geocode_fn = _geocode_with_tgos
        geocoder_name = "TGOS"
        print("Using TGOS API for geocoding (fast, Taiwan-optimized)")
    else:
        geocode_fn = _geocode_with_arcgis
        geocoder_name = "ArcGIS"
        print("Using ArcGIS World Geocoding Service (free tier, no API key)")
        print("Note: ~1800 addresses will take ~6-10 minutes with polite delays.")
        print("Set TPGOS_API_KEY env var to use faster TGOS API instead.")

    print("=" * 60)
    print("Eco Cup ETL - Local Execution")
    print(f"DB: {POSTGRES_URI}")
    print(f"Data path: {DATA_PATH}")
    print(f"Geocoder: {geocoder_name}")
    print("=" * 60)

    # 1. Parse Excel files
    print("\n[1/5] Reading Excel files...")
    df_tpe = _parse_ooxml_excel(f"{DATA_PATH}/Taipei-City-Dashboard-DE/dags/utils/opendata/環保杯/環保杯_台北市.xlsx")
    df_ntpc = _parse_ooxml_excel(f"{DATA_PATH}/Taipei-City-Dashboard-DE/dags/utils/opendata/環保杯/環保杯_新北市.xlsx")
    raw_data = pd.concat([df_tpe, df_ntpc], ignore_index=True)
    
    print(f"      Total rows: {len(raw_data)}")

    # Rename columns
    raw_data = raw_data.rename(columns={
        "連鎖品牌": "brand",
        "縣市別": "city",
        "門市名稱": "store_name",
        "門市地址": "address",
        "門市電話": "phone",
    })

    # Extract district
    raw_data["district"] = raw_data["address"].str[3:6]

    # 2. Geocode
    print(f"\n[2/5] Geocoding addresses via {geocoder_name}...")
    clean_addr = raw_data["address"].str.replace(r"\(.*\)", "", regex=True)
    lon, lat = geocode_fn(clean_addr.tolist())
    raw_data["lon"] = pd.to_numeric(lon, errors="coerce")
    raw_data["lat"] = pd.to_numeric(lat, errors="coerce")

    # Drop rows without coordinates
    before_drop = len(raw_data)
    raw_data = raw_data.dropna(subset=["lon", "lat"]).copy()
    after_drop = len(raw_data)
    print(f"      Geocoded: {after_drop}/{before_drop} ({before_drop - after_drop} failed)")
    
    # Store geocoding results for debugging
    raw_data[["address", "lon", "lat"]].to_csv(f"{DATA_PATH}/geocoding_results.csv", index=False)

    # 3. Build ready data
    print("\n[3/5] Preparing data...")
    ready_data = pd.DataFrame({
        "brand": raw_data["brand"],
        "store_name": raw_data["store_name"],
        "address": raw_data["address"],
        "city": raw_data["city"],
        "district": raw_data["district"],
        "phone": raw_data["phone"],
        "lon": raw_data["lon"],
        "lat": raw_data["lat"],
        "data_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })

    # 4. Save to PostgreSQL
    # 4. Save to PostgreSQL
    print("\n[4/5] Writing to PostgreSQL...")
    engine = create_engine(POSTGRES_URI)

    # Create table if not exists
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS eco_cup_store (
        ogc_fid SERIAL PRIMARY KEY,
        data_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        brand VARCHAR(100),
        store_name VARCHAR(200),
        address TEXT,
        city VARCHAR(20),
        district VARCHAR(20),
        phone VARCHAR(50),
        lon DOUBLE PRECISION,
        lat DOUBLE PRECISION,
        wkb_geometry GEOMETRY(Point, 4326),
        _ctime TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        _mtime TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """
    with engine.begin() as conn: # Using .begin() automatically handles the commit
        conn.execute(text(create_table_sql))
        conn.execute(text("TRUNCATE TABLE eco_cup_store;"))

    # Insert data using pandas to_sql (Pass the URI string directly!)
    ready_data.to_sql(
        "eco_cup_store",
        con=POSTGRES_URI,  # <-- Magic happens here: Pass the raw string, not the engine
        if_exists="append",
        index=False,
        method="multi",
        chunksize=500,
    )

    # 5. Create geometry from lon/lat
    print("\n[5/5] Creating PostGIS geometry...")
    with engine.connect() as conn:
        conn.execute(text("""
            UPDATE eco_cup_store
            SET wkb_geometry = ST_SetSRID(ST_MakePoint(lon, lat), 4326)
            WHERE wkb_geometry IS NULL;
        """))
        conn.commit()

    print(f"\nDone! Inserted {after_drop} records into eco_cup_store.")
    return 0


if __name__ == "__main__":
    exit(main())
