from airflow import DAG
from operators.common_pipeline import CommonDag

def _transfer(**kwargs):
	'''
	資料格式如下：
	{
		"district": "士林區",
		"village": "天壽里",
		"squad": "天母分隊",
		"bureau_id": "103-074",
		"plate_number": "821-BT",
		"route": "天母-1",
		"sequence": "第1車",
		"arrival_time": "1630",
		"departure_time": "1640",
		"location": "臺北市士林區天母西路48號",
		"longitude": "121.525",
		"latitude": "25.11836"
	}
	'''
	# 匯入處理函式與套件
	import pandas as pd
	import requests
	from sqlalchemy import create_engine

	from utils.load_stage import (
		save_dataframe_to_postgresql,
		update_lasttime_in_data_to_dataset_info,
	)
	from utils.transform_time import convert_str_to_time_format
	from utils.transform_geometry import add_point_wkbgeometry_column_to_df

	ready_data_db_uri = kwargs.get("ready_data_db_uri")
	proxies = kwargs.get('proxies')  # 如果有使用 proxy
	dag_infos = kwargs.get('dag_infos')
	dag_id = dag_infos.get("dag_id")
	load_behavior = dag_infos.get("load_behavior")
	default_table = dag_infos.get("ready_data_default_table")
	history_table = dag_infos.get("ready_data_history_table")
	FROM_CRS = 4326

	source_url = "https://data.taipei/api/v1/dataset/a6e90031-7ec4-4089-afb5-361a4efe7202?scope=resourceAquire"
	response = requests.get(source_url, timeout=60, proxies=proxies)
	response.raise_for_status()
	payload = response.json()
	records = payload.get("result", payload)
	if isinstance(records, dict):
		records = records.get("results", records.get("data", []))
	raw_data = pd.DataFrame(records)
	if raw_data.empty:
		raise ValueError("Source API returned no records.")
	
	data = raw_data.copy()
	
	lasttime_in_data = None
	if "arrival_time" in data.columns and data["_importdate"]["date"].notna().any():
		lasttime_in_data = data["_importdate"]["date"].max()
	print(f"lasttime_in_data: {lasttime_in_data}")

	rename_map = {
		"行政區":"district",
		"里別":"village",
		"分隊":"squad",
		"局編":"bureau_id",
		"車號":"plate_number",
		"路線":"route",
		"車次":"sequence",
		"抵達時間":"arrival_time",
		"離開時間":"departure_time",
		"地點":"location",
		"經度":"longitude",
		"緯度":"latitude"
	}
	data = data.rename(columns=rename_map)
	data = data.drop(["_id", "_importdate"], axis=1, errors='ignore')
	print(data.head())
	# geoData = add_point_wkbgeometry_column_to_df(
    #     data, x=data["longitude"], y=data["latitude"], from_crs=FROM_CRS
    # )
	engine = create_engine(ready_data_db_uri)
	save_dataframe_to_postgresql(
		engine,
		data=data,
		load_behavior=load_behavior,
		default_table=default_table,
		history_table=history_table,
	)
	

# 建立 DAG 實例，指定專案與 DAG 所屬資料夾
dag = CommonDag(
    proj_folder='proj_city_dashboard',
    dag_folder='garbage_truck_location'
)

# 將 _transfer 函式掛載至 DAG 中，作為 ETL 執行邏輯
dag.create_dag(etl_func=_transfer)

