import os
import pandas as pd
import requests
from airflow.models import Variable
from sqlalchemy import create_engine
import geopandas as gpd
from shapely.geometry import Point

from airflow import DAG
from operators.common_pipeline import CommonDag
from utils.load_stage import save_dataframe_to_postgresql

def _transfer(**kwargs):
    """
    CWA 降雨量資料：Extract → Transform → Load
    (客製化：篩選雙北測站，清洗降雨量異常值，並輸出 GeoJSON 供地圖使用)
    """
    
    # --- 執行環境與 DAG 目標表（由 job_config / kwargs 注入）---
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    proxies = kwargs.get("proxies")
    dag_infos = kwargs.get("dag_infos")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")  # 在 config 設定為 district_rainfall 
    history_table = dag_infos.get("ready_data_history_table")

    # --- Extract：抓取 CWA API ---
    # 建議在 Airflow UI 的 Variables 中設定 CWA_API_KEY
	# --- 1. 確保 API Key 絕對沒有隱形空白或換行 ---
    raw_api_key = Variable.get("CWA_API_KEY", "rdec-key-123-45678-011121314")
    api_key = raw_api_key.strip()  # 🌟 關鍵殺手鐧
    
    url = f'https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/O-A0002-001?Authorization={api_key}&format=JSON'
    
    print("Fetching data from CWA API...")
    
    # --- 2. 升級全套瀏覽器偽裝 Headers ---
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive'
    }
    
    # 發送請求
    response = requests.get(url, headers=headers, proxies=proxies, timeout=120)
    
    try:
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"❌ API 請求失敗或無法解析 JSON！")
        print(f"HTTP 狀態碼: {response.status_code}")
        print(f"請求的 URL (請檢查是否有異常換行): {url}") # 印出 URL 幫你肉眼檢查
        print(f"API 原始回傳內容: {response.text}")
        raise e
    # -------------------------
    
    stations = data.get('cwaopendata', {}).get('dataset', {}).get('Station', [])
    if not stations:
        raise ValueError("No stations found in CWA API.")

    # --- Transform：解析與清洗資料 ---
    records = []
    for s in stations:
        geo = s.get('GeoInfo', {})
        county = geo.get('CountyName')
        town = geo.get('TownName')
        
        # 📍 過濾邏輯：只保留「雙北」的測站
        if county in ['臺北市', '台北市', '新北市']:
            rain_data = s.get('RainfallElement', {})
            coords = geo.get('Coordinates', [])
            
            # 取得 WGS84 經緯度供地圖使用
            lat, lon = None, None
            for c in coords:
                if c.get('CoordinateName') == 'WGS84':
                    lat = c.get('StationLatitude')
                    lon = c.get('StationLongitude')

            # 處理氣象局特殊數值 (例如: 'T' 軌跡降雨微量, '-99.0' 儀器故障)
            def clean_rain_value(val):
                try:
                    v = float(val)
                    return 0.0 if v < 0 else v
                except (ValueError, TypeError):
                    return 0.0

            records.append({
                'station_id': s.get('StationId'),
                'station_name': s.get('StationName'),
                'county': county,
                'town': town,
                'rain_1hr': clean_rain_value(rain_data.get('Past1hr', {}).get('Precipitation')),
                'rain_24hr': clean_rain_value(rain_data.get('Past24hr', {}).get('Precipitation')),
                'longitude': lon,
                'latitude': lat
            })
            
    ready_data = pd.DataFrame(records)
    print(f"🌍 縣市過濾：篩選出雙北共 {len(ready_data)} 個氣象站。")
    
    if ready_data.empty:
        print("⚠️ 警告：本次 API 回傳中沒有雙北測站，提早結束任務。")
        return

    # 轉型經緯度確保能存入 DB 與轉成 Point 幾何圖形
    ready_data['longitude'] = pd.to_numeric(ready_data['longitude'], errors="coerce")
    ready_data['latitude'] = pd.to_numeric(ready_data['latitude'], errors="coerce")

    # 去重防呆機制 (保護 Primary Key)
    ready_data = ready_data.drop_duplicates(subset=["station_id"], keep="last")

    # --- Load：寫入 PostgreSQL ---
    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine,
        data=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
    )

    # --- 輸出 GeoJSON 供儀表板地圖直接讀取 ---
    geo_data = ready_data.dropna(subset=["longitude", "latitude"])
    if not geo_data.empty:
        geometry = [Point(xy) for xy in zip(geo_data["longitude"], geo_data["latitude"])]
        gdata = gpd.GeoDataFrame(geo_data, geometry=geometry, crs="EPSG:4326")
        
        # 輸出路徑要跟前端呼叫的 API 對齊
        output_path = "/opt/airflow/mapData/cwa_rainfall.geojson"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        gdata.to_file(output_path, driver="GeoJSON", encoding="utf-8")
        print(f"GeoJSON file has been created: {output_path}")
    else:
        print("No valid coordinates for GeoJSON output.")

# --- DAG 註冊 ---
# 確保 dag_folder 名稱與你們團隊的架構規則相符
dag = CommonDag(
    proj_folder="proj_new_taipei_city_dashboard",
    dag_folder="cwa_district_rainfall",  
)
dag.create_dag(etl_func=_transfer)