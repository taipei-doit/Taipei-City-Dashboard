from shapely.geometry import Point
from airflow import DAG
from operators.common_pipeline import CommonDag
from utils.extract_stage import get_data_taipei_api
from utils.load_stage import save_geodataframe_to_postgresql, update_lasttime_in_data_to_dataset_info
from utils.get_time import get_tpe_now_time_str
from utils.transform_geometry import add_point_wkbgeometry_column_to_df
from sqlalchemy import create_engine
import pandas as pd


def _transfer(**kwargs):
    # Config
    ready_data_db_uri = kwargs.get('ready_data_db_uri')
    proxies = kwargs.get('proxies')  # 若有用 proxy 可啟用
    dag_infos = kwargs.get('dag_infos')
    dag_id = dag_infos.get('dag_id')
    load_behavior = dag_infos.get('load_behavior')
    default_table = dag_infos.get('ready_data_default_table')
    history_table = dag_infos.get('ready_data_history_table')
    GEOMETRY_TYPE = "Point"
    FROM_CRS = 4326

    # Resource ID
    rid = '438c61ad-24f6-4e54-a1cc-e2cfe0e7051e'

    # Extract
    res = get_data_taipei_api(rid)
    raw_data = pd.DataFrame(res)
    raw_data["data_time"] = get_tpe_now_time_str()

    # Rename columns to match provided structure
    raw_data = raw_data.rename(columns={
        "_id": "place_id",
        "縣市別代碼": "city_code",
        "場所名稱": "place_name",
        "場所地址": "address",
        "行政區域代碼": "district_code",
        "緯度": "lat",
        "經度": "lng",
        "場所分類": "category",
        "場所類型": "type",
        "aed放置地點": "aed_location"
    })

    # Clean and select
    df = raw_data[[
        "place_id", "city_code", "place_name", "address", "district_code",
        "lat", "lng", "category", "type", "aed_location", "data_time"
    ]].copy()

    # 補上 city / district 欄位（若未來需要地圖篩選用）
    df["city"] = df["city_code"].astype(str).str[:2] + "000"
    df["district"] = df["district_code"].astype(str)

    # 經緯度轉為 WKB 幾何
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lng"] = pd.to_numeric(df["lng"], errors="coerce")
    gdf = add_point_wkbgeometry_column_to_df(df, df["lng"], df["lat"], from_crs=FROM_CRS)

    # 最終欄位
    final_df = gdf[[
        "place_id", "place_name", "address", "city", "district",
        "category", "type", "aed_location",
        "lat", "lng", "wkb_geometry", "data_time"
    ]]

    # Load to PostgreSQL
    engine = create_engine(ready_data_db_uri)
    save_geodataframe_to_postgresql(
        engine,
        gdata=final_df,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        geometry_type=GEOMETRY_TYPE,
    )

    # Update dataset info
    lasttime_in_data = final_df["data_time"].max()
    update_lasttime_in_data_to_dataset_info(engine, airflow_dag_id=dag_id, lasttime_in_data=lasttime_in_data)


# Create DAG
dag = CommonDag(proj_folder='proj_city_dashboard', dag_folder='aed_locations')
dag.create_dag(etl_func=_transfer)
