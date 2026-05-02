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
    (客製化：篩選雙北測站，計算行政區平均降雨量)
    """
    
    # --- 執行環境與 DAG 目標表 ---
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    proxies = kwargs.get("proxies")
    dag_infos = kwargs.get("dag_infos")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")  # config 設定為 district_rainfall 
    history_table = dag_infos.get("ready_data_history_table")

    # --- Extract：抓取 CWA API ---
    raw_api_key = Variable.get("CWA_API_KEY", "rdec-key-123-45678-011121314")
    api_key = raw_api_key.strip()
    
    url = 'https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0002-001'
    
    # 修正：拉高 limit 確保拿到所有測站，移除 RainfallElement 避免過濾異常
    params = {       
        'offset': 0,
        'format': 'JSON'
    }

    print("Fetching data from CWA REST API...")
    
    headers = {
        'Authorization': api_key,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    response = requests.get(url, headers=headers, params=params, timeout=120)
    
    try:
        response.raise_for_status()
        data = response.json()
        print("🎉 成功拿到 JSON 資料了！")
    except Exception as e:
        print(f"❌ API 請求失敗！回傳內容: {response.text}")
        raise e

    # --- Transform：解析與清洗資料 ---
    stations = data.get('records', {}).get('Station', [])
    
    if not stations:
        raise ValueError("API 回傳成功，但在 records 裡找不到 'Station' 陣列！")

    records = []
    for s in stations:
        geo = s.get('GeoInfo', {})
        county = geo.get('CountyName')
        town = geo.get('TownName')
        
        # 只保留「雙北」的測站
        if county in ['臺北市', '台北市', '新北市']:
            rain_data = s.get('RainfallElement', {})

            def clean_rain_value(val):
                try:
                    v = float(val)
                    return 0.0 if v < 0 else v
                except (ValueError, TypeError):
                    return 0.0

            # 確保欄位名稱與你的 SQL Table 完全一致
            records.append({
                'county_name': str(county),
                'town_name': str(town),
                'avg_rainfall_1hr': clean_rain_value(rain_data.get('Past1hr', {}).get('Precipitation')),
                'avg_rainfall_24hr': clean_rain_value(rain_data.get('Past24hr', {}).get('Precipitation')),
                'avg_rainfall_3days': clean_rain_value(rain_data.get('Past3days', {}).get('Precipitation'))
            })
            
    raw_df = pd.DataFrame(records)
    if raw_df.empty:
        print("⚠️ 警告：本次 API 回傳中沒有雙北測站，提早結束任務。")
        return

    # 計算行政區平均降雨量 (GroupBy)
    ready_data = raw_df.groupby(['county_name', 'town_name'], as_index=False).mean()
    ready_data['avg_rainfall_1hr'] = ready_data['avg_rainfall_1hr'].round(2)
    ready_data['avg_rainfall_24hr'] = ready_data['avg_rainfall_24hr'].round(2)
    ready_data['avg_rainfall_3days'] = ready_data['avg_rainfall_3days'].round(2)

    print(f"🌍 縣市過濾與平均計算完成：產出 {len(ready_data)} 個行政區平均數據。")

    # --- Load：寫入 PostgreSQL ---
    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine,
        data=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
    )

    # --- 輸出 GeoJSON (目前依需求註解停用) ---
    # geo_data = ready_data.dropna(subset=["longitude", "latitude"])
    # if not geo_data.empty:
    #     geometry = [Point(xy) for xy in zip(geo_data["longitude"], geo_data["latitude"])]
    #     gdata = gpd.GeoDataFrame(geo_data, geometry=geometry, crs="EPSG:4326")
    #     output_path = "/opt/airflow/mapData/cwa_rainfall.geojson"
    #     os.makedirs(os.path.dirname(output_path), exist_ok=True)
    #     gdata.to_file(output_path, driver="GeoJSON", encoding="utf-8")
    #     print(f"GeoJSON file has been created: {output_path}")
    # else:
    #     print("No valid coordinates for GeoJSON output.")

# --- DAG 註冊 ---
dag = CommonDag(
    proj_folder="proj_new_taipei_city_dashboard",
    dag_folder="cwa_district_rainfall",  
)
dag.create_dag(etl_func=_transfer)